#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import sys

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter

sys.path.insert(1, "../")
import config  # noqa: E402

import util_draw as udraw  # noqa: E402
from plot_io import load_axisy_daily_profiles, select_experiments  # noqa: E402


def create_cmap_segmented():
    tick_vals = np.array(
        "0 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30".split(),
        dtype=float,
    )
    bounds = np.r_[tick_vals - 0.5, 30.5]

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

def radius_km_to_size(r_km, r0, r1, s_min=100.0, s_max=1000.0):
    r_km = np.asarray(r_km, dtype=float)
    if not np.isfinite(r0) or not np.isfinite(r1) or r1 <= r0:
        return np.full_like(r_km, 300.0, dtype=float)
    #return s_min + (r_km - r0) * (s_max - s_min) / (r1 - r0)
    # inverse mapping: smaller r -> larger s
    return s_max - (r_km - r0) * (s_max - s_min) / (r1 - r0)

def main(
    center_flag: str = "czeta0km_positivemean",
    tag: str = "inflow_daily",
    iswhite: bool = True,
    include=None,
    exclude=None,
    regex=None,
    special_x_exps=None,
    special_o_exps=None,
):
    datdir = os.path.join(config.dataPath, "axisy_lowlevel", center_flag)
    nc_path = os.path.join(datdir, "axisy_daily_profiles.nc")
    ds = load_axisy_daily_profiles(nc_path)
    ds = select_experiments(ds, include=include, exclude=exclude, regex=regex)

    method_dict = {
        "inflow_daily": {"method": "daily", "scatter_x_label": "restart day average"},
        "inflow_snapshot": {"method": "instant", "scatter_x_label": "restart day snapshot"},
    }
    mdict = method_dict[tag]
    method = mdict["method"]

    # ignore CTRL for scatter (keep your current behavior)
    exp_vals = ds["exp"].values.tolist()
    if len(exp_vals) >= 2:
        exp_vals = exp_vals[1:]
        ds = ds.sel(exp=exp_vals)

    special_x_exps = set(special_x_exps or [])
    special_o_exps = set(special_o_exps or [])

    exp_arr = ds["exp"].values.astype("U")
    is_x = np.array([e in special_x_exps for e in exp_arr], dtype=bool)
    is_o = np.array([e in special_o_exps for e in exp_arr], dtype=bool)
    is_x = is_x & (~is_o)
    is_normal = ~(is_x | is_o)

    if iswhite:
        figdir = f"./{center_flag}_white/{tag}/"
    else:
        figdir = f"./{center_flag}/{tag}/"
    os.makedirs(figdir, exist_ok=True)

    udraw.set_figure_defalut()
    if not iswhite:
        udraw.set_black_background()

    tick_vals, bounds, cmap, norm = create_cmap_segmented()

    if "dry_fraction" not in ds.variables:
        raise ValueError("dry_fraction not found. Re-run cal_axisy_daily.py to add it.")

    # X axis: dry fraction (init)
    x_data = ds["dry_fraction"].sel({"period": "init", "method": method}).values.astype(float)

    # Y axis: max inflow strength from radi_wind_lower (init)
    rw_init = ds["radi_wind_lower"].sel({"period": "init", "method": method, "vtype": "mean"}).values
    rw_init = np.asarray(rw_init, dtype=float)  # (exp, radius)

    y_data = np.nanmin(rw_init, axis=1)  # radial wind, minus is inflow

    # marker size: radius where inflow is strongest
    radius_km = ds["radius_km"].values.astype(float)
    idx_min = np.nanargmin(rw_init, axis=1)
    r_at_max = radius_km[idx_min]  # km
    idx_00dy = np.where(np.isin(exp_vals, 'RRCE_3km_f10'))[0]
    r_at_max[idx_00dy] = radius_km.max() #set initial to maximum of radius
    print(r_at_max)

    r0 = np.nanmin(r_at_max)
    r1 = np.nanmax(r_at_max)
    s_data = radius_km_to_size(r_at_max, r0, r1, s_min=100.0, s_max=1000.0)

    # Color: restart_day (keep same)
    c_data = ds["restart_day"].values.astype(float)

    # figure layout (keep same)
    fig = plt.figure(figsize=(10*1.2, 8*1.2))
    ax = fig.add_axes([0.15, 0.15, 0.72, 0.75])
    cax = fig.add_axes([0.89, 0.15, 0.03, 0.7])

    # scatter
    if np.any(is_normal):
        ax.scatter(
            x_data[is_normal],
            y_data[is_normal],
            s=s_data[is_normal],
            c=c_data[is_normal],
            norm=norm,
            cmap=cmap,
            zorder=10,
        )

    if np.any(is_x):
        ax.scatter(
            x_data[is_x],
            y_data[is_x],
            s=s_data[is_x],
            c=c_data[is_x],
            norm=norm,
            cmap=cmap,
            zorder=11,
            marker="X",
        )

    if np.any(is_o):
        edge_rgba = cmap(norm(c_data[is_o]))
        ax.scatter(
            x_data[is_o],
            y_data[is_o],
            s=s_data[is_o],
            facecolors="none",
            #edgecolors=edge_rgba,
            edgecolors=['k'],
            linewidths=1.0,
            zorder=12,
            marker="o",
        )

    # colorbar (keep same)
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = fig.colorbar(
        sm,
        cax=cax,
        orientation="vertical",
        extend="neither",
        boundaries=bounds,
    )

    centers = 0.5 * (bounds[:-1] + bounds[1:])
    label_set = {0, 10, 15, 20, 25, 30}
    labels = [str(int(t)) if int(t) in label_set else "" for t in tick_vals]

    cbar.ax.yaxis.set_major_locator(FixedLocator(centers))
    cbar.ax.yaxis.set_major_formatter(FixedFormatter(labels))
    cbar.ax.minorticks_off()
    cbar.ax.tick_params(width=2.2, length=7, direction="out")
    #cbar.ax.set_title("D" + r"$xx$" + "_on", loc="left", fontsize=20, pad=13)
    cbar.ax.set_title("Restart\nDay", loc="left", fontsize=20, pad=13, ha='left')

    # ---- size legend (upper-left) ----
    # Pick a few representative radii (km) to show in legend.
    # You can change these values to match your science context.
    legend_r_km = np.array([5.0, 10.0, 20.0, 30.0], dtype=float)
    legend_r_km = np.array([200, 300, 400, 500], dtype=float)
    
    # Clip to available range so legend makes sense for this run
    legend_r_km = legend_r_km[(legend_r_km >= r0) & (legend_r_km <= r1)]
    if legend_r_km.size == 0:
        legend_r_km = np.array([r0, 0.5 * (r0 + r1), r1], dtype=float)
    
    legend_sizes = radius_km_to_size(legend_r_km, r0, r1, s_min=100.0, s_max=1000.0)
    
    handles = []
    labels = []
    for rr, ss in zip(legend_r_km, legend_sizes):
        h = ax.scatter([], [], s=ss, facecolors="none", edgecolors="k", linewidths=1.0)
        handles.append(h)
        labels.append(f"{rr:g} km")
    
    leg = ax.legend(
        handles,
        labels,
        title="R at max inflow",
        loc="upper left",
        frameon=True,
        borderpad=0.6,
        labelspacing=0.6,
        handletextpad=0.8,
    )
    leg._legend_box.align = "left"

    # --- axes settings (keep original) ---
    ax.set_xticks(np.arange(0, 0.71, 0.1))
    ax.set_yticks(np.arange(-3, 0.01, 0.5))
    #ax.set_xlim(0, 0.72)
    ax.set_ylim(0.1, -3)
    ax.grid(True)
    ax.set_xlabel(f"dry fraction (CWV < 30mm)\n{mdict['scatter_x_label']}")
    ax.set_ylabel(f"minimum radial wind\n{mdict['scatter_x_label']} [m/s]")

    outpng = f"{figdir}/scatter_dryfrac_vs_inflow_sizeby_r.png"
    plt.savefig(outpng, dpi=200)
    plt.close(fig)
    print("[saved]", outpng)


if __name__ == "__main__":
    main(
        exclude=[
            "RRCE_3km_f00_halfwind_30",
        ],
        special_x_exps=[
            "RRCE_3km_f00_30p27",
        ],
        special_o_exps=[
            "RRCE_3km_f00_14p972",
            "RRCE_3km_f00_14p986",
            "RRCE_3km_f00_15p014",
            "RRCE_3km_f00_15p028",
            "RRCE_3km_f00_19p972",
            "RRCE_3km_f00_19p986",
            "RRCE_3km_f00_20p014",
            "RRCE_3km_f00_20p028",
            "RRCE_3km_f00_24p972",
            "RRCE_3km_f00_24p986",
            "RRCE_3km_f00_25p014",
            "RRCE_3km_f00_25p028",
            "RRCE_3km_f00_29p972",
            "RRCE_3km_f00_29p986",
            "RRCE_3km_f00_30p014",
            "RRCE_3km_f00_30p028",
        ],
    )
