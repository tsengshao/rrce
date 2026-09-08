"""Command line interface for plan, render, submit, and status."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .planner import PlanError, build_plan, direct_request, plan_text, request_from_manifest
from .render import RenderError, render, verify_run
from .submit import SubmitError, submission_preview, submit


def _request(args: argparse.Namespace):
    if args.manifest:
        if args.config or args.cases or args.dataset_tag or args.run_id:
            raise PlanError("manifest conflicts with direct --config/--cases/--dataset-tag/--run-id fields")
        return request_from_manifest(args.manifest.resolve())
    if not args.config or not args.cases:
        raise PlanError("provide --manifest, or both --config and --cases")
    return direct_request(args.config, args.cases, args.dataset_tag, args.run_id)


def _add_plan_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--config")
    parser.add_argument("--cases", type=int, nargs="+")
    parser.add_argument("--dataset-tag")
    parser.add_argument("--run-id")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rrce-workflow")
    sub = parser.add_subparsers(dest="command", required=True)
    plan_parser = sub.add_parser("plan")
    _add_plan_inputs(plan_parser)
    plan_parser.add_argument("--dry-run", action="store_true", help="accepted for clarity; plan is always read-only")
    render_parser = sub.add_parser("render")
    _add_plan_inputs(render_parser)
    submit_parser = sub.add_parser("submit")
    submit_parser.add_argument("--run-dir", type=Path, required=True)
    submit_parser.add_argument("--dry-run", action="store_true")
    overwrite = submit_parser.add_mutually_exclusive_group()
    overwrite.add_argument(
        "--allow-overwrite", dest="allow_overwrite", action="store_true", default=None,
        help="override manifest and allow collisions recorded at render time",
    )
    overwrite.add_argument(
        "--no-overwrite", dest="allow_overwrite", action="store_false",
        help="override manifest and refuse existing runnable outputs",
    )
    status_parser = sub.add_parser("status")
    status_parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in {"plan", "render"}:
            request = _request(args)
            plan, cfg = build_plan(request)
            if args.command == "plan":
                print(plan_text(plan), end="")
                return 2 if plan["unresolved"] else 0
            run_dir = render(plan, cfg)
            print(run_dir)
            return 0
        if args.command == "submit":
            run_dir = args.run_dir.resolve()
            if args.dry_run:
                plan = verify_run(run_dir)
                state_path = run_dir / "state" / "jobs.json"
                state = json.loads(state_path.read_text()) if state_path.exists() else None
                for command in submission_preview(plan, state):
                    print(" ".join(command))
                return 2 if plan["unresolved"] else 0
            result = submit(run_dir, args.allow_overwrite)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        run_dir = args.run_dir.resolve()
        plan = verify_run(run_dir)
        state_path = run_dir / "state" / "jobs.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {"jobs": {}, "intents": {}}
        job_ids = [item["job_id"] for item in state["jobs"].values()]
        slurm = ""
        if job_ids:
            completed = subprocess.run(["squeue", "-h", "-j", ",".join(job_ids), "-o", "%i|%T"], text=True, capture_output=True, check=False)
            slurm = completed.stdout.strip()
        print(json.dumps({"run_id": plan["run_id"], "state": state, "squeue": slurm}, indent=2, sort_keys=True))
        return 0
    except (PlanError, RenderError, SubmitError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
