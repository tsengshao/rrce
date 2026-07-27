"""
Draw separate inflow/CWV profiles from the EXP and CTRL daily NetCDF files.

EXP data are selected by exp, day, and method. CTRL data have no exp
dimension and are selected by day and method only. Each main() call draws one
dataset; the script entry point calls CTRL, EXP, and EXP_ORI separately.

Outputs:
  ./{center_flag}_sap_white/{tag}/exp/
  ./{center_flag}_sap_white/{tag}/ctrl/
  ./{center_flag}_sap_white/{tag}/exp_ori/
or the corresponding ./{center_flag}_sap/ directories.
"""

from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(1, "../")
import config  # noqa: E402

import util_draw as udraw  # noqa: E402
from plot_io import (  # noqa: E402
    format_rday,
    load_axisy_daily_profiles,
    match_existing_days,
    select_experiments,
    to_vtype_radius,
)


PROFILE_VARS = ("tang_wind_lower", "radi_wind_lower", "cwv")
VTYPE_ORDER = ("mean", "axisymmetricity")
METHOD_BY_TAG = {
    "inflow_daily": "daily",
    "inflow_snapshot": "instant",
}


def _normalize_days(days, context: str) -> np.ndarray:
    if np.isscalar(days):
        requested = np.asarray([days], dtype=np.float64)
    else:
        requested = np.asarray(list(days), dtype=np.float64)

    if requested.ndim != 1 or requested.size == 0:
        raise ValueError(f"{context}: days must contain at least one scalar day")
    if not np.isfinite(requested).all():
        raise ValueError(f"{context}: days must contain only finite values")
    if len(np.unique(requested)) != len(requested):
        raise ValueError(f"{context}: days must not contain duplicate values")
    return requested


def _validate_dataset(ds, dset_tag: str, method: str, requested_days: np.ndarray) -> np.ndarray:
    required_coords = {"day", "method", "vtype", "radius_km"}
    if dset_tag == "exp":
        required_coords.add("exp")

    missing_coords = sorted(required_coords.difference(ds.coords))
    if missing_coords:
        raise ValueError(f"{dset_tag.upper()} nc is missing required coordinate(s): {missing_coords}")

    missing_vars = sorted(set(PROFILE_VARS).difference(ds.data_vars))
    if missing_vars:
        raise ValueError(f"{dset_tag.upper()} nc is missing required variable(s): {missing_vars}")

    available_methods = [str(value) for value in ds["method"].values.tolist()]
    if method not in available_methods:
        raise ValueError(
            f"{dset_tag.upper()} nc does not contain method={method!r}; "
            f"available methods are {available_methods}"
        )

    available_vtypes = [str(value) for value in ds["vtype"].values.tolist()]
    missing_vtypes = [value for value in VTYPE_ORDER if value not in available_vtypes]
    if missing_vtypes:
        raise ValueError(
            f"{dset_tag.upper()} nc is missing required vtype value(s): {missing_vtypes}"
        )

    return match_existing_days(
        ds["day"],
        requested_days,
        context=f"{dset_tag.upper()} plotting",
        coord_label="day",
    )


def _day_token(day: float) -> str:
    if abs(day - round(day)) < 1e-9:
        return f"{int(round(day)):02d}"
    return format_rday(day).replace("-", "m").replace(".", "p")


def _day_title(day: float, method: str, dset_tag: str) -> str:
    day_text = format_rday(day)
    if abs(day) < 1e-9:
        if dset_tag == "exp":
            return "day 0 (init; it=0)"
        return "day 0 (it=0)"
    if abs(day - 3.0) < 1e-9:
        if method == "daily":
            return "day 3 mean (+48 ~ +72 hrs)"
        return "day 3 snapshot (+72 hrs)"
    if method == "daily":
        return f"day {day_text} mean"
    return f"day {day_text} snapshot"


def _select_profiles(ds, selector) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    twind = to_vtype_radius(ds["tang_wind_lower"].sel(selector), VTYPE_ORDER)
    rwind = to_vtype_radius(ds["radi_wind_lower"].sel(selector), VTYPE_ORDER)
    cwv = to_vtype_radius(ds["cwv"].sel(selector), VTYPE_ORDER)
    return twind, rwind, cwv


def _draw_profile(
    radius_km: np.ndarray,
    twind: np.ndarray,
    rwind: np.ndarray,
    cwv: np.ndarray,
    left_title: str,
    right_title: str,
    output_path: str,
) -> None:
    fig = plt.figure(figsize=(10 * 1.2, 6 * 1.2))
    try:
        ax = fig.add_axes([0.12, 0.15, 0.8, 0.7])
        udraw.draw_pannel_3vars(ax, radius_km, twind, rwind, cwv)
        ax.set_title(right_title, loc="right", fontweight="bold")
        ax.set_title("    " + left_title, loc="left", fontweight="bold")
        fig.savefig(output_path, dpi=200)
    finally:
        plt.close(fig)


def plot_exp_dataset(
    nc_path: str,
    days,
    method: str,
    figdir: str,
    dataset_label: str = "exp",
    include=None,
    exclude=None,
    regex=None,
) -> None:
    requested_days = _normalize_days(days, "EXP plotting")
    ds = load_axisy_daily_profiles(nc_path)
    try:
        matched_days = _validate_dataset(ds, "exp", method, requested_days)
        selected = select_experiments(ds, include=include, exclude=exclude, regex=regex)
        if selected.sizes.get("exp", 0) == 0:
            raise ValueError("No EXP cases remain after applying experiment filters")

        print("dataset:", dataset_label)
        print("method:", method)
        print("days:", matched_days.tolist())

        radius_km = np.asarray(selected["radius_km"].values)
        for exp_value in selected["exp"].values.tolist():
            exp = str(exp_value)
            if "label" in selected:
                exp_label = str(selected["label"].sel(exp=exp).item())
            else:
                exp_label = config.expdict.get(exp, exp)

            for day in matched_days:
                day = float(day)
                selector = {"exp": exp, "day": day, "method": method}
                twind, rwind, cwv = _select_profiles(selected, selector)
                filename = f"{exp}_day{_day_token(day)}_{method}.png"
                output_path = os.path.join(figdir, filename)
                _draw_profile(
                    radius_km,
                    twind,
                    rwind,
                    cwv,
                    left_title=exp_label,
                    right_title=_day_title(day, method, "exp"),
                    output_path=output_path,
                )
                print("[saved]", output_path)
    finally:
        ds.close()


def plot_ctrl_dataset(nc_path: str, days, method: str, figdir: str) -> None:
    requested_days = _normalize_days(days, "CTRL plotting")
    ds = load_axisy_daily_profiles(nc_path)
    try:
        matched_days = _validate_dataset(ds, "ctrl", method, requested_days)
        print("dataset: ctrl")
        print("method:", method)
        print("days:", matched_days.tolist())

        radius_km = np.asarray(ds["radius_km"].values)
        source_exp = str(ds.attrs.get("source_exp", "CTRL"))
        source_label = config.expdict.get(source_exp, source_exp)

        for day in matched_days:
            day = float(day)
            selector = {"day": day, "method": method}
            twind, rwind, cwv = _select_profiles(ds, selector)
            filename = f"{source_label}_day{_day_token(day)}_{method}.png"
            output_path = os.path.join(figdir, filename)
            _draw_profile(
                radius_km,
                twind,
                rwind,
                cwv,
                left_title=source_label,
                right_title=_day_title(day, method, "ctrl"),
                output_path=output_path,
            )
            print("[saved]", output_path)
    finally:
        ds.close()


def main(
    nc_path: str,
    dset_tag: str,
    days=(0, 3),
    center_flag: str = "czeta0km_positivemean",
    tag: str = "inflow_daily",  # inflow_daily | inflow_snapshot
    iswhite: bool = True,
    include=None,
    exclude=None,
    regex=None,
) -> None:
    if tag not in METHOD_BY_TAG:
        raise ValueError(f"tag must be one of {list(METHOD_BY_TAG)}, got {tag!r}")
    if dset_tag not in ("ctrl", "exp", "exp_ori"):
        raise ValueError(f"dset_tag must be 'ctrl', 'exp', or 'exp_ori', got {dset_tag!r}")
    if dset_tag == "ctrl" and (include is not None or exclude or regex is not None):
        raise ValueError(
            "include/exclude/regex are only supported for EXP-style datasets"
        )

    method = METHOD_BY_TAG[tag]
    if iswhite:
        figroot = os.path.join(f"./{center_flag}_sap_white", tag)
    else:
        figroot = os.path.join(f"./{center_flag}_sap", tag)
    figdir = os.path.join(figroot, dset_tag)
    os.makedirs(figdir, exist_ok=True)

    udraw.set_figure_defalut()
    if not iswhite:
        udraw.set_black_background()

    if dset_tag == "ctrl":
        plot_ctrl_dataset(
            nc_path=nc_path,
            days=days,
            method=method,
            figdir=figdir,
        )
    else:
        plot_exp_dataset(
            nc_path=nc_path,
            days=days,
            method=method,
            figdir=figdir,
            dataset_label=dset_tag,
            include=include,
            exclude=exclude,
            regex=regex,
        )


if __name__ == "__main__":
    center_flag = "czeta0km_positivemean"
    tag = "inflow_daily"  # inflow_daily | inflow_snapshot
    iswhite = True
    days = (0, 3)
    datdir = os.path.join(config.dataPath, "axisy_lowlevel", center_flag)

    main(
        nc_path=os.path.join(datdir, "axisy_ctrl_daily_profiles.nc"),
        dset_tag="ctrl",
        days=days,
        center_flag=center_flag,
        tag=tag,
        iswhite=iswhite,
    )
    main(
        nc_path=os.path.join(datdir, "axisy_exp_daily_profiles.nc"),
        dset_tag="exp",
        days=days,
        center_flag=center_flag,
        tag=tag,
        iswhite=iswhite,
    )
    # main(
    #     nc_path=os.path.join(datdir, "axisy_exp_daily_profiles_origin.nc"),
    #     dset_tag="exp_ori",
    #     days=days,
    #     center_flag=center_flag,
    #     tag=tag,
    #     iswhite=iswhite,
    # )
