"""Build the canonical JSON-serializable workflow plan."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config_loader import ConfigError, ConfigSnapshot, load_config
from .contracts import inputs_for, inspect_products, outputs_for, validation_for
from .stages import STAGE_BY_ID, topological_order


class PlanError(ValueError):
    pass


@dataclass(frozen=True)
class PlanRequest:
    config: Path
    cases: tuple[int, ...]
    dataset_tag: str | None
    run_id: str | None
    actions: dict[str, str]
    external: dict[str, str]
    case_days: dict[str, float]
    resources: dict[str, dict[str, Any]]
    products: dict[str, Any]
    allow_overwrite: bool


def read_manifest(path: Path) -> dict[str, Any]:
    if path.suffix.lower() != ".toml":
        raise PlanError("manifest: TOML is required; YAML was only an early design draft")
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise PlanError(f"manifest: {exc}") from exc


def request_from_manifest(path: Path) -> PlanRequest:
    doc = read_manifest(path)
    run = doc.get("run", {})
    config_value = run.get("config")
    if not config_value:
        raise PlanError("run.config: required")
    allow_overwrite = run.get("allow_overwrite", False)
    if not isinstance(allow_overwrite, bool):
        raise PlanError("run.allow_overwrite: expected true or false")
    config = Path(config_value).expanduser()
    if not config.is_absolute():
        config = (path.parent / config).resolve()
    raw_actions = dict(doc.get("stages", {}))
    legacy_axisy = raw_actions.pop("axisy_postprocess", None)
    if legacy_axisy is not None:
        replacements = ("axisy_mean", "axisy_process", "axisy_daily")
        conflicts = [stage_id for stage_id in replacements if stage_id in raw_actions]
        if conflicts:
            raise PlanError("stages.axisy_postprocess conflicts with " + ", ".join(conflicts))
        for stage_id in replacements:
            raw_actions[stage_id] = legacy_axisy
    actions: dict[str, str] = {}
    for stage_id, table in raw_actions.items():
        if stage_id not in STAGE_BY_ID:
            raise PlanError(f"stages.{stage_id}: unknown stage")
        action = table.get("action") if isinstance(table, dict) else None
        if action not in {"run", "reuse", "auto"}:
            raise PlanError(f"stages.{stage_id}.action: expected 'run', 'reuse', or 'auto'")
        actions[stage_id] = action
    missing = [stage.id for stage in topological_order() if stage.id not in actions]
    if missing:
        raise PlanError("stages: every stage needs an explicit action; missing " + ", ".join(missing))
    resource_overrides = dict(doc.get("resources", {}))
    legacy_resources = resource_overrides.pop("axisy_postprocess", None)
    if legacy_resources is not None:
        replacements = ("axisy_mean", "axisy_process", "axisy_daily")
        conflicts = [stage_id for stage_id in replacements if stage_id in resource_overrides]
        if conflicts:
            raise PlanError("resources.axisy_postprocess conflicts with " + ", ".join(conflicts))
        for stage_id in replacements:
            resource_overrides[stage_id] = dict(legacy_resources)
    for stage_id, values in resource_overrides.items():
        if stage_id not in STAGE_BY_ID or not isinstance(values, dict):
            raise PlanError(f"resources.{stage_id}: unknown stage or invalid table")
        unknown = set(values) - {"partition", "tasks", "ranks"}
        if unknown:
            raise PlanError(f"resources.{stage_id}: unknown fields {sorted(unknown)}")
        if "tasks" in values and (not isinstance(values["tasks"], int) or values["tasks"] <= 0):
            raise PlanError(f"resources.{stage_id}.tasks: expected a positive integer")
        if "ranks" in values and values["ranks"] is not None and (not isinstance(values["ranks"], int) or values["ranks"] <= 0):
            raise PlanError(f"resources.{stage_id}.ranks: expected a positive integer or omitted")
    return PlanRequest(
        config=config,
        cases=tuple(run.get("cases", ())),
        dataset_tag=run.get("dataset_tag"),
        run_id=run.get("run_id"),
        actions=actions,
        external={key: str(value) for key, value in doc.get("inputs", {}).items()},
        case_days={key: float(value) for key, value in doc.get("case_days", {}).items()},
        resources=resource_overrides,
        products=doc.get("products", {}),
        allow_overwrite=allow_overwrite,
    )


def direct_request(config: str, cases: list[int], dataset_tag: str | None, run_id: str | None) -> PlanRequest:
    return PlanRequest(
        Path(config), tuple(cases), dataset_tag, run_id,
        {stage.id: "run" for stage in topological_order()}, {}, {}, {}, {}, False,
    )


def build_plan(request: PlanRequest) -> tuple[dict[str, Any], ConfigSnapshot]:
    try:
        cfg = load_config(request.config, request.cases, request.dataset_tag, request.case_days)
    except ConfigError as exc:
        raise PlanError(str(exc)) from exc
    unresolved: list[str] = []
    product_settings = {"lowlevel_days": [0, 3], "scatter_y_day": 3, **request.products}
    days = product_settings["lowlevel_days"]
    if not isinstance(days, list) or not days or any(not isinstance(day, int) or day < 0 for day in days):
        raise PlanError("products.lowlevel_days: expected a non-empty list of non-negative integers")
    scatter_day = product_settings["scatter_y_day"]
    if not isinstance(scatter_day, int) or scatter_day < 0:
        raise PlanError("products.scatter_y_day: expected a non-negative integer")
    if any(case.case_day is None for case in cfg.cases):
        names = [case.experiment for case in cfg.cases if case.case_day is None]
        unresolved.append("case_days required for: " + ", ".join(names))

    stages: list[dict[str, Any]] = []
    planned_by_id: dict[str, dict[str, Any]] = {}
    case_total_t = {case.index: case.total_t for case in cfg.cases}
    for stage in topological_order():
        requested_action = request.actions[stage.id]
        outputs = outputs_for(stage.id, cfg, product_settings)
        validation = validation_for(stage.id)
        state = inspect_products(outputs, validation, case_total_t)
        valid_paths = set(state["valid"])
        incomplete_paths = state["missing"] + [item["path"] for item in state["invalid"]]
        skipped_cases: list[int] = []
        action = requested_action
        if requested_action == "auto":
            if stage.case_mode == "per_case_loop":
                for case in cfg.cases:
                    case_outputs = [item for item in outputs if item.case_index == case.index]
                    if case_outputs and all(str(item.path) in valid_paths for item in case_outputs):
                        skipped_cases.append(case.index)
                action = "reuse" if len(skipped_cases) == len(cfg.cases) else "run"
            else:
                action = "reuse" if not incomplete_paths else "run"
        external_inputs = inputs_for(stage.id, cfg, request.external)
        external_errors: list[str] = []
        if stage.id in {"lowlevel_profiles", "scatter_dry", "scatter_dxx"} and not external_inputs:
            external_errors.append(f"inputs.control_profile_nc required by {stage.id}")
        for path in external_inputs:
            if not path.is_file():
                external_errors.append(f"external input does not exist: {path}")

        blocked_by: list[str] = []
        for parent_id in stage.parents:
            parent = planned_by_id[parent_id]
            if parent["action"] == "blocked":
                blocked_by.extend(parent["blocked_by"] or [parent_id])
        if requested_action == "reuse" and incomplete_paths:
            blocked_by.append(stage.id)
        if external_errors:
            blocked_by.append(stage.id)
        blocked_by = list(dict.fromkeys(blocked_by))
        if blocked_by:
            action = "blocked"

        resources = {
            "partition": stage.resources.partition,
            "tasks": stage.resources.tasks,
            "ranks": stage.resources.ranks,
        }
        resources.update(request.resources.get(stage.id, {}))
        if resources["ranks"] is not None and resources["ranks"] > resources["tasks"]:
            raise PlanError(f"resources.{stage.id}.ranks cannot exceed tasks")
        collisions = state["existing"] if action == "run" else []
        if action == "run" and requested_action == "auto" and skipped_cases:
            skipped = set(skipped_cases)
            collisions = [
                str(item.path) for item in outputs
                if item.case_index not in skipped and item.path.exists()
            ]
        stage_plan = {
            "id": stage.id,
            "parents": list(stage.parents),
            "action": action,
            "requested_action": requested_action,
            "skipped_cases": skipped_cases,
            "blocked_by": blocked_by,
            "kind": stage.kind,
            "case_mode": stage.case_mode,
            "resources": resources,
            "commands": list(stage.commands),
            "inputs": [str(path) for path in external_inputs],
            "outputs": [product.as_dict() for product in outputs],
            "validation": validation,
            "collisions": collisions,
            "missing_products": state["missing"],
            "invalid_products": state["invalid"],
            "external_errors": external_errors,
            "missing_reuse": incomplete_paths if requested_action == "reuse" else [],
        }
        stages.append(stage_plan)
        planned_by_id[stage.id] = stage_plan
    plan = {
        "schema_version": 1,
        "run_id": request.run_id,
        "repo_root": str(Path(__file__).resolve().parent.parent),
        "config": {"path": str(cfg.path), "sha256": cfg.sha256},
        "dataset_tag": cfg.dataset_tag,
        "dataset_tag_source": cfg.dataset_tag_source,
        "vvm_path": str(cfg.vvm_path),
        "data_path": str(cfg.data_path),
        "cases": [case.as_dict() for case in cfg.cases],
        "external_inputs": request.external,
        "products": product_settings,
        "allow_overwrite": request.allow_overwrite,
        "stages": stages,
        "unresolved": sorted(set(unresolved)),
        "daily_definitions": {
            "axisy_daily": "day N averages indexes N*72 through N*72+71",
            "lowlevel": "day 0 is index 0; day N>0 averages (N-1)*72+1 through N*72",
        },
    }
    return plan, cfg


def plan_text(plan: dict[str, Any]) -> str:
    return json.dumps(plan, indent=2, sort_keys=True) + "\n"
