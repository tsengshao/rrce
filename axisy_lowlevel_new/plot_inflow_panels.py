# plot_inflow_panels.py
"""
Reproduce the *two-panel* overlays from draw_line_inflow.py (top:init, bottom:last),
but read from axisy_daily_profiles.nc.

Outputs:
  ./{center_flag}_white/{tag}/
or
  ./{center_flag}/{tag}/
"""

from __future__ import annotations

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

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
            "ur_text": "{exp0} {txtstr}-{rday} day",
            "scatter_x_label": "restart day average",
        },
        "inflow_snapshot": {
            "method": "instant",
            "ur_text": "{exp0} {rday} day (snapshot)",
            "scatter_x_label": "restart day snapshot",
        },
    }
    mdict = method_dict[tag]
    method = mdict["method"]

    if iswhite:
        figdir = f"./{center_flag}_white/{tag}/"
    else:
        figdir = f"./{center_flag}/{tag}/"
    os.makedirs(figdir, exist_ok=True)

    udraw.set_figure_defalut()
    if not iswhite:
        udraw.set_black_background()

    exp0_label = config.expdict[config.expList[0]]
    radius_km = ds["radius_km"].values

    exp_vals = ds["exp"].values.tolist()
    for exp in exp_vals[1:]:
        rday = float(ds["restart_day"].sel(exp=exp).values)
        rday_str = format_rday(rday)
        txtstr = f"{int(rday-1)}" if rday > 1 else "0"

        fig, axs = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        plt.subplots_adjust(left=0.1)

        # top init
        tw_init = to_vtype_radius(ds["tang_wind_lower"].sel({"period": "init", "method": method, "exp": exp}))
        rw_init = to_vtype_radius(ds["radi_wind_lower"].sel({"period": "init", "method": method, "exp": exp}))
        udraw.draw_pannel(axs[0], radius_km, tw_init, rw_init)
        axs[0].set_title(f"{config.expdict.get(exp, exp)}", loc="left", fontweight="bold")
        axs[0].text(
            0.98,
            0.93,
            mdict["ur_text"].format(exp0=exp0_label, txtstr=txtstr, rday=rday_str),
            ha="right",
            va="top",
            transform=axs[0].transAxes,
        )

        # bottom last
        tw_last = to_vtype_radius(ds["tang_wind_lower"].sel({"period": "last", "method": method, "exp": exp}))
        rw_last = to_vtype_radius(ds["radi_wind_lower"].sel({"period": "last", "method": method, "exp": exp}))
        udraw.draw_pannel(axs[1], radius_km, tw_last, rw_last)
        axs[1].text(
            0.98,
            0.93,
            "+48 ~ +72 hrs (avg)",
            ha="right",
            va="top",
            transform=axs[1].transAxes,
        )

        fig.text(0.96, 0.5, "tang_wind [m/s]", va="center", color="#E25508", fontweight="bold", rotation="vertical")
        fig.text(0.03, 0.5, "radi_wind [m/s]", va="center", color="#7262AC", fontweight="bold", rotation="vertical")

        plt.savefig(f"{figdir}/{exp}.png", dpi=200)
        plt.close(fig)
        print("[saved]", exp)


if __name__ == "__main__":
    main()
