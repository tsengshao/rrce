#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Build daily NetCDF diagnostics for multiple experiment cases.

The output day coordinate follows:
  day 0: sample it=0
  day 1: mean over it=1..72
  day 2: mean over it=73..144
  day 3: mean over it=145..216

Default output:
  {config.dataPath}/axisy_lowlevel/{center_flag}/axisy_exp_daily_profiles.nc

This file is meant to be used as the y-axis data source. It stores explicit
``exp`` and ``case_day/restart_day`` metadata, so plotting code can align it by
case name with ``axisy_ctrl_daily_profiles.nc`` without trusting list order.
"""

from __future__ import annotations

import os
import sys
from typing import Dict, Optional, Sequence

import numpy as np
from netCDF4 import Dataset
import xarray as xr

sys.path.insert(1, "../")
import config  # noqa: E402

from axisy_meta import ctrl_day_from_case_day, parse_restart_day  # noqa: E402
from cal_axisy_daily import (  # noqa: E402
    CENTER_FLAG,
    _wp_avg_fraction_over_it,
    _wp_snap_fraction_at_it,
)


OUT_FILENAME = "axisy_exp_daily_profiles.nc"
ROUND_TO_INTEGER_TOLERANCE_HOURS = 3.0


class SkipCase(Exception):
    def __init__(self, exp: str, filename: str, reason: str):
        super().__init__(f"{exp}: {filename}: {reason}")
        self.exp = exp
        self.filename = filename
        self.reason = reason


def _window_for_day(day: int, nperday: int = 72) -> tuple[int, int]:
    if day == 0:
        return 0, 1
    return (day - 1) * nperday + 1, day * nperday + 1


def _default_exp_list() -> list[str]:
    exps = list(config.expList)
    return sorted(exps, key=lambda exp: (parse_restart_day(exp), exp))


def _fill_profile_day(data: Dict[str, np.ndarray], iday: int, imethod: int, values: Dict[str, np.ndarray]) -> None:
    for varname, arr in values.items():
        data[varname][iday, imethod, :, :] = arr


def _read_profile_2d_required(exp: str, filename: str, nc: Dataset, varname: str, profile_shape: tuple[int, int]) -> np.ndarray:
    if varname not in nc.variables:
        raise SkipCase(exp, filename, f"missing variable {varname}")
    arr = np.asarray(nc.variables[varname][0, ...], dtype=np.float32)
    if arr.shape != profile_shape:
        raise SkipCase(exp, filename, f"{varname} shape {arr.shape}, expected {profile_shape}")
    return arr


def _avg_over_it_required(
    datdir: str,
    exp: str,
    pattern: str,
    it0: int,
    it1: int,
    varnames: Sequence[str],
    profile_shape: tuple[int, int],
) -> Dict[str, np.ndarray]:
    out = {var: np.zeros(profile_shape, dtype=np.float64) for var in varnames}

    for it in range(it0, it1):
        fn = os.path.join(datdir, exp, pattern.format(it=it))
        if not os.path.exists(fn):
            raise SkipCase(exp, fn, "missing file")
        with Dataset(fn, "r") as nc:
            for var in varnames:
                out[var] += _read_profile_2d_required(exp, fn, nc, var, profile_shape)

    nit = it1 - it0
    return {var: (arr / nit).astype(np.float32) for var, arr in out.items()}


def _snap_at_it_required(
    datdir: str,
    exp: str,
    pattern: str,
    it: int,
    varnames: Sequence[str],
    profile_shape: tuple[int, int],
) -> Dict[str, np.ndarray]:
    fn = os.path.join(datdir, exp, pattern.format(it=it))
    if not os.path.exists(fn):
        raise SkipCase(exp, fn, "missing file")

    out = {}
    with Dataset(fn, "r") as nc:
        for var in varnames:
            out[var] = _read_profile_2d_required(exp, fn, nc, var, profile_shape)
    return out


def main(
    center_flag: str = CENTER_FLAG,
    day0: int = 0,
    day1: int = 3,
    exp_list: Optional[Sequence[str]] = None,
    exact_case_exps: Optional[Sequence[str]] = None,
) -> None:
    datdir = os.path.join(config.dataPath, "axisy", center_flag)
    wpdir = os.path.join(config.dataPath, "wp")
    outdir = os.path.join(config.dataPath, "axisy_lowlevel", center_flag)
    os.makedirs(outdir, exist_ok=True)

    exps = _default_exp_list() if exp_list is None else list(exp_list)
    exact_case_exps = set([] if exact_case_exps is None else exact_case_exps)
    axmean_vars = ["cwv"]
    axproc_vars = ["radi_wind_lower", "tang_wind_lower"]
    all_vars = axmean_vars + axproc_vars

    sample = os.path.join(datdir, exps[0], "axmean-000000.nc")
    with Dataset(sample, "r") as nc:
        radius_km = np.asarray(nc.variables["radius"][:], dtype=np.float64) / 1e3
        nvtype = len(nc.variables["vtype"][:])
    profile_shape = (nvtype, len(radius_km))

    days = np.arange(day0, day1 + 1, dtype=np.int32)
    methods = ["instant", "daily"]
    vtype = ["mean", "axisymmetricity"]

    case_shape = (len(days), len(methods), len(vtype), len(radius_km))
    dry_thr = 30.0
    valid_exps = []
    skipped = []
    data_by_var = {var: [] for var in all_vars}
    dry_by_exp = []

    for exp in exps:
        case_data = {var: np.full(case_shape, np.nan, dtype=np.float32) for var in all_vars}
        case_dry = np.full((len(days), len(methods)), np.nan, dtype=np.float32)
        try:
            for iday, day in enumerate(days):
                it0, it1 = _window_for_day(int(day), nperday=72)
                snap_it = it1 - 1

                daily_ax = _avg_over_it_required(
                    datdir, exp, "axmean-{it:06d}.nc", it0, it1, axmean_vars, profile_shape
                )
                snap_ax = _snap_at_it_required(
                    datdir, exp, "axmean-{it:06d}.nc", snap_it, axmean_vars, profile_shape
                )
                daily_pr = _avg_over_it_required(
                    datdir, exp, "axmean_process-{it:06d}.nc", it0, it1, axproc_vars, profile_shape
                )
                snap_pr = _snap_at_it_required(
                    datdir, exp, "axmean_process-{it:06d}.nc", snap_it, axproc_vars, profile_shape
                )

                _fill_profile_day(case_data, iday, 1, daily_ax)
                _fill_profile_day(case_data, iday, 0, snap_ax)
                _fill_profile_day(case_data, iday, 1, daily_pr)
                _fill_profile_day(case_data, iday, 0, snap_pr)

                case_dry[iday, 1] = _wp_avg_fraction_over_it(wpdir, exp, it0, it1, thr=dry_thr)
                case_dry[iday, 0] = _wp_snap_fraction_at_it(wpdir, exp, snap_it, thr=dry_thr)

                print(f"[done] {len(valid_exps):02d} {exp} day={int(day):02d} daily=range({it0},{it1}) instant={snap_it}")
        except SkipCase as e:
            skipped.append(e)
            print(f"[skip] {exp}: {e.filename}: {e.reason}")
            continue

        valid_exps.append(exp)
        for var in all_vars:
            data_by_var[var].append(case_data[var])
        dry_by_exp.append(case_dry)

    if not valid_exps:
        raise RuntimeError("No valid experiments remained after skipping missing-variable cases.")

    labels = [config.expdict.get(exp, exp) for exp in valid_exps]
    case_day = np.asarray([parse_restart_day(exp) for exp in valid_exps], dtype=np.float64)
    ctrl_day = np.asarray(
        [
            ctrl_day_from_case_day(
                day,
                force_exact=(exp in exact_case_exps),
                tolerance_hours=ROUND_TO_INTEGER_TOLERANCE_HOURS,
            )
            for exp, day in zip(valid_exps, case_day)
        ],
        dtype=np.float64,
    )
    data = {var: np.stack(arrs, axis=0).astype(np.float32) for var, arrs in data_by_var.items()}
    dry_fraction = np.stack(dry_by_exp, axis=0).astype(np.float32)

    ds = xr.Dataset(
        data_vars={
            **{
                var: (("exp", "day", "method", "vtype", "radius_km"), arr)
                for var, arr in data.items()
            },
            "dry_fraction": (("exp", "day", "method"), dry_fraction),
        },
        coords={
            "exp": np.asarray(valid_exps, dtype="U"),
            "label": ("exp", np.asarray(labels, dtype="U")),
            "case_day": ("exp", case_day),
            "restart_day": ("exp", case_day),
            "ctrl_day": ("exp", ctrl_day),
            "day": days,
            "method": methods,
            "vtype": vtype,
            "radius_km": radius_km,
        },
        attrs={
            "center_flag": center_flag,
            "exp_order": "sorted by (case_day, exp name); do not rely on order, align by exp name",
            "day_definition": "day 0 is it=0; day N>0 is mean over it=(N-1)*72+1..N*72 inclusive",
            "case_day_definition": "case_day/restart_day is the original day parsed from each case name",
            "ctrl_day_definition": "ctrl_day is the day this y-data case should use when looking up CTRL x-axis data; case_day within +/-3h of an integer is rounded unless exact_case_exps is used",
            "round_to_integer_tolerance_hours": float(ROUND_TO_INTEGER_TOLERANCE_HOURS),
            "instant_definition": "instant uses the last sample in each day window",
            "missing_profile_policy": "cases with missing required profile files/variables are skipped entirely and reported at script end",
            "dry_fraction_definition": "fraction of (cwv < 30) from wp files; NaNs ignored",
            "dry_fraction_threshold": float(dry_thr),
        },
    )

    out_nc = os.path.join(outdir, OUT_FILENAME)
    ds.to_netcdf(out_nc)
    print("[write]", out_nc)
    print(f"[summary] wrote {len(valid_exps)} cases; skipped {len(skipped)} cases")
    if skipped:
        print("[skipped cases]")
        for item in skipped:
            print(f"  {item.exp}: {item.filename}: {item.reason}")


if __name__ == "__main__":
    main()
