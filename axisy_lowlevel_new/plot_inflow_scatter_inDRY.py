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

Data source: axisy_daily_profiles.nc (produced by cal_axisy_daily.py)
"""

from __future__ import annotations

import os
import sys

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter
from scipy import stats

sys.path.insert(1, "../")
import config  # noqa: E402

import util_draw as udraw  # noqa: E402
from plot_io import load_axisy_daily_profiles, select_experiments  # noqa: E402


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
    cmap.set_over(lt.cm.Purples(0.7))

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
    iswhite: bool = True,
    include=None,
    exclude=None,
    regex=None,
    special_x_exps=None,  # list[str]: marker "X"
    special_o_exps=None,  # list[str]: hollow marker "o"
):
    datdir = os.path.join(config.dataPath, "axisy_lowlevel", center_flag)
    nc_path = os.path.join(datdir, "axisy_daily_profiles.nc")
    ds = load_axisy_daily_profiles(nc_path)
    ds = select_experiments(ds, include=include, exclude=exclude, regex=regex)

    # Match your original "tag -> method" design
    method_dict = {
        "inflow_daily": {"method": "daily", "scatter_x_label": "restart day average"},
        "inflow_snapshot": {"method": "instant", "scatter_x_label": "restart day snapshot"},
    }
    mdict = method_dict[tag]
    method = mdict["method"]

    # Match old behavior: ignore exp[0] (CTRL) for scatter
    exp_vals = ds["exp"].values.tolist()
    if len(exp_vals) >= 2:
        exp_vals = exp_vals[1:]
        ds = ds.sel(exp=exp_vals)

    # Special marker sets
    special_x_exps = set(special_x_exps or [])
    special_o_exps = set(special_o_exps or [])

    exp_arr = ds["exp"].values.astype("U")
    is_x = np.array([e in special_x_exps for e in exp_arr], dtype=bool)
    is_o = np.array([e in special_o_exps for e in exp_arr], dtype=bool)

    # If overlap, let hollow circle win (can change if you want)
    is_x = is_x & (~is_o)
    is_normal = ~(is_x | is_o)

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
    #tick_vals, bounds, cmap, norm = create_cmap_segmented()
    # -- for DRYFAC colormap
    tick_vals, bounds, cmap, norm = create_cmap_segmented_dryfrac()

    # --- data vectors (keep original definitions) ---
    # Use dict-style indexing to avoid xarray .sel(method=...) conflict
    rw_init = ds["radi_wind_lower"].sel({"period": "init", "method": method, "vtype": "mean"}).values  # (exp, radius)
    tw_last = ds["tang_wind_lower"].sel({"period": "last", "method": method, "vtype": "mean"}).values  # (exp, radius)

    # Keep original: x = min(rw_init), y = max(tw_last)
    x_data = np.nanmin(rw_init, axis=1)
    y_data = np.nanmax(tw_last, axis=1)

    # Color: restart_day
    c_data = ds["restart_day"].values.astype(float)
    # Color: dry_fraction
    c_data = ds["dry_fraction"].sel({"period": "init", "method": method}).values  # (exp, radius)
    face_colors = cmap(norm(c_data))
    edge_colors = [
        (r * 0.7, g * 0.7, b * 0.7, 1.0) 
        for r, g, b, a in face_colors
    ]
    edge_colors = np.array(edge_colors)

    # --- figure layout (keep original) ---
    fig = plt.figure(figsize=(10*1.2, 8*1.2))
    ax = fig.add_axes([0.15, 0.15, 0.72, 0.75])
    cax = fig.add_axes([0.89, 0.15, 0.03, 0.7])

    # Regression (keep original: fit only <= 25)
    idx_fit = ds["restart_day"].values.astype(float) <= 25
    if np.count_nonzero(idx_fit) >= 2:
        res = stats.linregress(x_data[idx_fit], y_data[idx_fit])
        x = np.arange(-10, 10)
        ax.plot(x, res.intercept + res.slope * x, "k", lw=1)

    # --- scatter points (keep style, add two special markers) ---
    # Normal filled points
    if np.any(is_normal):
        ax.scatter(
            x_data[is_normal],
            y_data[is_normal],
            s=500,
            c=face_colors[is_normal],
            edgecolors=edge_colors[is_normal], 
            # c=c_data[is_normal],
            # norm=norm,
            # cmap=cmap,
            zorder=10,
        )

    # X markers (filled)
    if np.any(is_x):
        ax.scatter(
            x_data[is_x],
            y_data[is_x],
            s=500,
            c=face_colors[is_x],
            edgecolors=edge_colors[is_x], 
            # c=c_data[is_x],
            # norm=norm,
            # cmap=cmap,
            zorder=11,
            marker="X",
        )

    # Hollow circle markers (edge colored by cmap)
    if np.any(is_o):
        edge_rgba = cmap(norm(c_data[is_o]))
        ax.scatter(
            x_data[is_o],
            y_data[is_o],
            s=550,
            facecolors="none",
            #edgecolors=edge_rgba,
            edgecolors=['k'],
            linewidths=1,
            zorder=9,
            marker="o",
        )

    # --- colorbar (keep placement/title/ticks style, only change mapping) ---
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])

    cbar = fig.colorbar(
        sm,
        cax=cax,
        orientation="vertical",
        extend="max",
        boundaries=bounds,
    )

    # -- for Dxx_on colormap
    ##  # Put tick marks at bin centers, show labels only for selected ticks
    ##  centers = 0.5 * (bounds[:-1] + bounds[1:])
    ##  label_set = {0, 10, 15, 20, 25, 30}
    ##  labels = [str(int(t)) if int(t) in label_set else "" for t in tick_vals]

    ##  cbar.ax.yaxis.set_major_locator(FixedLocator(centers))
    ##  cbar.ax.yaxis.set_major_formatter(FixedFormatter(labels))
    ##  cbar.ax.minorticks_off()
    ##  cbar.ax.tick_params(width=2.2, length=7, direction="out")
    ## 
    ##  # Keep original title style
    ##  cbar.ax.set_title("D" + r"$xx$" + "_on", loc="left", fontsize=20, pad=13)

    # -- for Dxx_on colormap
    cbar.ax.set_title('dry\nfraction\nin CTRL', loc="left", fontsize=20, pad=13)

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
    ax.set_xlabel(r"$\mathbf{daily}\mathit{-}\mathbf{mean\ inflow\ intensity}$" + " [m/s]\nfrom CTRL to initiate vortex")
    ax.set_ylabel(r"$\mathbf{vortex\ intensity}$"+" [m/s]\nin Dxx_on after 3 days")

    # -- for Dxx_on colormap
    outpng = f"{figdir}/scatter_max_radi_inDXX.png"
    # -- for DRYFAC colormap
    outpng = f"{figdir}/scatter_max_radi_inDRY.png"
    plt.savefig(outpng, dpi=200)
    print("[saved]", outpng)
    #plt.show()
    plt.close(fig)


if __name__ == "__main__":
    # Example usage; add experiment names as needed
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
