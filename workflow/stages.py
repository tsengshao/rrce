"""The complete DAG in one reviewable table.

Edit ``STAGES`` to change resources, dependencies, or commands.  Commands use
named placeholders expanded by the renderer; no shell fragments come from a
manifest.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Resources:
    partition: str
    tasks: int
    ranks: int | None = None


@dataclass(frozen=True)
class Stage:
    id: str
    parents: tuple[str, ...]
    resources: Resources
    kind: str
    commands: tuple[str, ...]
    case_mode: str = "per_case_loop"
    parallel_cases: bool = False


SERIAL = Resources("ct112,cf112", 1)
GRADS = Resources("ct112,cf112", 112)

STAGES: tuple[Stage, ...] = (
    Stage("cwv", (), Resources("ct112", 72, 72), "python", ("cwv/wp.py {case}",)),
    Stage("convolve", (), Resources("ct448", 217, 217), "python", ("convolve/cal_convolve.py {case} 150",)),
    Stage("horisf", (), Resources("ct112", 72, 72), "python", ("horisf/cal_sf_fft.py {case}",)),
    Stage("center_0", (), SERIAL, "python", ("find_center/find_center_domain_mean.py {case} 0km",)),
    Stage("center_150", ("convolve",), SERIAL, "python", ("find_center/find_center_domain_mean.py {case} 150km",)),
    Stage("center_sf", ("horisf",), SERIAL, "python", ("find_center/find_center_domain_mean_sf.py {case}",)),
    Stage("cloud", (), Resources("cf448", 448, 29), "python", ("cloud/find_cloud.py {case}",)),
    Stage("wp_ctl", ("cwv",), SERIAL, "ctl", ("wp",)),
    Stage("convolve_ctl", ("convolve",), SERIAL, "ctl", ("convolve",)),
    Stage("sf_ctl", ("horisf",), SERIAL, "ctl", ("sf",)),
    Stage("water", ("wp_ctl", "center_0", "center_150", "center_sf"), GRADS, "grads", ("ani_water_wind/draw_water.gs",)),
    Stage("wind", ("wp_ctl", "center_0", "center_150", "center_sf"), GRADS, "grads", ("ani_water_wind/draw_wind.gs",)),
    Stage("center_zeta", ("center_0", "center_150", "center_sf", "convolve_ctl", "sf_ctl"), GRADS, "grads", ("ani_center/draw_zeta.gs",)),
    Stage("center_conzeta", ("center_0", "center_150", "center_sf", "convolve_ctl", "sf_ctl"), GRADS, "grads", ("ani_center/draw_conzeta.gs",)),
    Stage(
        "axisy_convert",
        ("cwv", "center_0"),
        Resources("ct448,cf448", 224, 217),
        "python",
        ("axisy/cal_axisy.py {case}",),
        parallel_cases=True,
    ),
    Stage("axisy_mean", ("axisy_convert",), Resources("ct112,cf112", 72, 72), "python", ("axisy/cal_axisymmetricity.py {case}",)),
    Stage("axisy_process", ("axisy_convert",), Resources("ct448,cf448", 217, 217), "python", ("axisy/cal_process_axisymmetricity.py {case}",)),
    Stage("axisy_daily", ("axisy_convert",), Resources("ct112,cf112", 3, 3), "python", ("axisy/cal_axisymmetricity_daily.py {case}",)),
    Stage("hov_radial", ("axisy_process",), SERIAL, "python", ("axisy/draw_hov_inflow.py {case} --component radial",)),
    Stage("hov_tangential", ("axisy_process",), SERIAL, "python", ("axisy/draw_hov_inflow.py {case} --component tangential",)),
    Stage("tang_daily", ("axisy_daily",), SERIAL, "python", ("axisy/draw_tang_wind_one_daily.py {case}",)),
    Stage("radi_daily", ("axisy_daily",), SERIAL, "python", ("axisy/draw_radi_wind_one_daily.py {case}",)),
    Stage("mse_ccc_daily", ("axisy_daily", "cloud", "center_0"), SERIAL, "python", ("axisy/draw_mse_ccc_daily.py {case}",)),
    Stage("lowlevel_exp", ("axisy_mean", "axisy_process", "cwv"), SERIAL, "lowlevel", ("build_exp",), "set_aggregate"),
    Stage("lowlevel_profiles", ("lowlevel_exp",), SERIAL, "lowlevel", ("profiles",), "set_aggregate"),
    Stage("scatter_dry", ("lowlevel_exp",), SERIAL, "lowlevel", ("scatter_dry",), "set_aggregate"),
    Stage("scatter_dxx", ("lowlevel_exp",), SERIAL, "lowlevel", ("scatter_dxx",), "set_aggregate"),
)

STAGE_BY_ID = {stage.id: stage for stage in STAGES}


def topological_order() -> tuple[Stage, ...]:
    seen: set[str] = set()
    ordered: list[Stage] = []

    def visit(stage: Stage, active: set[str]) -> None:
        if stage.id in active:
            raise ValueError(f"stage DAG cycle at {stage.id}")
        if stage.id in seen:
            return
        active.add(stage.id)
        for parent in stage.parents:
            if parent not in STAGE_BY_ID:
                raise ValueError(f"stage {stage.id}: unknown parent {parent}")
            visit(STAGE_BY_ID[parent], active)
        active.remove(stage.id)
        seen.add(stage.id)
        ordered.append(stage)

    for item in STAGES:
        visit(item, set())
    return tuple(ordered)
