# cal_axisy_daily.py
"""
Compute axisymmetric/ring-mean daily (and snapshot) profiles for multiple experiments.

This replaces:
- cal_daily_cwv.py
- cal_daily_inflow.py

Key improvements:
- single script handles multiple variable groups (axmean + axmean_process)
- outputs a self-describing NetCDF (xarray) with exp coordinate and metadata
  (no more "values depend on config.expList ordering" traps)
- restart_day and labels are stored alongside data for robust plotting

Output:
  {config.dataPath}/axisy_lowlevel/{center_flag}/axisy_daily_profiles.nc
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List

import numpy as np
from netCDF4 import Dataset

# optional but strongly recommended output format
try:
    import xarray as xr
except Exception as e:
    xr = None

sys.path.insert(1, "../")
import config  # noqa: E402

from axisy_meta import (  # noqa: E402
    parse_restart_day,
    init_window_from_restart_day,
    last_window_default,
)

CENTER_FLAG = "czeta0km_positivemean"


def _read_profile_2d(nc: Dataset, varname: str) -> np.ndarray:
    """
    Read (vtype, radius) profile at time index 0.
    Works for both axmean and axmean_process in your files:
      (time, vtype, radius) -> return (vtype, radius)
    """
    arr = nc.variables[varname][0, ...]
    arr = np.asarray(arr)
    if arr.ndim != 2:
        raise ValueError(f"{varname}: expected (vtype,radius), got shape={arr.shape}")
    return arr


def _avg_over_it(datdir: str, exp: str, pattern: str, it0: int, it1: int, varnames: List[str]) -> Dict[str, np.ndarray]:
    """
    Average variables over it in [it0, it1).
    Returns dict: var -> (vtype, radius)
    """
    nit = it1 - it0
    out = {v: None for v in varnames}
    for it in range(it0, it1):
        fn = os.path.join(datdir, exp, pattern.format(it=it))
        with Dataset(fn, "r") as nc:
            for v in varnames:
                prof = _read_profile_2d(nc, v) / nit
                out[v] = prof if out[v] is None else out[v] + prof
    return out


def _snap_at_it(datdir: str, exp: str, pattern: str, it: int, varnames: List[str]) -> Dict[str, np.ndarray]:
    """
    Snapshot at exact it.
    Returns dict: var -> (vtype, radius)
    """
    fn = os.path.join(datdir, exp, pattern.format(it=it))
    out = {}
    with Dataset(fn, "r") as nc:
        for v in varnames:
            out[v] = _read_profile_2d(nc, v)
    return out

def _wp_read_cwv_fraction(fn: str, thr: float = 30.0) -> float:
    """
    Read wp-*.nc and compute fraction(cwv < thr) for time index 0.
    cwv shape: (time, yc, xc)
    """
    with Dataset(fn, "r") as nc:
        cwv = nc.variables["cwv"][0, ...]
        cwv = np.asarray(cwv, dtype=np.float64)

    good = np.isfinite(cwv)
    ngood = int(np.count_nonzero(good))
    if ngood == 0:
        return np.nan

    ndry = int(np.count_nonzero((cwv < thr) & good))
    return float(ndry / ngood)


def _wp_avg_fraction_over_it(wpdir: str, exp: str, it0: int, it1: int, thr: float = 30.0) -> float:
    """
    Average dry fraction over it in [it0, it1).
    Files: {wpdir}/{exp}/wp-{it:06d}.nc
    """
    vals = []
    for it in range(it0, it1):
        fn = os.path.join(wpdir, exp, f"wp-{it:06d}.nc")
        if not os.path.exists(fn):
            vals.append(np.nan)
            continue
        vals.append(_wp_read_cwv_fraction(fn, thr=thr))

    vals = np.asarray(vals, dtype=np.float64)
    if np.all(~np.isfinite(vals)):
        return np.nan
    return float(np.nanmean(vals))


def _wp_snap_fraction_at_it(wpdir: str, exp: str, it: int, thr: float = 30.0) -> float:
    """
    Snapshot dry fraction at exact it.
    """
    fn = os.path.join(wpdir, exp, f"wp-{it:06d}.nc")
    if not os.path.exists(fn):
        return np.nan
    return _wp_read_cwv_fraction(fn, thr=thr)


def main(center_flag: str = CENTER_FLAG) -> None:
    datdir = os.path.join(config.dataPath, "axisy", center_flag)
    outdir = os.path.join(config.dataPath, "axisy_lowlevel", center_flag)
    os.makedirs(outdir, exist_ok=True)

    # ---- variable groups you currently need ----
    axmean_vars = ["cwv"]
    axproc_vars = ["radi_wind_lower", "tang_wind_lower"]
    all_vars = axmean_vars + axproc_vars

    # ---- coords from a sample file ----
    sample = os.path.join(datdir, "RRCE_3km_f00_10", "axmean-000000.nc")
    with Dataset(sample, "r") as nc:
        radius_km = np.asarray(nc.variables["radius"][:]) / 1e3

    exp_list = list(config.expList)
    labels = [config.expdict[e] for e in exp_list]

    vtype = ["mean", "axisymmetricity"]
    period = ["init", "last"]
    method = ["instant", "daily"]

    # data array shape: (period, method, exp, vtype, radius)
    shape = (len(period), len(method), len(exp_list), len(vtype), len(radius_km))
    data = {v: np.full(shape, np.nan, dtype=np.float32) for v in all_vars}

    # scalar output: (period, method, exp)
    dry_fraction = np.full((len(period), len(method), len(exp_list)), np.nan, dtype=np.float32)
    wpdir = os.path.join(config.dataPath, "wp")
    dry_thr = 30.0

    restart_day = np.zeros(len(exp_list), dtype=float)

    ctrl = "RRCE_3km_f00"
    last0, last1 = last_window_default()

    for iexp, exp in enumerate(exp_list):
        rday = parse_restart_day(exp)
        restart_day[iexp] = rday
        init0, init1 = init_window_from_restart_day(rday, nperday=72)

        # ---- init comes from CTRL (RRCE_3km_f00) ----
        init_daily_ax = _avg_over_it(datdir, ctrl, "axmean-{it:06d}.nc", init0, init1, axmean_vars)
        init_snap_ax = _snap_at_it(datdir, ctrl, "axmean-{it:06d}.nc", init1 - 1, axmean_vars)

        init_daily_pr = _avg_over_it(datdir, ctrl, "axmean_process-{it:06d}.nc", init0, init1, axproc_vars)
        init_snap_pr = _snap_at_it(datdir, ctrl, "axmean_process-{it:06d}.nc", init1 - 1, axproc_vars)

        # dry fraction from wp files
        # init uses CTRL to match axisy init definition
        dry_fraction[0, 1, iexp] = _wp_avg_fraction_over_it(wpdir, ctrl, init0, init1, thr=dry_thr)
        dry_fraction[0, 0, iexp] = _wp_snap_fraction_at_it(wpdir, ctrl, init1 - 1, thr=dry_thr)

        # ---- last comes from each exp ----
        last_daily_ax = _avg_over_it(datdir, exp, "axmean-{it:06d}.nc", last0, last1, axmean_vars)
        last_snap_ax = _snap_at_it(datdir, exp, "axmean-{it:06d}.nc", last1 - 1, axmean_vars)

        last_daily_pr = _avg_over_it(datdir, exp, "axmean_process-{it:06d}.nc", last0, last1, axproc_vars)
        last_snap_pr = _snap_at_it(datdir, exp, "axmean_process-{it:06d}.nc", last1 - 1, axproc_vars)

        # last uses each experiment
        dry_fraction[1, 1, iexp] = _wp_avg_fraction_over_it(wpdir, exp, last0, last1, thr=dry_thr)
        dry_fraction[1, 0, iexp] = _wp_snap_fraction_at_it(wpdir, exp, last1 - 1, thr=dry_thr)


        # fill arrays
        for v in axmean_vars:
            data[v][0, 1, iexp, :, :] = init_daily_ax[v]
            data[v][0, 0, iexp, :, :] = init_snap_ax[v]
            data[v][1, 1, iexp, :, :] = last_daily_ax[v]
            data[v][1, 0, iexp, :, :] = last_snap_ax[v]

        for v in axproc_vars:
            data[v][0, 1, iexp, :, :] = init_daily_pr[v]
            data[v][0, 0, iexp, :, :] = init_snap_pr[v]
            data[v][1, 1, iexp, :, :] = last_daily_pr[v]
            data[v][1, 0, iexp, :, :] = last_snap_pr[v]

        print(
            f"[done] {iexp:02d} {exp} restart_day={rday:g} "
            f"init=range({init0},{init1}) last=range({last0},{last1})"
        )

    # ---- output ----
    out_nc = os.path.join(outdir, "axisy_daily_profiles.nc")

    if xr is None:
        # Fallback: npz with explicit metadata (still safer than old ordering-only files)
        out_npz = os.path.join(outdir, "axisy_daily_profiles.npz")
        np.savez(
            out_npz,
            exp=np.array(exp_list, dtype="U"),
            label=np.array(labels, dtype="U"),
            restart_day=restart_day,
            radius_km=radius_km,
            vtype=np.array(vtype, dtype="U"),
            period=np.array(period, dtype="U"),
            method=np.array(method, dtype="U"),
            **{k: v for k, v in data.items()},
        )
        print("[write fallback npz]", out_npz)
        return

    ds = xr.Dataset(
        data_vars={
            **{k: (("period", "method", "exp", "vtype", "radius_km"), v) for k, v in data.items()},
            "dry_fraction": (("period", "method", "exp"), dry_fraction),
        },
        coords={
            "period": period,
            "method": method,
            "exp": exp_list,
            "vtype": vtype,
            "radius_km": radius_km,
            "restart_day": ("exp", restart_day),
            "label": ("exp", np.array(labels, dtype="U")),
        },
        attrs={
            "center_flag": center_flag,
            "init_definition": "from CTRL (RRCE_3km_f00); window determined by restart_day; rday==0 uses (0,1)",
            "last_definition": "from each experiment; range(145,217) (72 samples)",
            "dry_fraction_definition": "fraction of (cwv < 30) from wp files; NaNs ignored",
            "dry_fraction_threshold": float(dry_thr),
        },
    )

    ds.to_netcdf(out_nc)
    print("[write]", out_nc)


if __name__ == "__main__":
    main()
