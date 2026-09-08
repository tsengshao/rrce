"""Explicit, one-product entrypoints for the low-level aggregate plots."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType


CENTER = "czeta0km_positivemean"


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _prepare(run_dir: Path) -> tuple[dict, Path]:
    plan = json.loads((run_dir / "plan.json").read_text())
    sources = run_dir / "sources"
    lowlevel = sources / "axisy_lowlevel_new"
    axisy = sources / "axisy"
    sys.path[:] = [str(lowlevel), str(axisy), str(sources), *sys.path]
    _load(run_dir / "config.snapshot.py", "config")
    return plan, lowlevel


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--operation", choices=("build_exp", "profiles", "scatter_dry", "scatter_dxx"), required=True)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    plan, source = _prepare(run_dir)
    data_root = Path(plan["data_path"]) / "axisy_lowlevel" / CENTER
    exp_nc = data_root / f"axisy_exp_daily_profiles_{plan['dataset_tag']}.nc"
    output_root = Path(plan["data_path"]) / "workflow_figures" / plan["dataset_tag"] / "lowlevel"
    output_root.mkdir(parents=True, exist_ok=True)
    experiments = [case["experiment"] for case in plan["cases"]]
    hollow = [case["experiment"] for case in plan["cases"] if case["case_day"] is not None and not float(case["case_day"]).is_integer()]

    if args.operation == "build_exp":
        module = _load(source / "cal_axisy_exp_daily.py", "rrce_lowlevel_build")
        overwrite_path = run_dir / "state" / "overwrite.json"
        allowed = set(json.loads(overwrite_path.read_text())) if overwrite_path.exists() else set()
        if exp_nc.exists() and str(exp_nc) in allowed:
            exp_nc.unlink()
        module.main(exp_list=experiments, output_nc=str(exp_nc), require_all=True)
        return
    control = plan["external_inputs"].get("control_profile_nc")
    if not control:
        raise RuntimeError("control_profile_nc is required")
    previous = Path.cwd()
    os.chdir(output_root)
    try:
        if args.operation == "profiles":
            module = _load(source / "plot_inflow_cwv_sep.py", "rrce_lowlevel_profiles")
            module.main(nc_path=str(exp_nc), dset_tag="exp", days=tuple(plan["products"]["lowlevel_days"]), center_flag=CENTER)
        else:
            filename = "scatter_DRY.png" if args.operation == "scatter_dry" else "scatter_DXX.png"
            script = "plot_inflow_scatter_inDRY.py" if args.operation == "scatter_dry" else "plot_inflow_scatter_inDXX.py"
            module = _load(source / script, "rrce_lowlevel_scatter")
            module.main(ctrl_nc_path=control, y_nc_path=str(exp_nc), y_source_names=[plan["dataset_tag"]],
                        y_markers=["o"], y_day=plan["products"]["scatter_y_day"],
                        special_o_exps=hollow, special_x_exps=[], figname=filename)
    finally:
        os.chdir(previous)


if __name__ == "__main__":
    main()
