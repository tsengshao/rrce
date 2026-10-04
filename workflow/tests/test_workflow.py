from __future__ import annotations

import json
import os
import tempfile
import unittest
import subprocess
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from netCDF4 import Dataset
from workflow.contracts import Product, inspect_products, product_error, validation_for

from workflow.config_loader import ConfigError, load_config, parse_restart_day, resolve_dataset_tag
from workflow.ctl import render_ctl
from workflow.planner import build_plan, direct_request, request_from_manifest
from workflow.render import RenderError, render, render_grads_case, verify_run
from workflow.runner import run_stage
from workflow.stages import STAGES, topological_order
from workflow.status import collect_status, format_status
from workflow.submit import SubmitError, parse_job_id, submission_preview, submit


CONFIG = """
vvmPath = {vvm!r}
dataPath = {data!r}
expList = ['cluster_f10_d20_HomogRad', 'cluster_f10_d14p986_HomogRad']
totalT = [217, 217]
expdict = {{expList[0]: 'D20', expList[1]: 'D14.986'}}


def getExpDeltaT(exp):
    return 20
"""

def write_netcdf(path: Path, variables: tuple[str, ...] = ("cwv", "lwp", "iwp")) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with Dataset(path, "w") as dataset:
        dataset.createDimension("time", 1)
        for name in variables:
            dataset.createVariable(name, "f4", ("time",))[:] = [1.0]




class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.path = root / "config_group_name.py"
        self.path.write_text(CONFIG.format(vvm=str(root / "vvm"), data=str(root / "data")))

    def tearDown(self):
        self.temp.cleanup()

    def test_non_contiguous_cases_keep_original_indexes(self):
        cfg = load_config(self.path, [1, 0])
        self.assertEqual([case.index for case in cfg.cases], [1, 0])
        self.assertEqual(cfg.dataset_tag, "group_name")
        self.assertEqual([case.case_day for case in cfg.cases], [14.986, 20.0])
        self.assertFalse((self.path.parent / "__pycache__").exists())

    def test_config_py_requires_explicit_tag(self):
        renamed = self.path.with_name("config.py")
        renamed.write_text(self.path.read_text())
        with self.assertRaisesRegex(ConfigError, "dataset_tag"):
            load_config(renamed, [0])

    def test_duplicate_and_bad_index_fail_with_field(self):
        with self.assertRaisesRegex(ConfigError, "duplicate"):
            load_config(self.path, [0, 0])
        with self.assertRaisesRegex(ConfigError, "outside"):
            load_config(self.path, [9])

    def test_restart_day_is_unique(self):
        self.assertEqual(parse_restart_day("cluster_f10_d20_HomogRad"), 20.0)
        self.assertIsNone(parse_restart_day("cluster_f10_HomogRad"))
        self.assertIsNone(parse_restart_day("cluster_d10_f10_d20"))


class DagAndCtlTests(unittest.TestCase):
    def test_dag_is_topological_and_complete(self):
        ordered = topological_order()
        positions = {stage.id: index for index, stage in enumerate(ordered)}
        self.assertEqual(len(ordered), len(STAGES))
        self.assertIn("axisy_mean", positions)
        self.assertIn("axisy_process", positions)
        self.assertIn("axisy_daily", positions)
        self.assertNotIn("axisy_postprocess", positions)
        for stage in ordered:
            self.assertTrue(all(positions[parent] < positions[stage.id] for parent in stage.parents))

    def test_split_axisy_stages_use_qos_compatible_partitions(self):
        stages = {stage.id: stage for stage in STAGES}
        self.assertEqual(stages["axisy_convert"].resources.tasks, 224)
        self.assertEqual(stages["axisy_convert"].resources.ranks, 217)
        self.assertTrue(stages["axisy_convert"].parallel_cases)
        self.assertEqual(stages["axisy_mean"].resources.partition, "ct112,cf112")
        self.assertEqual(stages["axisy_daily"].resources.partition, "ct112,cf112")
        self.assertEqual(stages["axisy_process"].resources.partition, "ct448,cf448")
        self.assertEqual(stages["cloud"].resources.partition, "ct448")
        self.assertEqual(stages["cloud"].resources.tasks, 448)
        self.assertEqual(stages["cloud"].resources.ranks, 29)

    def test_legacy_axisy_postprocess_action_expands(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config_tiny.py"
            config.write_text("# parser only\n")
            manifest = root / "run.toml"
            stage_tables = []
            for stage in STAGES:
                if stage.id not in {"axisy_mean", "axisy_process", "axisy_daily"}:
                    stage_tables.append(f'[stages.{stage.id}]\naction = "run"')
            stage_tables.append('[stages.axisy_postprocess]\naction = "auto"')
            manifest.write_text(
                '[run]\nconfig = "config_tiny.py"\ncases = [0]\n\n' +
                "\n\n".join(stage_tables) + "\n"
            )
            request = request_from_manifest(manifest)
            self.assertEqual(request.actions["axisy_mean"], "auto")
            self.assertEqual(request.actions["axisy_process"], "auto")
            self.assertEqual(request.actions["axisy_daily"], "auto")

    def test_ctl_contract(self):
        wp = render_ctl("wp", "case", 217, 20)
        self.assertIn("TDEF 217", wp)
        self.assertIn("cwv=>cwv", wp)
        convolve = render_ctl("convolve", "case", 217, 20)
        self.assertIn("EDEF 1 NAMES 150km", convolve)
        sf = render_ctl("sf", "case", 217, 20)
        self.assertIn("sf=>msf 38", sf)


class RenderAndSubmitTests(unittest.TestCase):
    def test_auto_action_skips_complete_case_and_reports_partial_case(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = root / "data"
            config = root / "config_tiny.py"
            config.write_text(
                "vvmPath='/vvm'\ndataPath=" + repr(str(data)) + "\n"
                "expList=['cluster_f10_d20_HomogRad', 'cluster_f10_d21_HomogRad']\n"
                "totalT=[2, 2]\n"
                "expdict={expList[0]:'D20', expList[1]:'D21'}\n"
                "def getExpDeltaT(exp): return 20\n"
            )
            request = direct_request(str(config), [0, 1], "tiny", "auto-1")
            actions = dict(request.actions)
            actions["cwv"] = "auto"
            request = replace(request, actions=actions)

            first_root = data / "wp" / "cluster_f10_d20_HomogRad"
            first_root.mkdir(parents=True)
            write_netcdf(first_root / "wp-000000.nc")
            write_netcdf(first_root / "wp-000001.nc")
            second_root = data / "wp" / "cluster_f10_d21_HomogRad"
            second_root.mkdir(parents=True)
            partial_file = second_root / "wp-000000.nc"
            write_netcdf(partial_file)

            partial, _ = build_plan(request)
            cwv = next(stage for stage in partial["stages"] if stage["id"] == "cwv")
            self.assertEqual(cwv["requested_action"], "auto")
            self.assertEqual(cwv["action"], "run")
            self.assertEqual(cwv["skipped_cases"], [0])
            self.assertEqual(cwv["collisions"], [str(partial_file)])

            write_netcdf(second_root / "wp-000001.nc")
            complete, _ = build_plan(request)
            cwv = next(stage for stage in complete["stages"] if stage["id"] == "cwv")
            self.assertEqual(cwv["action"], "reuse")
            self.assertEqual(cwv["skipped_cases"], [0, 1])
            self.assertEqual(cwv["collisions"], [])

    def test_axisy_netcdf_requires_wind_variables(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "axisy-000000.nc"
            write_netcdf(path, ("cwv", "rain"))
            error = product_error(
                Product(path, "data", 0), validation_for("axisy_convert"), 1
            )
            self.assertIn("radi_wind", error)

    def test_lowlevel_profile_contract_uses_plotter_day_tokens(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config_tiny.py"
            config.write_text(
                "vvmPath='/vvm'\ndataPath=" + repr(str(root / "data")) + "\n"
                "expList=['cluster_f10_d20_HomogRad']\ntotalT=[1]\n"
                "expdict={expList[0]:'D20'}\ndef getExpDeltaT(exp): return 20\n"
            )
            request = direct_request(str(config), [0], "tiny", "lowlevel-day-token")
            plan, _ = build_plan(request)
            stage = next(
                stage for stage in plan["stages"] if stage["id"] == "lowlevel_profiles"
            )
            names = [Path(output["path"]).name for output in stage["outputs"]]
            self.assertEqual(names, [
                "cluster_f10_d20_HomogRad_day00_daily.png",
                "cluster_f10_d20_HomogRad_day03_daily.png",
            ])

    def test_series_validation_counts_all_files_and_opens_only_last(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "wp-000000.nc"
            last = root / "wp-000001.nc"
            first.write_bytes(b"not a NetCDF, deliberately unchecked")
            write_netcdf(last)
            products = [Product(first, "data", 0), Product(last, "data", 0)]

            state = inspect_products(products, validation_for("cwv"), {0: 2})
            self.assertEqual(state["valid"], [str(first), str(last)])
            self.assertEqual(state["invalid"], [])

            last.unlink()
            state = inspect_products(products, validation_for("cwv"), {0: 2})
            self.assertEqual(state["missing"], [str(last)])
            self.assertEqual(state["valid"], [])

            write_netcdf(last, ("cwv",))
            state = inspect_products(products, validation_for("cwv"), {0: 2})
            self.assertIn("lwp", state["invalid"][0]["reason"])

    def test_runnable_incomplete_parent_uses_dependency_instead_of_blocking(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = root / "data"
            config = root / "config_tiny.py"
            config.write_text(
                "vvmPath='/vvm'\ndataPath=" + repr(str(data)) + "\n"
                "expList=['cluster_f10_d20_HomogRad']\ntotalT=[1]\n"
                "expdict={expList[0]:'D20'}\ndef getExpDeltaT(exp): return 20\n"
            )
            request = direct_request(str(config), [0], "tiny", "blocked-1")
            actions = dict(request.actions)
            actions["cwv"] = "auto"
            request = replace(request, actions=actions)
            bad = data / "wp" / "cluster_f10_d20_HomogRad" / "wp-000000.nc"
            bad.parent.mkdir(parents=True)
            bad.touch()
            plan, _ = build_plan(request)
            cwv = next(stage for stage in plan["stages"] if stage["id"] == "cwv")
            self.assertEqual(cwv["invalid_products"][0]["reason"], "empty file")
            self.assertEqual(cwv["action"], "run")
            wp_ctl = next(stage for stage in plan["stages"] if stage["id"] == "wp_ctl")
            self.assertEqual(wp_ctl["action"], "run")
            self.assertEqual(wp_ctl["blocked_by"], [])

    def test_incomplete_reuse_parent_blocks_only_its_descendants(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config_tiny.py"
            config.write_text(
                "vvmPath='/vvm'\ndataPath=" + repr(str(root / "data")) + "\n"
                "expList=['cluster_f10_d20_HomogRad']\ntotalT=[1]\n"
                "expdict={expList[0]:'D20'}\ndef getExpDeltaT(exp): return 20\n"
            )
            request = direct_request(str(config), [0], "tiny", "reuse-blocked-1")
            actions = dict(request.actions)
            actions["cloud"] = "reuse"
            request = replace(request, actions=actions)
            plan, _ = build_plan(request)

            cloud = next(stage for stage in plan["stages"] if stage["id"] == "cloud")
            mse = next(stage for stage in plan["stages"] if stage["id"] == "mse_ccc_daily")
            axisy = next(stage for stage in plan["stages"] if stage["id"] == "axisy_convert")
            cloud_blocked = [
                stage["id"] for stage in plan["stages"]
                if "cloud" in stage.get("blocked_by", [])
            ]
            self.assertEqual(cloud["action"], "blocked")
            self.assertEqual(mse["action"], "blocked")
            self.assertEqual(cloud_blocked, ["cloud", "mse_ccc_daily"])
            self.assertEqual(axisy["action"], "run")

    def test_runner_does_not_execute_complete_case(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "state").mkdir()
            complete = run_dir / "complete.nc"
            produced = run_dir / "produced.nc"
            complete.write_bytes(b"complete")
            plan = {
                "dataset_tag": "tiny",
                "data_path": str(run_dir / "data"),
                "cases": [
                    {"index": 0, "experiment": "complete"},
                    {"index": 1, "experiment": "missing"},
                ],
                "stages": [{
                    "id": "cwv", "action": "run", "requested_action": "auto",
                    "skipped_cases": [0], "resources": {"ranks": 1},
                    "validation": {"kind": "nonempty"},
                    "outputs": [
                        {"path": str(complete), "case_index": 0},
                        {"path": str(produced), "case_index": 1},
                    ],
                }],
            }
            (run_dir / "plan.json").write_text(json.dumps(plan))
            calls = []

            def fake_run(argv, **kwargs):
                calls.append(argv)
                produced.write_bytes(b"produced")

            with patch("workflow.runner._run", side_effect=fake_run):
                run_stage(run_dir, "cwv")
            self.assertEqual(len(calls), 1)
            self.assertTrue((run_dir / "state" / "receipt-cwv.json").is_file())

    def test_axisy_convert_runs_two_cases_per_slurm_step_batch(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "state").mkdir()
            outputs = [run_dir / f"axisy-case-{index}.nc" for index in range(3)]
            plan = {
                "dataset_tag": "tiny",
                "data_path": str(run_dir / "data"),
                "cases": [
                    {"index": index, "experiment": f"case-{index}"}
                    for index in range(3)
                ],
                "stages": [{
                    "id": "axisy_convert", "action": "run", "requested_action": "run",
                    "skipped_cases": [], "resources": {"tasks": 434, "ranks": 217},
                    "validation": {"kind": "nonempty"},
                    "outputs": [
                        {"path": str(path), "case_index": index}
                        for index, path in enumerate(outputs)
                    ],
                }],
            }
            (run_dir / "plan.json").write_text(json.dumps(plan))
            batches = []

            def fake_parallel(commands, cwd=None):
                batches.append(commands)
                for command in commands:
                    outputs[int(command[-1])].write_bytes(b"produced")

            with patch("workflow.runner._run_parallel", side_effect=fake_parallel):
                run_stage(run_dir, "axisy_convert")

            self.assertEqual([len(batch) for batch in batches], [2, 1])
            for command in [item for batch in batches for item in batch]:
                self.assertEqual(command[0], "srun")
                self.assertIn("--exclusive", command)
                self.assertEqual(command[command.index("-n") + 1], "217")

    def test_full_render_is_locked_and_reviewable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config_tiny.py"
            config.write_text(
                "vvmPath='/vvm'\ndataPath=" + repr(str(root / "data")) + "\n"
                "expList=['cluster_f10_d20_HomogRad']\ntotalT=[1]\n"
                "expdict={expList[0]:'D20'}\ndef getExpDeltaT(exp): return 20\n"
            )
            request = direct_request(str(config), [0], None, "review-1")
            plan, cfg = build_plan(request)
            run_dir = render(plan, cfg, root / "runs with spaces")
            self.assertTrue((run_dir / "review.md").is_file())
            self.assertTrue((run_dir / "jobs" / "axisy_convert.sbatch").exists())
            axisy = next(stage for stage in plan["stages"] if stage["id"] == "axisy_convert")
            self.assertEqual(axisy["action"], "run")
            self.assertEqual(axisy["blocked_by"], [])
            self.assertEqual(verify_run(run_dir)["run_id"], "review-1")
            cache = run_dir / "sources" / "workflow" / "__pycache__"
            cache.mkdir()
            (cache / "generated.pyc").touch()
            self.assertEqual(verify_run(run_dir)["run_id"], "review-1")
            job = run_dir / "jobs" / "cwv.sbatch"
            job_text = job.read_text()
            self.assertNotIn("#SBATCH --nodes=1", job_text)
            self.assertLess(job_text.index("source ~/.bashrc"), job_text.index("set -u"))
            self.assertIn("export PYTHONDONTWRITEBYTECODE=1", job_text)
            job.write_text(job.read_text() + "# changed\n")
            with self.assertRaisesRegex(RenderError, "changed"):
                verify_run(run_dir)

    def test_grads_adapter_has_reviewable_diff(self):
        source = "head\nvvmPath=\"old\"\ndatPath=\"old\"\nexp='old'\nexplabel='old'\ntlast=1\nsay explabel\noutPath='./old'\ntail\n"
        case = {"experiment": "cluster_f10_d20_HomogRad", "label": "D20", "total_t": 217, "dt_minutes": 20}
        plan = {"vvm_path": "/vvm", "data_path": "/data"}
        rendered, diff = render_grads_case(source, case, plan, Path("/fig"))
        self.assertIn("exp = 'cluster_f10_d20_HomogRad'", rendered)
        self.assertIn("outPath='/fig'", rendered)
        self.assertIn("--- source", diff)

    def test_job_id_parser(self):
        self.assertEqual(parse_job_id("12345;cluster\n"), "12345")
        with self.assertRaises(SubmitError):
            parse_job_id("Submitted batch job 12345")

    def test_dependency_preview_uses_placeholders_then_ids(self):
        plan = {
            "run_dir": "/run",
            "stages": [
                {"id": "a", "action": "run", "parents": []},
                {"id": "b", "action": "reuse", "parents": []},
                {"id": "c", "action": "run", "parents": ["a", "b"]},
                {"id": "d", "action": "blocked", "parents": ["a"]},
            ],
        }
        preview = submission_preview(plan)
        self.assertIn("--dependency=afterok:<JOB_ID:a>", preview[1])
        self.assertFalse(any(command[-1].endswith("d.sbatch") for command in preview))
        state = {"jobs": {"a": {"job_id": "42"}}}
        preview = submission_preview(plan, state)
        self.assertIn("--dependency=afterok:42", preview[0])

    def test_submit_uses_real_parent_job_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "state").mkdir()
            (run_dir / "jobs").mkdir()
            plan = {
                "run_dir": str(run_dir), "unresolved": [],
                "stages": [
                    {"id": "a", "action": "run", "parents": [], "outputs": [], "collisions": []},
                    {"id": "c", "action": "run", "parents": ["a"], "outputs": [], "collisions": []},
                ],
            }
            calls = []

            def fake_runner(argv, **kwargs):
                calls.append(argv)
                return subprocess.CompletedProcess(argv, 0, stdout=f"{40 + len(calls)};cluster\n", stderr="")

            with patch("workflow.submit.verify_run", return_value=plan):
                state = submit(run_dir, runner=fake_runner)
            self.assertEqual(state["jobs"]["a"]["job_id"], "41")
            self.assertIn("--dependency=afterok:41", calls[1])

    def test_submit_excludes_auto_skipped_case_from_overwrite_collisions(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "state").mkdir()
            (run_dir / "jobs").mkdir()
            existing = run_dir / "complete.nc"
            existing.write_bytes(b"complete")
            plan = {
                "run_dir": str(run_dir), "unresolved": [],
                "stages": [{
                    "id": "a", "action": "run", "requested_action": "auto",
                    "skipped_cases": [0], "parents": [], "collisions": [],
                    "outputs": [{"path": str(existing), "case_index": 0}],
                }],
            }

            def fake_runner(argv, **kwargs):
                return subprocess.CompletedProcess(argv, 0, stdout="41;cluster\n", stderr="")

            with patch("workflow.submit.verify_run", return_value=plan):
                state = submit(run_dir, runner=fake_runner)
            self.assertEqual(state["jobs"]["a"]["job_id"], "41")

    def test_submit_uses_manifest_overwrite_setting_and_allows_cli_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "state").mkdir()
            (run_dir / "jobs").mkdir()
            collision = run_dir / "partial.nc"
            collision.touch()
            plan = {
                "run_dir": str(run_dir), "unresolved": [], "allow_overwrite": True,
                "stages": [{
                    "id": "a", "action": "run", "parents": [],
                    "collisions": [str(collision)],
                    "outputs": [{"path": str(collision), "case_index": 0}],
                }],
            }

            def fake_runner(argv, **kwargs):
                return subprocess.CompletedProcess(argv, 0, stdout="41;cluster\n", stderr="")

            with patch("workflow.submit.verify_run", return_value=plan):
                with self.assertRaisesRegex(SubmitError, "output collisions"):
                    submit(run_dir, allow_overwrite=False, runner=fake_runner)
                state = submit(run_dir, runner=fake_runner)
            self.assertEqual(state["jobs"]["a"]["job_id"], "41")
            self.assertEqual(json.loads((run_dir / "state" / "overwrite.json").read_text()), [str(collision)])


class StatusTests(unittest.TestCase):
    def test_rendered_run_is_reported_as_not_submitted(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "state").mkdir()
            plan = {
                "run_id": "rendered-1",
                "unresolved": [],
                "stages": [
                    {"id": "ready", "action": "run", "parents": []},
                    {"id": "old", "action": "reuse", "parents": []},
                    {
                        "id": "blocked", "action": "blocked", "parents": [],
                        "blocked_by": ["missing_input"], "missing_products": ["x"],
                    },
                ],
            }

            summary = collect_status(run_dir, plan)

            self.assertEqual(summary["overall"], "RENDERED_NOT_SUBMITTED")
            self.assertFalse(summary["finished"])
            self.assertEqual(summary["submission"]["unsubmitted_jobs"], ["ready"])
            self.assertIn("Submission: 0/1 jobs submitted", format_status(summary))

    def test_status_summarizes_failure_reason_and_failed_dependency(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "state").mkdir()
            (run_dir / "logs").mkdir()
            (run_dir / "state" / "jobs.json").write_text(json.dumps({
                "jobs": {
                    "prepare": {"job_id": "41"},
                    "calculate": {"job_id": "42"},
                    "plot": {"job_id": "43"},
                },
                "intents": {},
                "failures": {},
            }))
            (run_dir / "logs" / "calculate.42.out").write_text(
                "Traceback (most recent call last):\n"
                "ValueError: duplicate experiment coordinate\n"
                "StageFailure: command exited 1\n"
            )
            plan = {
                "run_id": "failed-1",
                "unresolved": [],
                "stages": [
                    {"id": "prepare", "action": "run", "parents": []},
                    {"id": "calculate", "action": "run", "parents": ["prepare"]},
                    {"id": "plot", "action": "run", "parents": ["calculate"]},
                ],
            }

            def fake_runner(argv, **kwargs):
                if argv[0] == "squeue":
                    return subprocess.CompletedProcess(
                        argv, 0, stdout="43|PENDING|DependencyNeverSatisfied\n", stderr=""
                    )
                return subprocess.CompletedProcess(
                    argv, 0,
                    stdout=(
                        "41|COMPLETED|0:0|00:00:05\n"
                        "42|FAILED|1:0|00:00:02\n"
                        "43|PENDING|0:0|00:00:00\n"
                    ),
                    stderr="",
                )

            summary = collect_status(run_dir, plan, runner=fake_runner)
            output = format_status(summary)

            self.assertEqual(summary["overall"], "FAILED")
            self.assertTrue(summary["finished"])
            self.assertEqual(summary["jobs"]["succeeded"], 1)
            self.assertEqual(summary["jobs"]["failed"], 1)
            self.assertEqual(summary["jobs"]["dependency_failed"], 1)
            self.assertIn("ValueError: duplicate experiment coordinate", output)
            self.assertIn("plot (43): DEPENDENCY_FAILED", output)


if __name__ == "__main__":
    unittest.main()
