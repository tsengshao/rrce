# plot_io.py
"""
Small utilities for plotting axisymmetric daily profiles from axisy_daily_profiles.nc.

Design goals:
- avoid relying on config.expList ordering
- make include/exclude and per-exp styling easy
"""

from __future__ import annotations

import re
import os
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import xarray as xr


def load_axisy_daily_profiles(nc_path: str) -> xr.Dataset:
    """Load the NetCDF produced by cal_axisy_daily.py."""
    return xr.open_dataset(nc_path)


def select_experiments(
    ds: xr.Dataset,
    include: Optional[Sequence[str]] = None,
    exclude: Optional[Sequence[str]] = None,
    regex: Optional[str] = None,
) -> xr.Dataset:
    """
    Return a filtered dataset by exp names.

    - include: explicit list of exp names (keeps order)
    - exclude: exp names to drop
    - regex: keep only exp names matching regex (applied after include/exclude)
    """
    out = ds
    if include is not None:
        out = out.sel(exp=list(include))
    if exclude:
        out = out.sel(exp=~out["exp"].isin(list(exclude)))
    if regex:
        pat = re.compile(regex)
        keep = [e for e in out["exp"].values.tolist() if pat.search(e)]
        out = out.sel(exp=keep)
    return out


def as_path_list(value):
    if value is None:
        return None
    if isinstance(value, (str, os.PathLike)):
        return [str(value)]
    return list(value)


def source_names(paths, names):
    if names is not None:
        names = list(names)
        if len(names) != len(paths):
            raise ValueError("y_source_names must have the same length as y_nc_paths")
        return names
    return [os.path.splitext(os.path.basename(path))[0] for path in paths]


def source_markers(nsource: int, markers=None):
    default = ["o", "^", "x", "s", "D", "v", "P"]
    markers = default if markers is None else list(markers)
    if len(markers) < nsource:
        raise ValueError("y_markers must provide at least one marker per y_nc file")
    return markers[:nsource]


def select_existing_exps(ds: xr.Dataset, include=None, exclude=None, regex=None) -> xr.Dataset:
    out = select_experiments(ds, include=include, exclude=exclude, regex=regex)
    exp_vals = [str(exp) for exp in out["exp"].values.tolist() if str(exp) != "RRCE_3km_f00"]
    return out.sel(exp=exp_vals)


def match_existing_days(day_coord: xr.DataArray, requested_days: np.ndarray, context: str, coord_label: str) -> np.ndarray:
    available = np.asarray(day_coord.values, dtype=np.float64)
    matched = []
    missing = []
    for day in requested_days:
        idx = np.where(np.isclose(available, day, rtol=0.0, atol=1e-9))[0]
        if len(idx) != 1:
            missing.append(float(day))
        else:
            matched.append(float(available[idx[0]]))
    if missing:
        raise ValueError(
            f"{context}: {coord_label} coordinate is missing required exact day(s) {missing}. "
            "Plotting does not interpolate or use nearest."
        )
    return np.asarray(matched, dtype=np.float64)


def ctrl_data_for_exps(
    ctrl_ds: xr.Dataset,
    exp_vals,
    ctrl_days: np.ndarray,
    varname: str,
    method: str,
    vtype: str | None = None,
):
    if "day" not in ctrl_ds.coords:
        raise ValueError("CTRL nc must contain a day coordinate")

    ctrl_day = np.asarray(ctrl_days, dtype=np.float64)
    if len(ctrl_day) != len(exp_vals):
        raise ValueError(f"{varname}: exp_vals and ctrl_days must have the same length")

    matched_day = match_existing_days(ctrl_ds["day"], ctrl_day, f"{varname}", "CTRL day")
    day_indexer = xr.DataArray(matched_day, dims=("exp",), coords={"exp": exp_vals}, name="day")

    selector = {"day": day_indexer, "method": method}
    if vtype is not None:
        selector["vtype"] = vtype

    out = ctrl_ds[varname].sel(selector)
    out = out.assign_coords(
        exp=("exp", exp_vals),
        ctrl_day=("exp", ctrl_day),
    )
    return out


def y_tang_wind_profile_for_source(ds: xr.Dataset, source_name: str, y_day: float, method: str) -> xr.DataArray:
    if "day" not in ds.coords:
        raise ValueError(f"{source_name}: y nc must contain a day coordinate")
    matched_day = match_existing_days(ds["day"], np.asarray([y_day], dtype=np.float64), source_name, "y day")[0]
    return ds["tang_wind_lower"].sel({"day": matched_day, "method": method, "vtype": "mean"})


def to_vtype_radius(arr: xr.DataArray, vtype_order=("mean", "axisymmetricity")) -> np.ndarray:
    """
    Convert a (vtype, radius_km) DataArray to a numpy array shaped (2, nradius)
    in the requested vtype order.
    """
    a = arr.sel(vtype=list(vtype_order)).transpose("vtype", "radius_km").values
    return np.asarray(a)


def format_rday(rday: float) -> str:
    """Match your historical formatting: int if integer-like, else float."""
    if abs(rday - round(rday)) < 1e-9:
        return str(int(round(rday)))
    return f"{rday:g}"
