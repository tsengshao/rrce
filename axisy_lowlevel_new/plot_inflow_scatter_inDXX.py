#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
plot_inflow_scatter.py

Keep original plotting style (layout/ticks/limits/grid/regression/colorbar style),
but:
1) Use segmented discrete colormap so values within (N-0.5, N+0.5) share same color.
   e.g., 14.99, 15.00, 15.01 -> same color bin centered at 15.
2) Support two special markers:
   - X markers for special_x_exps
   - hollow circle markers for special_o_exps

Data sources:
- x axis: axisy_ctrl_daily_profiles.nc (produced by cal_axisy_ctrl_daily.py)
- y axis/color: one or more case-aligned NetCDF files, default axisy_exp_daily_profiles.nc
"""

from __future__ import annotations

import os
import sys

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter
from scipy import stats
import xarray as xr

sys.path.insert(1, "../")
import config  # noqa: E402

import util_draw as udraw  # noqa: E402
from plot_io import (  # noqa: E402
    as_path_list,
    ctrl_data_for_exps,
    select_existing_exps,
    source_markers,
    source_names,
    y_tang_wind_profile_for_source,
)


CTRL_DAILY_FILENAME = "axisy_ctrl_daily_profiles.nc"
EXP_DAILY_FILENAME = "axisy_exp_daily_profiles.nc"


def create_cmap_segmented():
    """
    Discrete bins centered on integer ticks.
    - tick_vals: values we want to represent as category centers
    - bounds: bin edges, tick_vals - 0.5 plus a final 30.5 edge
    """
    # Do NOT include 31 in ticks
    tick_vals = np.array(
        "0 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30".split(),
        dtype=float,
    )

    # Bin edges: center +/- 0.5; last edge 30.5
    bounds = np.r_[tick_vals - 0.5, 30.5]

    # Keep your original segmented palette logic
    newcolors = np.vstack(
        (
            [[0.9, 0.9, 0.9, 1.0]],
            #[[0.5, 0.5, 0.5, 1.0]],
            plt.cm.binary(np.linspace(0.3, 0.7, 5)),
            plt.cm.Greens(np.linspace(0.2, 0.9, 5)),
            plt.cm.Oranges(np.linspace(0.2, 0.9, 5)),
            plt.cm.Blues(np.linspace(0.2, 0.9, 5)),
            np.atleast_2d(plt.cm.Purples(0.7)),
        )
    )

    cmap = mpl.colors.ListedColormap(newcolors, name="SegmentedCmap")
    cmap.set_under((0.7, 0.7, 0.7))
    cmap.set_over(plt.cm.Purples(0.7))

    norm = mpl.colors.BoundaryNorm(bounds, cmap.N, clip=False)
    return tick_vals, bounds, cmap, norm

def create_cmap_segmented_dryfrac():
    bounds = np.arange(0.0, 0.61, 0.1)
    tick_vals = bounds.copy()

    colors = ['#FDB164', '#FEEBA1', '#7DBF78', '#4464A6']
    nodes = np.linspace(0, 1, len(colors))
    cmap_raw = mpl.colors.LinearSegmentedColormap.from_list("mycmap", list(zip(nodes, colors)))
    cmap = cmap_raw


    # # Keep your original segmented palette logic
    # newcolors = np.vstack(
    #     (   
    #         [[0.9, 0.9, 0.9, 1.0]],
    #         plt.cm.binary(np.linspace(0.3, 0.7, 2)),
    #         plt.cm.Greens(np.linspace(0.2, 0.9, 2)),
    #         plt.cm.Oranges(np.linspace(0.2, 0.9, 2)),
    #     )
    # )
    # cmap = mpl.colors.ListedColormap(newcolors, name="SegmentedCmap")
    # cmap.set_under((0.2, 0.2, 0.2))
    cmap.set_over('#A84D8F')

    norm = mpl.colors.BoundaryNorm(bounds, cmap.N, clip=False)
    return tick_vals, bounds, cmap, norm

def main(
    center_flag: str = "czeta0km_positivemean",
    tag: str = "inflow_daily",  # inflow_daily | inflow_snapshot
    ctrl_nc_path: str | None = None,
    y_nc_path: str | None = None,
    y_nc_paths=None,
    y_source_names=None,
    y_markers=None,
    y_day: int = 3,
    iswhite: bool = True,
    include=None,
    exclude=None,
    regex=None,
    special_x_exps=None,  # list[str]: marker "X"
    special_o_exps=None,  # list[str]: hollow marker "o"
):
    datdir = os.path.join(config.dataPath, "axisy_lowlevel", center_flag)
    default_ctrl_nc_path = os.path.join(datdir, CTRL_DAILY_FILENAME)
    default_y_nc_path = os.path.join(datdir, EXP_DAILY_FILENAME)

    if ctrl_nc_path is None:
        ctrl_nc_path = default_ctrl_nc_path
    if y_nc_paths is None:
        y_nc_paths = [default_y_nc_path if y_nc_path is None else y_nc_path]
    else:
        y_nc_paths = as_path_list(y_nc_paths)
        if y_nc_path is not None:
            y_nc_paths = [y_nc_path] + y_nc_paths
    y_source_names = source_names(y_nc_paths, y_source_names)
    y_markers = source_markers(len(y_nc_paths), y_markers)

    ctrl_ds = xr.open_dataset(ctrl_nc_path)

    # Match your original "tag -> method" design
    method_dict = {
        "inflow_daily": {"method": "daily", "scatter_x_label": "restart day average"},
        "inflow_snapshot": {"method": "instant", "scatter_x_label": "restart day snapshot"},
    }
    mdict = method_dict[tag]
    method = mdict["method"]

    # Special marker sets
    special_x_exps = set(special_x_exps or [])
    special_o_exps = set(special_o_exps or [])

    # Output directory (keep original style)
    if iswhite:
        figdir = f"./{center_flag}_white/{tag}/"
    else:
        figdir = f"./{center_flag}/{tag}/"
    os.makedirs(figdir, exist_ok=True)

    udraw.set_figure_defalut()
    if not iswhite:
        udraw.set_black_background()

    # Segmented cmap/norm (your requested behavior)
    # -- for Dxx_on colormap
    tick_vals, bounds, cmap, norm = create_cmap_segmented()
    # -- for DRYFAC colormap
    # tick_vals, bounds, cmap, norm = create_cmap_segmented_dryfrac()

    plot_groups = []
    for y_path, source_name, source_marker in zip(y_nc_paths, y_source_names, y_markers):
        ds = xr.open_dataset(y_path)
        ds = select_existing_exps(ds, include=include, exclude=exclude, regex=regex)
        exp_vals = [str(exp) for exp in ds["exp"].values.tolist()]
        if not exp_vals:
            print(f"[skip source] {source_name}: no experiments after filtering")
            continue
        if "ctrl_day" not in ds.coords:
            raise ValueError(f"{source_name}: y nc must contain ctrl_day coordinate for exp -> CTRL day matching")
        if "case_day" not in ds.coords:
            raise ValueError(f"{source_name}: y nc must contain case_day coordinate for Dxx_on coloring")

        ctrl_days = ds["ctrl_day"].sel(exp=exp_vals).values.astype(np.float64)
        case_day = ds["case_day"].sel(exp=exp_vals).values.astype(float)
        x_profile = ctrl_data_for_exps(ctrl_ds, exp_vals, ctrl_days, "radi_wind_lower", method, vtype="mean")
        tw_y = y_tang_wind_profile_for_source(ds, source_name, y_day, method).transpose("exp", "radius_km").values

        x_data = np.nanmin(x_profile.transpose("exp", "radius_km").values, axis=1)
        y_data = np.nanmax(tw_y, axis=1)
        c_data = case_day
        face_colors = cmap(norm(c_data))
        edge_colors = np.array([(r * 0.7, g * 0.7, b * 0.7, 1.0) for r, g, b, a in face_colors])

        plot_groups.append(
            {
                "source": source_name,
                "marker": source_marker,
                "exp": np.asarray(exp_vals, dtype="U"),
                "x": x_data,
                "y": y_data,
                "c": c_data,
                "face_colors": face_colors,
                "edge_colors": edge_colors,
                "case_day": case_day,
            }
        )

    if not plot_groups:
        raise ValueError("No y-axis data remained to plot after filtering.")

    # --- figure layout (keep original) ---
    fig = plt.figure(figsize=(10*1.2, 8*1.2))
    ax = fig.add_axes([0.15, 0.15, 0.72, 0.75])
    cax = fig.add_axes([0.89, 0.15, 0.03, 0.7])

    # Regression (keep original: fit only <= 25)
    first = plot_groups[0]
    idx_fit = first["case_day"] <= 25
    if np.count_nonzero(idx_fit) >= 2:
        res = stats.linregress(first["x"][idx_fit], first["y"][idx_fit])
        x = np.arange(-10, 10)
        ax.plot(x, res.intercept + res.slope * x, "k", lw=1)

    # Source marker is the default. special_o_exps is drawn first so it stays underneath.
    for igroup, group in enumerate(plot_groups):
        exp_arr = group["exp"]
        is_o = np.array([exp in special_o_exps for exp in exp_arr], dtype=bool)
        is_x = np.array([exp in special_x_exps for exp in exp_arr], dtype=bool) & (~is_o)
        is_source = ~(is_o | is_x)

        if np.any(is_o):
            ax.scatter(
                group["x"][is_o],
                group["y"][is_o],
                s=550,
                facecolors="none",
                edgecolors=["k"],
                linewidths=1,
                zorder=5 + igroup,
                marker="o",
            )

        if np.any(is_source):
            ax.scatter(
                group["x"][is_source],
                group["y"][is_source],
                s=500,
                c=group["face_colors"][is_source],
                edgecolors=group["edge_colors"][is_source],
                zorder=10 + igroup,
                marker=group["marker"],
                label=group["source"] if len(plot_groups) > 1 else None,
            )

        if np.any(is_x):
            ax.scatter(
                group["x"][is_x],
                group["y"][is_x],
                s=500,
                c=group["face_colors"][is_x],
                edgecolors=group["edge_colors"][is_x],
                zorder=20 + igroup,
                marker="X",
            )

    # --- colorbar (keep placement/title/ticks style, only change mapping) ---
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])

    cbar = fig.colorbar(
        sm,
        cax=cax,
        orientation="vertical",
        extend="neither",
        boundaries=bounds,
    )

    # -- for Dxx_on colormap
    # Put tick marks at bin centers, show labels only for selected ticks
    centers = 0.5 * (bounds[:-1] + bounds[1:])
    label_set = {0, 10, 15, 20, 25, 30}
    labels = [str(int(t)) if int(t) in label_set else "" for t in tick_vals]

    cbar.ax.yaxis.set_major_locator(FixedLocator(centers))
    cbar.ax.yaxis.set_major_formatter(FixedFormatter(labels))
    cbar.ax.minorticks_off()
    cbar.ax.tick_params(width=2.2, length=7, direction="out")
    
    # Keep original title style
    cbar.ax.set_title("D" + r"$xx$" + "_on", loc="left", fontsize=20, pad=13)

    # -- for Dxx_on colormap
    ## cbar.ax.set_title('dry\nfraction\nin CTRL', loc="left", fontsize=20, pad=13)

    # --- axes settings (keep original) ---
    ax.set_yticks(np.arange(0, 9.01, 1.5))
    ax.set_xticks(np.arange(-3, 0.01, 0.5))
    ax.set_ylim(-0.3, 9)
    ax.set_xlim(0.1, -3)
    ax.grid(True)
    # ax.set_xlabel(f"minimum radial wind\n{mdict['scatter_x_label']} [m/s]")
    # ax.set_ylabel("maximum tangential wind\nlast day average [m/s]")
    ## ax.set_xlabel(f"minimum daily-mean radial wind of the convective cluster\ninitial day in CTRL [m/s]")
    ## ax.set_ylabel("maximum daily-mean tangential wind\nlast day in EXP [m/s]")
    ax.set_xlabel(r"$\mathbf{daily}\mathit{-}\mathbf{mean\ inflow\ intensity}$" + " [m/s]\nfrom shared CTRL day")
    ax.set_ylabel(r"$\mathbf{vortex\ intensity}$"+f" [m/s]\nin EXP day {y_day}")
    if len(plot_groups) > 1:
        ax.legend(loc="best", fontsize=14, frameon=False)

    # -- for Dxx_on colormap
    outpng = f"{figdir}/scatter_max_radi_inDXX.png"
    # -- for DRYFAC colormap
    # outpng = f"{figdir}/scatter_max_radi_inDRY.png"
    plt.savefig(outpng, dpi=200)
    print("[saved]", outpng)
    #plt.show()
    plt.close(fig)


if __name__ == "__main__":
    # Default usage:
    # - x reads axisy_ctrl_daily_profiles.nc
    # - y/color reads axisy_exp_daily_profiles.nc
    #
    # Multiple y nc files:
    # main(
    #     y_nc_paths=[
    #         "/path/to/axisy_exp_daily_profiles.nc",
    #         "/path/to/axisy_exp_daily_profiles_newrun.nc",
    #     ],
    #     y_source_names=["base", "newrun"],
    #     y_markers=["o", "^"],  # source markers: circle, triangle; "x" also works
    # )
    main(
        exclude=[
            'RRCE_3km_f00_halfwind_30',
        ],
        special_x_exps=[
            'RRCE_3km_f00_30p27',
            #'RRCE_3km_f00_halfwind_30',
        ],
        special_o_exps=[
            #20
            'RRCE_3km_f00_14p972',
            'RRCE_3km_f00_14p986',
            'RRCE_3km_f00_15p014',
            'RRCE_3km_f00_15p028',
            'RRCE_3km_f00_19p972',
            #25
            'RRCE_3km_f00_19p986',
            'RRCE_3km_f00_20p014',
            'RRCE_3km_f00_20p028',
            'RRCE_3km_f00_24p972',
            'RRCE_3km_f00_24p986',
            #30
            'RRCE_3km_f00_25p014',
            'RRCE_3km_f00_25p028',
            'RRCE_3km_f00_29p972',
            'RRCE_3km_f00_29p986',
            'RRCE_3km_f00_30p014',
            #35
            'RRCE_3km_f00_30p028',
        ],
    )
