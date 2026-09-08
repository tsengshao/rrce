"""Crash-aware Slurm submission."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .contracts import inspect_products, validation_for
from .render import verify_run


JOB_ID_RE = re.compile(r"^(\d+)(?:;([^;\s]+))?$")


class SubmitError(RuntimeError):
    pass


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def parse_job_id(output: str) -> str:
    match = JOB_ID_RE.fullmatch(output.strip())
    if not match:
        raise SubmitError(f"malformed sbatch --parsable output: {output!r}")
    return match.group(1)


def submission_preview(plan: dict[str, Any], existing: dict[str, Any] | None = None) -> list[list[str]]:
    jobs = (existing or {}).get("jobs", {})
    result: list[list[str]] = []
    actions = {item["id"]: item["action"] for item in plan["stages"]}
    for stage in plan["stages"]:
        if stage["action"] != "run" or stage["id"] in jobs:
            continue
        parents = []
        for parent in stage["parents"]:
            if actions[parent] == "reuse":
                continue
            if actions[parent] == "blocked":
                raise SubmitError(f"{stage['id']}: runnable stage depends on blocked parent {parent}")
            parents.append(jobs.get(parent, {}).get("job_id", f"<JOB_ID:{parent}>"))
        argv = ["sbatch", "--parsable"]
        if parents:
            argv.append("--dependency=afterok:" + ":".join(parents))
        argv.append(str(Path(plan["run_dir"]) / "jobs" / f"{stage['id']}.sbatch"))
        result.append(argv)
    return result


def submit(run_dir: Path, allow_overwrite: bool | None = None, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> dict[str, Any]:
    plan = verify_run(run_dir)
    if allow_overwrite is None:
        allow_overwrite = bool(plan.get("allow_overwrite", False))
    if plan["unresolved"]:
        raise SubmitError("unresolved plan items: " + "; ".join(plan["unresolved"]))
    state_path = run_dir / "state" / "jobs.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"jobs": {}, "intents": {}, "failures": {}}

    invalid_reusable = []
    collisions = []
    case_total_t = {case["index"]: case.get("total_t") for case in plan.get("cases", [])}
    for stage in plan["stages"]:
        if stage["id"] in state["jobs"] or stage["action"] == "blocked":
            continue
        skipped_cases = set(stage.get("skipped_cases", []))
        validation = stage.get("validation", validation_for(stage["id"]))
        reusable = []
        for item in stage["outputs"]:
            is_reusable = stage["action"] == "reuse" or item.get("case_index") in skipped_cases
            if is_reusable:
                reusable.append(item)
            elif stage["action"] == "run" and Path(item["path"]).exists():
                collisions.append(item["path"])
        reusable_state = inspect_products(reusable, validation, case_total_t)
        invalid_reusable.extend(
            {"path": path, "reason": "missing"} for path in reusable_state["missing"]
        )
        invalid_reusable.extend(reusable_state["invalid"])
    if invalid_reusable:
        first = invalid_reusable[0]
        raise SubmitError(
            f"{len(invalid_reusable)} planned reusable outputs became invalid; "
            f"render a new run; first: {first['path']}: {first['reason']}"
        )
    if collisions and not allow_overwrite:
        raise SubmitError(f"{len(collisions)} output collisions; review and pass --allow-overwrite")
    if allow_overwrite:
        rendered = {path for stage in plan["stages"] for path in stage["collisions"]}
        new_collisions = sorted(set(collisions) - rendered)
        if new_collisions:
            raise SubmitError("outputs appeared after render and are not authorized: " + ", ".join(new_collisions[:10]))
        _atomic_json(run_dir / "state" / "overwrite.json", sorted(collisions))

    state.setdefault("failures", {})
    while True:
        pending = submission_preview(plan, state)
        if not pending:
            break
        argv = pending[0]
        stage_id = Path(argv[-1]).stem
        if stage_id in state["intents"] and stage_id not in state["jobs"]:
            raise SubmitError(f"{stage_id}: unknown_submission; reconcile with squeue/sacct before retry")
        state["intents"][stage_id] = {"time": datetime.now(timezone.utc).isoformat(), "argv": argv}
        _atomic_json(state_path, state)
        completed = runner(argv, check=False, text=True, capture_output=True)
        if completed.returncode:
            state["failures"][stage_id] = {"time": datetime.now(timezone.utc).isoformat(), "stderr": completed.stderr.strip()}
            state["intents"].pop(stage_id, None)
            _atomic_json(state_path, state)
            raise SubmitError(f"sbatch failed for {stage_id}: {completed.stderr.strip()}")
        job_id = parse_job_id(completed.stdout)
        state["jobs"][stage_id] = {"job_id": job_id, "submitted_at": datetime.now(timezone.utc).isoformat()}
        _atomic_json(state_path, state)
    return state
