"""Shared CSV scale-radius lookup for the scale scatter plots."""

from __future__ import annotations

import os

import numpy as np


DEFAULT_SCALE_CSV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "data", "scale", "RRCE_3km_f00", "crossing_scale_time.csv",
)


def load_scale_csv(path=DEFAULT_SCALE_CSV_PATH):
    """Return sorted valid crossing times (days) and 3-sigma radii (km)."""
    data = np.genfromtxt(path, delimiter=",", names=True, encoding="utf-8-sig", ndmin=1)
    required = {"time_days", "scale_6sigma_km"}
    if not required.issubset(data.dtype.names or ()):
        raise ValueError(f"{path}: CSV must contain time_days and scale_6sigma_km")
    times = data["time_days"]
    scales = data["scale_6sigma_km"]
    valid = np.isfinite(times) & np.isfinite(scales)
    times, scales = times[valid], scales[valid]
    if times.size == 0:
        raise ValueError(f"{path}: no valid time/scale pairs")
    order = np.argsort(times)
    times, scales = times[order], scales[order]
    if np.any(np.diff(times) <= 0):
        raise ValueError(f"{path}: crossing times must be unique")
    if np.any(scales <= 0):
        raise ValueError(f"{path}: scales must be positive")
    radii = scales / 2.0
    print(
        f"[scale] {times.size} valid rows; skipped {np.count_nonzero(~valid)} rows; "
        f"time bounds {times[0]:.6f}..{times[-1]:.6f} days; "
        f"radius bounds {radii[0]:g}..{radii[-1]:g} km"
    )
    return times, radii


def scale_radius_for_days(ctrl_days, scale_times, scale_radii, matching="linear"):
    """Match CTRL days to radii; outside the time range use endpoint radii."""
    if matching not in ("linear", "nearest"):
        raise ValueError("scale_matching must be 'linear' or 'nearest'")
    days = np.asarray(ctrl_days, dtype=float)
    if not np.all(np.isfinite(days)):
        raise ValueError("Scale lookup requires finite ctrl_day values")
    if matching == "linear":
        return np.interp(days, scale_times, scale_radii)

    right = np.clip(np.searchsorted(scale_times, days), 0, len(scale_times) - 1)
    left = np.maximum(right - 1, 0)
    # An equal-distance tie uses the earlier crossing time.
    use_left = np.abs(days - scale_times[left]) <= np.abs(scale_times[right] - days)
    return scale_radii[np.where(use_left, left, right)]
