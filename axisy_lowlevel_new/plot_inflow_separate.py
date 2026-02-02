# plot_inflow_separate.py
"""
Reproduce the plot types from draw_line_inflow_separate.py
but read from axisy_daily_profiles.nc (self-describing output).

Outputs:
  ./{center_flag}_sap_white/{tag}/
or
  ./{center_flag}_sap/{tag}/
"""

from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

sys.path.insert(1, "../")
import config  # noqa: E402

import util_draw as udraw  # noqa: E402
from plot_io import format_rday, load_axisy_daily_profiles, select_experiments, to_vtype_radius  # noqa: E402


def main(
    center_flag: str = "czeta0km_positivemean",
    tag: str = "inflow_daily",   # inflow_daily | inflow_snapshot
    iswhite: bool = True,
    include=None,
    exclude=None,
    regex=None,
):
    datdir = os.path.join(config.dataPath, "axisy_lowlevel", center_flag)
    nc_path = os.path.join(datdir, "axisy_daily_profiles.nc")
    ds = load_axisy_daily_profiles(nc_path)
    ds = select_experiments(ds, include=include, exclude=exclude, regex=regex)

    method_dict = {
        "inflow_daily": {
            "method": "daily",
            "ur_text": "{txtstr}-{rday} day",
        },
        "inflow_snapshot": {
            "method": "instant",
            "ur_text": "{rday} day (snapshot)",
        },
    }
    mdict = method_dict[tag]
    method = mdict["method"]
    print('method:', method)

    # output dir (match old naming)
    if iswhite:
        figdir = f"./{center_flag}_sap_white/{tag}/"
    else:
        figdir = f"./{center_flag}_sap/{tag}/"
    os.makedirs(figdir, exist_ok=True)

    udraw.set_figure_defalut()
    if not iswhite:
        udraw.set_black_background()

    exp0_label = config.expdict[config.expList[0]]

    # Loop experiments except exp[0] (CTRL) to match old behavior
    exp_vals = ds["exp"].values.tolist()
    for exp in exp_vals[1:]:
        rday = float(ds["restart_day"].sel(exp=exp).values)
        rday_str = format_rday(rday)
        txtstr = f"{int(rday-1)}" if rday > 1 else "0"
        title_init = mdict["ur_text"].format(txtstr=txtstr, rday=rday_str)

        radius_km = ds["radius_km"].values

        # INIT panel (from CTRL window but stored per-exp in output)
        tw_init = to_vtype_radius(ds["tang_wind_lower"].sel({"period": "init", "method": method, "exp": exp}))
        rw_init = to_vtype_radius(ds["radi_wind_lower"].sel({"period": "init", "method": method, "exp": exp}))

        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_axes([0.05, 0.15, 0.9, 0.7])
        udraw.draw_pannel(ax, radius_km, tw_init, rw_init)
        plt.title(title_init, loc="right", fontweight="bold")
        plt.title("    " + exp0_label, loc="left", fontweight="bold")
        plt.savefig(f"{figdir}/{exp0_label}_{rday_str}dy.png", dpi=200)
        plt.close(fig)

        # LAST panel (+48~+72 hrs)
        tw_last = to_vtype_radius(ds["tang_wind_lower"].sel({"period": "last", "method": method, "exp": exp}))
        rw_last = to_vtype_radius(ds["radi_wind_lower"].sel({"period": "last", "method": method, "exp": exp}))

        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_axes([0.05, 0.15, 0.9, 0.7])
        udraw.draw_pannel(ax, radius_km, tw_last, rw_last)
        plt.title("+48 ~ +72 hrs", loc="right", fontweight="bold")
        plt.title(f"    {config.expdict.get(exp, exp)}", loc="left", fontweight="bold")
        plt.savefig(f"{figdir}/{exp}_3dy.png", dpi=200)
        plt.close(fig)

        print("[saved]", exp)


if __name__ == "__main__":
    main()
