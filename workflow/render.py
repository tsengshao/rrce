"""Render an immutable, human-reviewable run directory."""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import shlex
import shutil
from pathlib import Path
from typing import Any

from .config_loader import ConfigSnapshot, sha256_file
from .planner import plan_text
from .stages import STAGE_BY_ID


SOURCE_DIRS = (
    "workflow", "cwv", "convolve", "horisf", "find_center", "cloud", "axisy",
    "axisy_lowlevel_new", "ani_water_wind", "ani_center", "util",
)
SOURCE_SUFFIXES = {".py", ".gs", ".sh", ".ctl"}


class RenderError(RuntimeError):
    pass


def _safe_run_id(value: str | None) -> str:
    if not value or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value) or value in {".", ".."}:
        raise RenderError("run_id: required and must be one safe path component")
    return value


def _copy_sources(repo: Path, target: Path) -> None:
    for dirname in SOURCE_DIRS:
        source_dir = repo / dirname
        if not source_dir.is_dir():
            continue
        for source in source_dir.rglob("*"):
            if source.is_file() and source.suffix in SOURCE_SUFFIXES and "runs" not in source.parts:
                relative = source.relative_to(repo)
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)


def _quote_grads(value: str) -> str:
    if "'" in value or "\n" in value:
        raise RenderError(f"value cannot be represented safely in GrADS: {value!r}")
    return value


def render_grads_case(source: str, case: dict[str, Any], plan: dict[str, Any], output_root: Path) -> tuple[str, str]:
    """Replace the single config block, failing if its structural anchors drift."""
    start = source.find("vvmPath=")
    markers = ("say explabel", "say exp', '")
    end = next((position for marker in markers if (position := source.find(marker, start)) >= 0), -1)
    if start < 0 or end < 0:
        raise RenderError("GrADS adapter anchors not found")
    exp = _quote_grads(str(case["experiment"]))
    label = _quote_grads(str(case["label"]))
    block = (
        f"vvmPath='{_quote_grads(plan['vvm_path'])}/'\n"
        f"datPath='{_quote_grads(plan['data_path'])}/'\n\n"
        f"dt = {case['dt_minutes']}\n"
        f"exp = '{exp}'\n"
        f"explabel = '{label}'\n"
        f"tlast = {case['total_t']}\n"
    )
    tail = source[end:]
    tail, replacements = re.subn(
        r"(?m)^outPath=.*$", f"outPath='{_quote_grads(str(output_root))}'", tail, count=1
    )
    if replacements != 1:
        raise RenderError("GrADS output-path anchor not found")
    rendered = source[:start] + block + tail
    diff = "".join(difflib.unified_diff(source.splitlines(True), rendered.splitlines(True), fromfile="source", tofile="rendered"))
    return rendered, diff


def _hash_tree(root: Path, excluded: set[str] | None = None) -> dict[str, str]:
    excluded = excluded or set()
    result: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file() or item.is_symlink()):
        relative = str(path.relative_to(root))
        if "__pycache__" in path.relative_to(root).parts:
            continue
        if relative not in excluded and not relative.startswith(("logs/", "state/")):
            if path.is_symlink():
                result[relative] = "symlink:" + hashlib.sha256(os.readlink(path).encode()).hexdigest()
            else:
                result[relative] = sha256_file(path)
    return result


def _review_markdown(plan: dict[str, Any]) -> str:
    lines = [f"# Workflow review: {plan['run_id']}", "", f"Dataset: `{plan['dataset_tag']}`", "", "| stage | action | skipped cases | parents | tasks | collisions | missing | invalid | blocked by |", "|---|---|---|---|---:|---:|---:|---:|---|"]
    for stage in plan["stages"]:
        requested = stage.get("requested_action", stage["action"])
        action = stage["action"] if requested == stage["action"] else f"{requested} -> {stage['action']}"
        skipped = ", ".join(str(index) for index in stage.get("skipped_cases", [])) or "-"
        missing = len(stage.get("missing_products", []))
        invalid = len(stage.get("invalid_products", []))
        blocked = ", ".join(stage.get("blocked_by", [])) or "-"
        lines.append(f"| {stage['id']} | {action} | {skipped} | {', '.join(stage['parents']) or '-'} | {stage['resources']['tasks']} | {len(stage['collisions'])} | {missing} | {invalid} | {blocked} |")
    lines += ["", "## Cases", ""]
    for case in plan["cases"]:
        lines.append(f"- `{case['index']}` `{case['experiment']}` ({case['label']}), T={case['total_t']}, dt={case['dt_minutes']} min, day={case['case_day']}")
    lines += ["", "## Unresolved", ""]
    lines += [f"- {item}" for item in plan["unresolved"]] or ["- none"]
    lines += ["", "Generated jobs and source changes are under `jobs/` and `patches/`.", ""]
    return "\n".join(lines)


def render(plan: dict[str, Any], cfg: ConfigSnapshot, runs_root: Path | None = None) -> Path:
    run_id = _safe_run_id(plan.get("run_id"))
    repo = Path(plan["repo_root"])
    root = (runs_root or repo / "workflow" / "runs") / run_id
    try:
        root.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise RenderError(f"run directory already exists: {root}") from exc
    for dirname in ("jobs", "logs", "state", "artifacts", "patches", "sources"):
        (root / dirname).mkdir()
    try:
        _copy_sources(repo, root / "sources")
        shutil.copy2(cfg.path, root / "config.snapshot.py")
        plan["run_dir"] = str(root.resolve())
        plan["config_snapshot"] = str((root / "config.snapshot.py").resolve())
        template = (repo / "workflow" / "templates" / "stage.sbatch").read_text()
        for stage_data in plan["stages"]:
            stage = STAGE_BY_ID[stage_data["id"]]
            if stage_data["action"] != "run":
                continue
            job = template.format(
                job_name=f"rrce_{run_id}_{stage.id}",
                partition=stage_data["resources"]["partition"],
                tasks=stage_data["resources"]["tasks"],
                log_path=shlex.quote(str((root / "logs" / f"{stage.id}.%j.out").resolve())),
                sources_root=shlex.quote(str((root / "sources").resolve())),
                run_dir=shlex.quote(str(root.resolve())),
                stage_id=stage.id,
            )
            path = root / "jobs" / f"{stage.id}.sbatch"
            path.write_text(job)
            path.chmod(0o755)

            if stage.kind == "grads":
                original_path = repo / stage.commands[0]
                original = original_path.read_text()
                for case in plan["cases"]:
                    output = root / "rendered" / "grads" / stage.id / str(case["index"]) / original_path.name
                    output.parent.mkdir(parents=True, exist_ok=True)
                    figure_root = Path(plan["data_path"]) / "workflow_figures" / plan["dataset_tag"] / stage.id / case["experiment"]
                    text, diff = render_grads_case(original, case, plan, figure_root)
                    output.write_text(text)
                    (root / "patches" / f"{stage.id}-{case['index']}.diff").write_text(diff)

        (root / "plan.json").write_text(plan_text(plan))
        (root / "review.md").write_text(_review_markdown(plan))
        artifacts = []
        for stage in plan["stages"]:
            for item in stage["outputs"]:
                artifacts.append({"stage": stage["id"], **item})
            grouped: dict[tuple[str, object], str] = {}
            for item in stage["outputs"]:
                key = (item["role"], item["case_index"])
                grouped.setdefault(key, item["path"])
            for (role, case_index), target in grouped.items():
                link_dir = root / "artifacts" / role / stage["id"]
                link_dir.mkdir(parents=True, exist_ok=True)
                link = link_dir / ("aggregate" if case_index is None else str(case_index))
                target_path = Path(target)
                link.symlink_to(target_path if role == "ctl" else target_path.parent)
        (root / "artifacts.json").write_text(json.dumps(artifacts, indent=2) + "\n")
        hashes = _hash_tree(root, {"manifest.lock.json"})
        lock = {"schema_version": 1, "files": hashes}
        (root / "manifest.lock.json").write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
    except Exception:
        shutil.rmtree(root)
        raise
    return root


def verify_run(root: Path) -> dict[str, Any]:
    lock_path = root / "manifest.lock.json"
    try:
        lock = json.loads(lock_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RenderError(f"invalid lock manifest: {exc}") from exc
    actual = _hash_tree(root, {"manifest.lock.json", "state/jobs.json", "state/events.jsonl"})
    expected = lock.get("files", {})
    changed = sorted(key for key in set(actual) | set(expected) if actual.get(key) != expected.get(key))
    if changed:
        raise RenderError("rendered run has changed; render a new run: " + ", ".join(changed))
    return json.loads((root / "plan.json").read_text())
