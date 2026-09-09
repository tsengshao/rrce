"""Concise workflow and Slurm status reporting."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable


SUCCESS_STATES = {"COMPLETED"}
FAILURE_STATES = {
    "BOOT_FAIL", "CANCELLED", "DEADLINE", "FAILED", "NODE_FAIL",
    "OUT_OF_MEMORY", "PREEMPTED", "REVOKED", "SPECIAL_EXIT", "TIMEOUT",
}
RUNNING_STATES = {"COMPLETING", "RUNNING", "SIGNALING", "STAGE_OUT"}
PENDING_STATES = {
    "CONFIGURING", "PENDING", "REQUEUED", "REQUEUE_FED", "RESIZING", "SUSPENDED",
}
EXCEPTION_RE = re.compile(
    r"^(?P<name>(?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*(?:Error|Exception|Failure)):\s*(?P<message>.+)$"
)


def _run_command(
    argv: list[str], runner: Callable[..., subprocess.CompletedProcess[str]]
) -> subprocess.CompletedProcess[str]:
    return runner(argv, text=True, capture_output=True, check=False)


def _normalize_state(value: str) -> str:
    return value.strip().split()[0].rstrip("+").upper() if value.strip() else "UNKNOWN"


def _query_squeue(
    job_ids: list[str], runner: Callable[..., subprocess.CompletedProcess[str]]
) -> tuple[dict[str, dict[str, str]], str | None, str]:
    if not job_ids:
        return {}, None, ""
    completed = _run_command(
        ["squeue", "-h", "-j", ",".join(job_ids), "-o", "%i|%T|%R"], runner
    )
    if completed.returncode:
        error = completed.stderr.strip() or f"squeue exited {completed.returncode}"
        return {}, error, completed.stdout.strip()
    jobs: dict[str, dict[str, str]] = {}
    for line in completed.stdout.splitlines():
        parts = line.strip().split("|", 2)
        if len(parts) >= 2:
            jobs[parts[0]] = {
                "state": _normalize_state(parts[1]),
                "reason": parts[2].strip() if len(parts) == 3 else "",
            }
    return jobs, None, completed.stdout.strip()


def _query_sacct(
    job_ids: list[str], runner: Callable[..., subprocess.CompletedProcess[str]]
) -> tuple[dict[str, dict[str, str]], str | None, str]:
    if not job_ids:
        return {}, None, ""
    completed = _run_command(
        [
            "sacct", "-X", "-n", "-P", "-j", ",".join(job_ids),
            "--format=JobIDRaw,State,ExitCode,Elapsed",
        ],
        runner,
    )
    if completed.returncode:
        error = completed.stderr.strip() or f"sacct exited {completed.returncode}"
        return {}, error, completed.stdout.strip()
    jobs: dict[str, dict[str, str]] = {}
    wanted = set(job_ids)
    for line in completed.stdout.splitlines():
        parts = line.strip().split("|")
        if len(parts) >= 2 and parts[0] in wanted:
            jobs[parts[0]] = {
                "state": _normalize_state(parts[1]),
                "exit_code": parts[2].strip() if len(parts) > 2 else "",
                "elapsed": parts[3].strip() if len(parts) > 3 else "",
            }
    return jobs, None, completed.stdout.strip()


def _failure_reason(run_dir: Path, stage: str, job_id: str) -> str | None:
    log_path = run_dir / "logs" / f"{stage}.{job_id}.out"
    try:
        lines = log_path.read_text(errors="replace").splitlines()
    except OSError:
        return None

    exceptions = []
    for line in lines:
        match = EXCEPTION_RE.match(line.strip())
        if match:
            exceptions.append((match.group("name"), match.group("message")))
    useful = [item for item in exceptions if not item[0].endswith("StageFailure")]
    if useful:
        name, message = useful[-1]
        return f"{name}: {message}"
    if exceptions:
        name, message = exceptions[-1]
        return f"{name}: {message}"

    for line in reversed(lines):
        stripped = line.strip()
        if stripped and ("error" in stripped.lower() or "killed" in stripped.lower()):
            return stripped
    return None


def _blocked_stage(stage: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": stage["id"],
        "blocked_by": stage.get("blocked_by", []),
        "missing_outputs": len(stage.get("missing_products", [])),
        "invalid_outputs": len(stage.get("invalid_products", [])),
    }


def collect_status(
    run_dir: Path,
    plan: dict[str, Any],
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    """Return a compact, JSON-serializable status summary."""
    state_path = run_dir / "state" / "jobs.json"
    state = (
        json.loads(state_path.read_text())
        if state_path.exists()
        else {"jobs": {}, "intents": {}, "failures": {}}
    )
    jobs_state = state.get("jobs", {})
    planned = [stage for stage in plan["stages"] if stage["action"] == "run"]
    planned_ids = [stage["id"] for stage in planned]
    reused = [stage["id"] for stage in plan["stages"] if stage["action"] == "reuse"]
    blocked = [_blocked_stage(stage) for stage in plan["stages"] if stage["action"] == "blocked"]
    submitted_ids = [stage_id for stage_id in planned_ids if stage_id in jobs_state]
    unsubmitted = [stage_id for stage_id in planned_ids if stage_id not in jobs_state]
    job_ids = [str(jobs_state[stage_id]["job_id"]) for stage_id in submitted_ids]

    squeue, squeue_error, raw_squeue = _query_squeue(job_ids, runner)
    sacct, sacct_error, raw_sacct = _query_sacct(job_ids, runner)
    scheduler_errors = [error for error in (squeue_error, sacct_error) if error]

    jobs = []
    by_stage: dict[str, dict[str, Any]] = {}
    for stage_id in submitted_ids:
        job_id = str(jobs_state[stage_id]["job_id"])
        queue_item = squeue.get(job_id, {})
        account_item = sacct.get(job_id, {})
        scheduler_state = queue_item.get("state") or account_item.get("state")
        receipt = run_dir / "state" / f"receipt-{stage_id}.json"
        if not scheduler_state and receipt.is_file():
            scheduler_state = "COMPLETED"
        scheduler_state = scheduler_state or "UNKNOWN"
        item: dict[str, Any] = {
            "stage": stage_id,
            "job_id": job_id,
            "state": scheduler_state,
        }
        if account_item.get("exit_code"):
            item["exit_code"] = account_item["exit_code"]
        if account_item.get("elapsed"):
            item["elapsed"] = account_item["elapsed"]
        if queue_item.get("reason"):
            item["scheduler_reason"] = queue_item["reason"]
        if scheduler_state in FAILURE_STATES:
            reason = _failure_reason(run_dir, stage_id, job_id)
            if reason:
                item["failure_reason"] = reason
        jobs.append(item)
        by_stage[stage_id] = item

    # afterok children can remain pending forever when a parent fails. Report that
    # condition as dependency-blocked instead of ordinary pending work.
    changed = True
    while changed:
        changed = False
        for stage in planned:
            item = by_stage.get(stage["id"])
            if not item or item["state"] not in PENDING_STATES:
                continue
            failed_parents = [
                parent for parent in stage.get("parents", [])
                if by_stage.get(parent, {}).get("state") in FAILURE_STATES | {"DEPENDENCY_FAILED"}
            ]
            queue_reason = item.get("scheduler_reason", "")
            if failed_parents or "DependencyNeverSatisfied" in queue_reason:
                item["state"] = "DEPENDENCY_FAILED"
                item["failure_reason"] = (
                    "afterok dependency failed: " + ", ".join(failed_parents)
                    if failed_parents else queue_reason
                )
                changed = True

    successful = [item for item in jobs if item["state"] in SUCCESS_STATES]
    failed = [item for item in jobs if item["state"] in FAILURE_STATES]
    dependency_failed = [item for item in jobs if item["state"] == "DEPENDENCY_FAILED"]
    running = [item for item in jobs if item["state"] in RUNNING_STATES]
    pending = [item for item in jobs if item["state"] in PENDING_STATES]
    unknown = [
        item for item in jobs
        if item["state"] not in SUCCESS_STATES | FAILURE_STATES | RUNNING_STATES | PENDING_STATES | {"DEPENDENCY_FAILED"}
    ]

    submission_failures = [
        {"stage": stage, **details}
        for stage, details in state.get("failures", {}).items()
        if stage not in jobs_state
    ]
    unknown_submissions = [
        stage for stage in state.get("intents", {})
        if stage not in jobs_state
    ]

    finished = False
    if plan.get("unresolved"):
        overall = "FAILED"
    elif not planned:
        overall, finished = ("FAILED", True) if blocked else ("COMPLETED", True)
    elif not jobs_state:
        overall = "RENDERED_NOT_SUBMITTED"
    elif submission_failures:
        overall = "SUBMISSION_FAILED"
    elif unknown_submissions:
        overall = "UNKNOWN_SUBMISSION"
    elif unsubmitted:
        overall = "PARTIALLY_SUBMITTED"
    elif running or pending:
        overall = "RUNNING_WITH_FAILURES" if failed or dependency_failed or blocked else "RUNNING"
    elif failed or dependency_failed or blocked:
        overall, finished = "FAILED", True
    elif unknown:
        overall = "STATUS_UNKNOWN"
    else:
        overall, finished = "COMPLETED", True

    # A render-time blocked branch means the requested workflow is incomplete,
    # even if all independent submitted jobs have reached terminal states.
    if blocked and not running and not pending and not unsubmitted and not unknown:
        finished = True

    return {
        "run_id": plan["run_id"],
        "overall": overall,
        "finished": finished,
        "submission": {
            "planned_jobs": len(planned),
            "submitted_jobs": len(submitted_ids),
            "unsubmitted_jobs": unsubmitted,
        },
        "jobs": {
            "succeeded": len(successful),
            "failed": len(failed),
            "dependency_failed": len(dependency_failed),
            "running": len(running),
            "pending": len(pending),
            "unknown": len(unknown),
        },
        "stages": {
            "reused": len(reused),
            "reused_stages": reused,
            "blocked": len(blocked),
            "blocked_stages": blocked,
        },
        "failed_jobs": failed + dependency_failed,
        "running_jobs": running,
        "pending_jobs": pending,
        "unknown_jobs": unknown,
        "submission_failures": submission_failures,
        "unknown_submissions": unknown_submissions,
        "unresolved": plan.get("unresolved", []),
        "scheduler_errors": scheduler_errors,
        "_raw": {"state": state, "squeue": raw_squeue, "sacct": raw_sacct},
    }


def format_status(summary: dict[str, Any]) -> str:
    """Format a compact status intended for humans."""
    submission = summary["submission"]
    jobs = summary["jobs"]
    stages = summary["stages"]
    lines = [
        f"Run: {summary['run_id']}",
        f"Overall: {summary['overall']}",
        f"Finished: {'yes' if summary['finished'] else 'no'}",
        f"Submission: {submission['submitted_jobs']}/{submission['planned_jobs']} jobs submitted",
        (
            "Jobs: "
            f"{jobs['succeeded']} succeeded, {jobs['failed']} failed, "
            f"{jobs['dependency_failed']} dependency-blocked, {jobs['running']} running, "
            f"{jobs['pending']} pending, {jobs['unknown']} unknown"
        ),
        f"Plan: {stages['reused']} reused, {stages['blocked']} blocked",
    ]
    if submission["unsubmitted_jobs"]:
        lines.append("Unsubmitted: " + ", ".join(submission["unsubmitted_jobs"]))
    if summary["running_jobs"]:
        lines.append("Running jobs:")
        for item in summary["running_jobs"]:
            elapsed = f", elapsed {item['elapsed']}" if item.get("elapsed") else ""
            lines.append(f"  - {item['stage']} ({item['job_id']}): {item['state']}{elapsed}")
    if summary["pending_jobs"]:
        lines.append("Pending jobs:")
        for item in summary["pending_jobs"]:
            reason = f" — {item['scheduler_reason']}" if item.get("scheduler_reason") else ""
            lines.append(f"  - {item['stage']} ({item['job_id']}): {item['state']}{reason}")
    if summary["failed_jobs"]:
        lines.append("Failed jobs:")
        for item in summary["failed_jobs"]:
            details = []
            if item.get("exit_code"):
                details.append(f"exit {item['exit_code']}")
            if item.get("failure_reason"):
                details.append(item["failure_reason"])
            suffix = " — " + "; ".join(details) if details else ""
            lines.append(f"  - {item['stage']} ({item['job_id']}): {item['state']}{suffix}")
    if summary["submission_failures"]:
        lines.append("Submission failures:")
        for item in summary["submission_failures"]:
            lines.append(f"  - {item['stage']}: {item.get('stderr') or 'sbatch failed'}")
    if summary["unknown_submissions"]:
        lines.append("Unknown submissions: " + ", ".join(summary["unknown_submissions"]))
    if stages["blocked_stages"]:
        lines.append("Blocked stages:")
        for item in stages["blocked_stages"]:
            reasons = []
            if item["blocked_by"]:
                reasons.append("blocked by " + ", ".join(item["blocked_by"]))
            if item["missing_outputs"]:
                reasons.append(f"{item['missing_outputs']} missing outputs")
            if item["invalid_outputs"]:
                reasons.append(f"{item['invalid_outputs']} invalid outputs")
            lines.append(f"  - {item['stage']}: " + ("; ".join(reasons) or "blocked"))
    if summary["unresolved"]:
        lines.append("Unresolved: " + "; ".join(summary["unresolved"]))
    if summary["scheduler_errors"]:
        lines.append("Scheduler query warnings: " + "; ".join(summary["scheduler_errors"]))
    return "\n".join(lines) + "\n"
