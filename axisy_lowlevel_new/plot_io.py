# plot_io.py
"""
Small utilities for plotting axisymmetric daily profiles from axisy_daily_profiles.nc.

Design goals:
- avoid relying on config.expList ordering
- make include/exclude and per-exp styling easy
"""

from __future__ import annotations

import re
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
