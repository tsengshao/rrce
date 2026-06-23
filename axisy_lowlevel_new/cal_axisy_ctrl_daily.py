#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Build a shared CTRL daily NetCDF for x-axis diagnostics.

Only RRCE_3km_f00 is analyzed. The output day coordinate follows:
  day 0: sample it=0
  day 1: mean over it=1..72
  day 2: mean over it=73..144
  ...
  day 35: mean over it=2449..2520

The output day coordinate includes all CTRL times needed by experiment cases.
The experiment-to-CTRL-day mapping is stored in the y-data NetCDF, not here.

If a case_day is within +/-3 hours of an integer day, ctrl_day is rounded to
that integer day. Otherwise ctrl_day keeps the exact fractional day and is
computed from actual model output samples, without interpolation.

Output:
  {config.dataPath}/axisy_lowlevel/{center_flag}/axisy_ctrl_daily_profiles.nc
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, Optional, Sequence

import numpy as np
from netCDF4 import Dataset
import xarray as xr

sys.path.insert(1, "../")
import config  # noqa: E402

from cal_axisy_daily import (  # noqa: E402
    CENTER_FLAG,
    _avg_over_it,
    _snap_at_it,
    _wp_avg_fraction_over_it,
    _wp_snap_fraction_at_it,
)
from axisy_meta import ctrl_day_from_case_day, parse_restart_day  # noqa: E402


CTRL_EXP = "RRCE_3km_f00"
OUT_FILENAME = "axisy_ctrl_daily_profiles.nc"
ROUND_TO_INTEGER_TOLERANCE_HOURS = 3.0


def _norm_day(day: float) -> float:
    return float(round(float(day), 10))


def _unique_sorted(values: list[float]) -> np.ndarray:
    return np.asarray(sorted(set(_norm_day(v) for v in values)), dtype=np.float64)


def _day_sources(days: np.ndarray, base_days: Sequence[float], ctrl_days: Sequence[float], extra_days: Sequence[float]) -> np.ndarray:
    base_set = set(_norm_day(day) for day in base_days)
    ctrl_set = set(_norm_day(day) for day in ctrl_days)
    extra_set = set(_norm_day(day) for day in extra_days)
    sources = []
    for day in days:
        labels = []
        key = _norm_day(float(day))
        if key in base_set:
            labels.append("integer")
        if key in ctrl_set:
            labels.append("case")
        if key in extra_set:
            labels.append("extra")
        sources.append(",".join(labels))
    return np.asarray(sources, dtype="U")


def _window_for_day(day: float, nperday: int = 72) -> tuple[int, int]:
    if day == 0:
        return 0, 1
    end_it = int(round(day * nperday))
    return end_it - nperday + 1, end_it + 1


def _fill_profile_day(
    data: Dict[str, np.ndarray],
    iday: int,
    imethod: int,
    values: Dict[str, np.ndarray],
) -> None:
    for varname, arr in values.items():
        data[varname][iday, imethod, :, :] = arr


def main(
    center_flag: str = CENTER_FLAG,
    day0: int = 0,
    day1: int = 35,
    extra_days: Optional[Sequence[float]] = None,
    exact_case_exps: Optional[Sequence[str]] = None,
) -> None:
    datdir = os.path.join(config.dataPath, "axisy", center_flag)
    wpdir = os.path.join(config.dataPath, "wp")
    outdir = os.path.join(config.dataPath, "axisy_lowlevel", center_flag)
    os.makedirs(outdir, exist_ok=True)

    axmean_vars = ["cwv"]
    axproc_vars = ["radi_wind_lower", "tang_wind_lower"]
    all_vars = axmean_vars + axproc_vars

    sample = os.path.join(datdir, CTRL_EXP, "axmean-000000.nc")
    with Dataset(sample, "r") as nc:
        radius_km = np.asarray(nc.variables["radius"][:], dtype=np.float64) / 1e3

    extra_days = [] if extra_days is None else [_norm_day(day) for day in extra_days]
    exact_case_exps = set([] if exact_case_exps is None else exact_case_exps)

    exp_list = sorted(list(config.expList), key=lambda exp: (parse_restart_day(exp), exp))
    case_day = np.asarray([parse_restart_day(exp) for exp in exp_list], dtype=np.float64)
    ctrl_day = np.asarray(
        [
            ctrl_day_from_case_day(
                day,
                force_exact=(exp in exact_case_exps),
                tolerance_hours=ROUND_TO_INTEGER_TOLERANCE_HOURS,
            )
            for exp, day in zip(exp_list, case_day)
        ],
        dtype=np.float64,
    )

    base_days = [float(day) for day in range(day0, day1 + 1)]
    days = _unique_sorted(base_days + ctrl_day.tolist() + list(extra_days))
    day_source = _day_sources(days, base_days, ctrl_day.tolist(), extra_days)
    methods = ["instant", "daily"]
    vtype = ["mean", "axisymmetricity"]

    shape = (len(days), len(methods), len(vtype), len(radius_km))
    data = {var: np.full(shape, np.nan, dtype=np.float32) for var in all_vars}
    dry_fraction = np.full((len(days), len(methods)), np.nan, dtype=np.float32)
    window_start_it = np.full(len(days), -1, dtype=np.int32)
    window_end_it = np.full(len(days), -1, dtype=np.int32)
    instant_it = np.full(len(days), -1, dtype=np.int32)
    dry_thr = 30.0

    for iday, day in enumerate(days):
        it0, it1 = _window_for_day(float(day), nperday=72)
        snap_it = it1 - 1
        window_start_it[iday] = it0
        window_end_it[iday] = it1 - 1
        instant_it[iday] = snap_it

        daily_ax = _avg_over_it(datdir, CTRL_EXP, "axmean-{it:06d}.nc", it0, it1, axmean_vars)
        snap_ax = _snap_at_it(datdir, CTRL_EXP, "axmean-{it:06d}.nc", snap_it, axmean_vars)
        daily_pr = _avg_over_it(datdir, CTRL_EXP, "axmean_process-{it:06d}.nc", it0, it1, axproc_vars)
        snap_pr = _snap_at_it(datdir, CTRL_EXP, "axmean_process-{it:06d}.nc", snap_it, axproc_vars)

        _fill_profile_day(data, iday, 1, daily_ax)
        _fill_profile_day(data, iday, 0, snap_ax)
        _fill_profile_day(data, iday, 1, daily_pr)
        _fill_profile_day(data, iday, 0, snap_pr)

        dry_fraction[iday, 1] = _wp_avg_fraction_over_it(wpdir, CTRL_EXP, it0, it1, thr=dry_thr)
        dry_fraction[iday, 0] = _wp_snap_fraction_at_it(wpdir, CTRL_EXP, snap_it, thr=dry_thr)

        print(f"[done] day={float(day):g} daily=range({it0},{it1}) instant={snap_it}")

    ds = xr.Dataset(
        data_vars={
            **{var: (("day", "method", "vtype", "radius_km"), arr) for var, arr in data.items()},
            "dry_fraction": (("day", "method"), dry_fraction),
            "window_start_it": ("day", window_start_it),
            "window_end_it": ("day", window_end_it),
            "instant_it": ("day", instant_it),
            "day_source": ("day", day_source),
        },
        coords={
            "day": days,
            "method": methods,
            "vtype": vtype,
            "radius_km": radius_km,
            "extra_day": ("extra_day", np.asarray(extra_days, dtype=np.float64)),
            "exact_case_exp": ("exact_case_exp", np.asarray(sorted(exact_case_exps), dtype="U")),
        },
        attrs={
            "source_exp": CTRL_EXP,
            "center_flag": center_flag,
            "day_definition": "day 0 is it=0; day>0 is a 72-sample mean ending at round(day*72)",
            "ctrl_day_definition": "the day coordinate stores actual CTRL days available for exact plotting lookup",
            "case_mapping_policy": "experiment-to-CTRL-day mapping is stored in y-data NetCDF files, not in this CTRL file",
            "round_to_integer_tolerance_hours": float(ROUND_TO_INTEGER_TOLERANCE_HOURS),
            "extra_day_definition": "extra_day values are user-requested CTRL days and are never rounded",
            "exact_case_exp_definition": "case names listed here force ctrl_day to equal the original case_day without rounding",
            "instant_definition": "instant uses the last sample in each day window",
            "interpolation_policy": "no interpolation; plotting must exact-select existing day coordinates",
            "dry_fraction_definition": "fraction of (cwv < 30) from wp files; NaNs ignored",
            "dry_fraction_threshold": float(dry_thr),
        },
    )

    out_nc = os.path.join(outdir, OUT_FILENAME)
    ds.to_netcdf(out_nc)
    print("[write]", out_nc)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build shared RRCE_3km_f00 CTRL daily axisymmetric profiles.")
    parser.add_argument("--center-flag", default=CENTER_FLAG)
    parser.add_argument("--day0", type=int, default=0)
    parser.add_argument("--day1", type=int, default=35)
    parser.add_argument(
        "--extra-days",
        nargs="*",
        type=float,
        default=[],
        help="Additional CTRL days to compute exactly, e.g. --extra-days 8.5 12.25 30.27",
    )
    parser.add_argument(
        "--exact-case-exps",
        nargs="*",
        default=[],
        help="Case names whose case_day should not be rounded to an integer day.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    main(
        center_flag=args.center_flag,
        day0=args.day0,
        day1=args.day1,
        extra_days=args.extra_days,
        exact_case_exps=args.exact_case_exps,
    )
