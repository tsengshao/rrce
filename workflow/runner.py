"""Runtime entrypoint used by every rendered Slurm job."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from .contracts import inspect_products, validation_for
from .stages import STAGE_BY_ID


class StageFailure(RuntimeError):
    pass


def _run(argv: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(argv), flush=True)
    completed = subprocess.run(argv, cwd=cwd, env=env, check=False)
    if completed.returncode:
        raise StageFailure(f"command exited {completed.returncode}: {argv}")


def _run_parallel(commands: list[list[str]], cwd: Path) -> None:
    processes = []
    for argv in commands:
        print("+", " ".join(argv), flush=True)
        processes.append((argv, subprocess.Popen(argv, cwd=cwd)))
    failures = [(argv, process.wait()) for argv, process in processes]
    failures = [(argv, code) for argv, code in failures if code]
    if failures:
        argv, code = failures[0]
        raise StageFailure(f"{len(failures)} parallel commands failed; first exited {code}: {argv}")


def _locks(paths: list[str], stage_id: str) -> ExitStack:
    stack = ExitStack()
    lock_root = Path("/tmp/rrce-workflow-locks")
    lock_root.mkdir(mode=0o700, exist_ok=True)
    keys = sorted({hashlib.sha256(f"{stage_id}\0{path}".encode()).hexdigest() for path in paths})
    for key in keys:
        stream = stack.enter_context((lock_root / key).open("a+"))
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            stack.close()
            raise StageFailure(f"another workflow owns output lock {key}") from exc
    return stack


def _python_command(run_dir: Path, relative_and_args: str, ranks: int | None) -> list[str]:
    parts = relative_and_args.split()
    adapter = [
        sys.executable, "-m", "workflow.run_with_config",
        "--config", str(run_dir / "config.snapshot.py"),
        "--script", str(run_dir / "sources" / parts[0]), "--", *parts[1:],
    ]
    return ["mpirun", "-np", str(ranks), *adapter] if ranks else adapter


def _ctl_command(kind: str, case: dict[str, Any], plan: dict[str, Any], allow: bool) -> list[str]:
    data = Path(plan["data_path"])
    exp = case["experiment"]
    outputs = {
        "wp": data / "wp" / f"{exp}.ctl",
        "sf": data / "horimsf" / f"msf_{exp}.ctl",
        "convolve": data / "convolve" / exp / "convolve.ctl",
    }
    argv = [sys.executable, "-m", "workflow.ctl", "--kind", kind, "--experiment", exp,
            "--total-t", str(case["total_t"]), "--dt", str(case["dt_minutes"]),
            "--output", str(outputs[kind])]
    if allow:
        argv.append("--allow-overwrite")
    return argv


def run_stage(run_dir: Path, stage_id: str) -> None:
    plan = json.loads((run_dir / "plan.json").read_text())
    stage_data = next((item for item in plan["stages"] if item["id"] == stage_id), None)
    if stage_data is None or stage_id not in STAGE_BY_ID:
        raise StageFailure(f"unknown stage: {stage_id}")
    if stage_data["action"] != "run":
        raise StageFailure(f"stage is not planned to run: {stage_id}")
    skipped_cases = set(stage_data.get("skipped_cases", []))
    outputs = [item["path"] for item in stage_data["outputs"]]
    active_outputs = [
        item["path"] for item in stage_data["outputs"]
        if item.get("case_index") not in skipped_cases
    ]
    overwrite_path = run_dir / "state" / "overwrite.json"
    allowed = set(json.loads(overwrite_path.read_text())) if overwrite_path.exists() else set()
    unexpected = [path for path in active_outputs if Path(path).exists() and path not in allowed]
    if unexpected:
        raise StageFailure("unapproved existing outputs: " + ", ".join(unexpected[:10]))

    stage = STAGE_BY_ID[stage_id]
    with _locks(outputs or [f"aggregate:{plan['dataset_tag']}"], stage_id):
        if stage.kind in {"python", "python_multi"}:
            for command_spec in stage.commands:
                spec, separator, rank_text = command_spec.partition("|")
                ranks = int(rank_text) if separator else stage_data["resources"]["ranks"]
                for case in plan["cases"]:
                    if case["index"] in skipped_cases:
                        print(f"skip {stage_id} case {case['index']}: expected filenames are complete", flush=True)
                        continue
                    environment = os.environ.copy()
                    if stage_id in {"hov_radial", "hov_tangential", "tang_daily", "radi_daily", "mse_ccc_daily"}:
                        output = Path(plan["data_path"]) / "workflow_figures" / plan["dataset_tag"] / stage_id / case["experiment"]
                        environment["RRCE_OUTPUT_DIR"] = str(output)
                    _run(_python_command(run_dir, spec.format(case=case["index"]), ranks), env=environment)
        elif stage.kind == "ctl":
            for case in plan["cases"]:
                if case["index"] in skipped_cases:
                    print(f"skip {stage_id} case {case['index']}: expected filenames are complete", flush=True)
                    continue
                _run(_ctl_command(stage.commands[0], case, plan, bool(allowed)))
        elif stage.kind == "grads":
            executable = os.environ.get("RRCE_OPENGRADS", "/work1/umbrella0c/opengrads-hpc-1.0.8-linux-x86_64/opengrads")
            commands = []
            for case in plan["cases"]:
                if case["index"] in skipped_cases:
                    print(f"skip {stage_id} case {case['index']}: expected filenames are complete", flush=True)
                    continue
                source = Path(stage.commands[0])
                script = run_dir / "rendered" / "grads" / stage_id / str(case["index"]) / source.name
                expression = f"run {script} 1 -ts 1 -te {case['total_t']} -mode SAVEFIG"
                commands.append([executable, "-blc", expression])
            width = stage_data["resources"]["tasks"]
            for start in range(0, len(commands), width):
                _run_parallel(commands[start:start + width], run_dir / "sources" / source.parent)
        elif stage.kind == "lowlevel":
            _run([sys.executable, "-m", "workflow.adapters.lowlevel", "--run-dir", str(run_dir), "--operation", stage.commands[0]])
        else:
            raise StageFailure(f"unsupported stage kind: {stage.kind}")

        validation = stage_data.get("validation", validation_for(stage_id))
        case_total_t = {case["index"]: case.get("total_t") for case in plan["cases"]}
        product_state = inspect_products(stage_data["outputs"], validation, case_total_t)
        failures = [
            *({"path": path, "reason": "missing"} for path in product_state["missing"]),
            *product_state["invalid"],
        ]
        if failures:
            first = failures[0]
            raise StageFailure(
                f"post-validation found {len(failures)} incomplete outputs; "
                f"first: {first['path']}: {first['reason']}"
            )
        receipt = run_dir / "state" / f"receipt-{stage_id}.json"
        receipt.write_text(json.dumps({
            "stage": stage_id, "expected_outputs": len(outputs), "validation": validation,
        }, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--stage", required=True)
    args = parser.parse_args()
    run_stage(args.run_dir.resolve(), args.stage)


if __name__ == "__main__":
    main()
