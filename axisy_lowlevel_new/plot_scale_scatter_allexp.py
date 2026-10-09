#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Compare experimental groups against the shared paper/origin reference.

Examples (run separately to produce individual figures):
    python plot_scale_scatter_allexp.py --group radiation
    python plot_scale_scatter_allexp.py --group coriolis
    python plot_scale_scatter_allexp.py --group evolution
With no arguments, all configured groups are produced.

Origin uses gray circles and gray X markers; each overlay uses a single color.
Scatter opacity is configurable per source. Hollow circles retain their black
outlines. No regression line is drawn.
The x axis uses CSV scale_6sigma_km / 2 at the initial ctrl_day, with linear
interpolation by default and endpoint bounds outside the valid time range.
Thermal-wind references use small filled black dots and integer days only.
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import os
import sys

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import xarray as xr

sys.path.insert(1, "../")
import config  # noqa: E402

import util_draw as udraw  # noqa: E402
from plot_io import (  # noqa: E402
    as_path_list,
    ctrl_data_for_exps,
    match_existing_days,
    select_existing_exps,
    source_markers,
    source_names,
    y_tang_wind_profile_for_source,
)

from plot_scale_io import (  # noqa: E402
    DEFAULT_SCALE_CSV_PATH,
    load_scale_csv,
    scale_radius_for_days,
)


CTRL_DAILY_FILENAME = "axisy_ctrl_daily_profiles.nc"
EXP_DAILY_FILENAME = "axisy_exp_daily_profiles.nc"

# ===== 常用設定：新增實驗只需修改這一區 =====
DEFAULT_CENTER_FLAG = "czeta0km_positivemean"
DEFAULT_Y_DAY = 3
DEFAULT_SCATTER_ALPHA = 0.9 # 0=完全透明，1=不透明；各組可用 alpha 個別覆寫。
DEFAULT_EDGE_LINEWIDTH = 0.0  # 散點邊框粗細，單位 points。
DEFAULT_MARKER_SIZE = 500  # 散點面積（points²），數值越大符號越大。
CORIOLIS_HOLLOW = True  # f20/f60 共用開關：True=空心，False=實心。

# 每張圖會自動加入 origin；圓點和 X 都用此 color。
ORIGIN_SOURCE = {
    "filename": "axisy_exp_daily_profiles_origin.nc",
    "day_flag": 3,
    "label": "f@10 (origin)",
    #"color": "#808080",
    "color": "0.7",
    "marker": "o",
    "size": DEFAULT_MARKER_SIZE,
    "alpha": 1,
    "edgecolor": None,
    "linewidth": 1,
}

# 每筆實驗設定：filename=nc 檔名，label=圖例，color=單色，marker=符號。
# day_flag=從 nc 取 EXP 第幾天；None 跟隨 --y-day（預設 3）。
# wind_source="exp"（預設）取 EXP 風速；"ctrl" 用此 nc 的 restart_day
# （若無則用 case_day）加上 day_flag，讀取 CTRL 對應天數的切向風。
# CTRL 天數必須精確存在，不四捨五入或插值；filename 仍提供實驗清單與日期。
# alpha=透明度（0～1），套用於該來源的所有散點與圖例。
# 修改 DEFAULT_SCATTER_ALPHA 可調整預設值；某筆改成 "alpha": 0.5 可個別調整。
# edgecolor=None 使用原本深色邊框；可改成 "black"、"#555555" 或 "none"（無邊框）。
# linewidth=邊框粗細（points）；0 表示不畫邊框。邊框透明度也使用 alpha。
# hollow=True 使用空心符號（預設 False）；需搭配可見的 edgecolor 和 linewidth。
# size=散點面積（points²）；改 DEFAULT_MARKER_SIZE 可統一調整，也可逐筆設定 "size": 300。
# 要在既有圖疊上新實驗：在該組的 sources 清單內複製一筆 dict 並修改。
# 要新增一張圖：新增 "組名": {"references": True, "sources": [...]}。
# references=True 疊上參考點；False 不讀取參考 nc，也不繪製參考點及其圖例。
# origin 不必重複填入；--group both 會繪製這裡列出的所有組別。
EXPERIMENT_GROUPS = {
    "radiation": {
        "references": False,
        "sources": [
            {
                "filename": "axisy_exp_daily_profiles_f10_FixRad.nc",
                "day_flag": 3,
                "label": "f@10 Fix-Rad",
                "color": "#6988C9",
                "marker": "o",
                "size": DEFAULT_MARKER_SIZE*0.8,
                "alpha": DEFAULT_SCATTER_ALPHA,
                "edgecolor": None,
                "linewidth": DEFAULT_EDGE_LINEWIDTH,
            },
            {
                "filename": "axisy_exp_daily_profiles_f10_HomogRadCTRL.nc",
                "day_flag": 3,
                "label": "f@10 Homog-Rad",
                "color": "#26478C",
                "marker": "o",
                "size": DEFAULT_MARKER_SIZE*0.8,
                "alpha": DEFAULT_SCATTER_ALPHA,
                "edgecolor": None,
                "linewidth": DEFAULT_EDGE_LINEWIDTH,
            },
            # {
            #     "filename": "axisy_exp_daily_profiles_f10_HomogRad.nc",
            #     "day_flag": 3,
            #     "label": "f10 HomogRad",
            #     "color": "#313CA8",
            #     "marker": "o",
            #     "size": DEFAULT_MARKER_SIZE,
            #     "alpha": DEFAULT_SCATTER_ALPHA*0.8,
            #     "edgecolor": None,
            #     "linewidth": DEFAULT_EDGE_LINEWIDTH,
            # },
        ],
    },
    "coriolis": {
        "references": False,
        "sources": [
            {
                "filename": "axisy_exp_daily_profiles_f20.nc",
                "day_flag": 3,
                "label": "f@20",
                "color": "#FCB97E",
                "marker": "^",
                "size": DEFAULT_MARKER_SIZE*0.8,
                "alpha": DEFAULT_SCATTER_ALPHA,
                "edgecolor": None,
                "linewidth": DEFAULT_EDGE_LINEWIDTH,
                "hollow": False,
            },
            {
                "filename": "axisy_exp_daily_profiles_f60.nc",
                "day_flag": 3,
                "label": "f@60",
                "color": "#EB4400",
                "marker": "D",
                "size": DEFAULT_MARKER_SIZE*0.5,
                "alpha": DEFAULT_SCATTER_ALPHA,
                "edgecolor": None,
                "linewidth": DEFAULT_EDGE_LINEWIDTH,
                "hollow": False,
            },
        ],
    },
    "evolution": {
        "references": False,
        "sources": [
            {
                "filename": "axisy_exp_daily_profiles_origin.nc",
                "label": "day-2",
                "day_flag": 2,
                "color": "#480058",
                "marker": "o",
                "size": DEFAULT_MARKER_SIZE*0.5,
                "alpha": DEFAULT_SCATTER_ALPHA,
                "edgecolor": None,
                "linewidth": DEFAULT_EDGE_LINEWIDTH,
            },
            {
                "filename": "axisy_exp_daily_profiles_origin.nc",
                "label": "day-1",
                "day_flag": 1,
                "color": "#275291",
                "marker": "o",
                "size": DEFAULT_MARKER_SIZE*0.5,
                "alpha": DEFAULT_SCATTER_ALPHA,
                "edgecolor": None,
                "linewidth": DEFAULT_EDGE_LINEWIDTH,
            },
            {
                "filename": "axisy_exp_daily_profiles_origin.nc",
                "label": "day-0",
                "day_flag": 0,
                "wind_source": "ctrl",
                "color": "#ADEEC5",
                "marker": "o",
                "size": DEFAULT_MARKER_SIZE*0.5,
                "alpha": DEFAULT_SCATTER_ALPHA,
                "edgecolor": None,
                "linewidth": DEFAULT_EDGE_LINEWIDTH,
            },
        ],
    },
    "basic": {
        "references": True,
        "sources": [
        ],
    },
}

# ===== Thermal-wind 參考點：CTRL 與 EXP day1/2/3，可各自調整檔案與畫法 =====
REFERENCE_DATA_DIR = os.path.join(config.dataPath, "twb")
# filename 可用相對於 REFERENCE_DATA_DIR 的檔名，或完整路徑。
# kind="ctrl": 各 CTRL day 的最大風速；kind="exp": EXP 指定 day 的最大風速。
# x 軸皆取相同初始 CTRL day 對應 CSV scale_6sigma_km / 2（3sigma 半徑）。
# integer_only 依 CTRL day / EXP case_day 篩選，排除小數天 ensemble。
# CTRL day_flag=要取資料的 CTRL 天數清單；None 畫所有整數天。
# EXP day_flag=要取資料的 EXP 天數；None 跟隨 --y-day。
# EXP case_days=要畫哪些重啟案例（case_day）；None 畫所有整數天案例。
# enabled=False 關閉該組；REFERENCE_GROUPS={} 關閉全部參考點。
# color / marker / size / alpha / edgecolor / linewidth / hollow / zorder 可調整畫法。
# label 的 {day} 自動依 EXP day_flag 更新。
# 若 nc 只有單一天數，更改 day_flag 時需將 filename 換成含該天資料的檔案。
# 每組必須使用不同的鍵名（如 exp_day1），避免後面的設定覆蓋前面的設定。
REFERENCE_GROUPS = {
    "ctrl": {
        "kind": "ctrl",
        "filename": "twb_ctrl_lowlevel_daily.nc",
        "variable": "twindd_lower",
        "label": "balance vortex\n(by initial buoyancy)",
        "enabled": True,
        "integer_only": True,
        "day_flag": list(range(10, 31)),
        "color": "black",
        "marker": "o",
        "size": 70,
        "alpha": 1.0,
        "edgecolor": "none",
        "linewidth": 0,
        "hollow": False,
        "zorder": 30,
    },
    # "exp_day1": {
    #     "kind": "exp",
    #     "filename": "twb_exp_lowlevel_day1.nc",
    #     "variable": "twindd_lower",
    #     #"label": "vortex day{day}",
    #     "label": "balance vortex\n(by day{day} buoyancy)",
    #     "day_flag": 1,
    #     "enabled": True,
    #     "integer_only": True,
    #     "case_days": None,
    #     "color": "r",
    #     "marker": "o",
    #     "size": 70,
    #     "alpha": 1.0,
    #     "edgecolor": "none",
    #     "linewidth": 0,
    #     "hollow": False,
    #     "zorder": 31,
    # },
    # "exp_day2": {
    #     "kind": "exp",
    #     "filename": "twb_exp_lowlevel_day2.nc",
    #     "variable": "twindd_lower",
    #     #"label": "vortex day{day}",
    #     "label": "balance vortex\n(by day{day} buoyancy)",
    #     "day_flag": 2,
    #     "enabled": True,
    #     "integer_only": True,
    #     "case_days": None,
    #     "color": "r",
    #     "marker": "o",
    #     "size": 70,
    #     "alpha": 1.0,
    #     "edgecolor": "none",
    #     "linewidth": 0,
    #     "hollow": False,
    #     "zorder": 31,
    # },
    "exp_day3": {
        "kind": "exp",
        "filename": "twb_exp_lowlevel_day3.nc",
        "variable": "twindd_lower",
        #"label": "vortex day{day}",
        "label": "balance vortex\n(by day{day} buoyancy)",
        "day_flag": 3,
        "enabled": True,
        "integer_only": True,
        "case_days": None,
        "color": "r",
        "marker": "o",
        "size": 70,
        "alpha": 1.0,
        "edgecolor": "none",
        "linewidth": 0,
        "hollow": False,
        "zorder": 31,
    },
}
# ===== 常用設定結束 =====


def load_reference_groups(scale_times, scale_radii, reference_groups, reference_data_dir, y_day, scale_matching="linear"):
    """Pair thermal-wind maxima with shared CSV scale radii at initial CTRL days."""
    groups = []
    for name, source in reference_groups.items():
        if not source.get("enabled", True):
            continue
        source = dict(source)
        path = os.path.join(reference_data_dir, source["filename"])
        # Keep coordinates with units="days" numeric, rather than timedeltas.
        with xr.open_dataset(path, decode_timedelta=False) as ds:
            kind = source["kind"]
            if kind == "ctrl":
                sample_dim = "day"
                case_days = np.asarray(ds["day"].values, dtype=float)
                ctrl_days = case_days
                selected_case_days = source.get("day_flag")
            elif kind == "exp":
                day = y_day if source.get("day_flag") is None else source["day_flag"]
                source["label"] = source["label"].format(day=day)
                ds = select_existing_exps(
                    ds, include=source.get("include"), exclude=source.get("exclude"),
                    regex=source.get("regex"),
                )
                matched = match_existing_days(
                    xr.DataArray(np.atleast_1d(ds["day"].values)),
                    np.asarray([day]), source["label"], "reference EXP day"
                )[0]
                if "day" in ds.dims:
                    ds = ds.sel(day=matched)
                sample_dim = "exp"
                case_days = np.asarray(ds["case_day"].values, dtype=float)
                ctrl_days = np.asarray(ds["ctrl_day"].values, dtype=float)
                selected_case_days = source.get("case_days")
            else:
                raise ValueError(f"{name}: reference kind must be 'ctrl' or 'exp'")

            keep = np.isfinite(case_days) & np.isfinite(ctrl_days)
            if source.get("integer_only", True):
                keep &= np.isclose(case_days, np.rint(case_days), rtol=0, atol=1e-9)
            if selected_case_days is not None:
                keep &= np.isin(case_days, selected_case_days)
            ds = ds.isel({sample_dim: np.flatnonzero(keep)})
            if ds.sizes[sample_dim] == 0:
                print(f"[skip reference] {source['label']}: no selected days")
                continue

            x = scale_radius_for_days(
                ctrl_days[keep], scale_times, scale_radii, scale_matching
            )
            y = ds[source.get("variable", "twindd_lower")].max(
                dim="radius_km", skipna=True
            ).transpose(sample_dim).values
            valid = np.isfinite(x) & np.isfinite(y)
            groups.append({"style": source, "x": x[valid], "y": y[valid]})
            print(f"[reference] {source['label']}: {np.count_nonzero(valid)} points")
    return groups


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
    center_flag: str = DEFAULT_CENTER_FLAG,
    tag: str = "inflow_daily",  # inflow_daily | inflow_snapshot
    ctrl_nc_path: str | None = None,
    y_nc_path: str | None = None,
    y_nc_paths=None,
    y_source_names=None,
    y_markers=None,
    y_day: int = DEFAULT_Y_DAY,
    iswhite: bool = True,
    include=None,
    exclude=None,
    regex=None,
    special_x_exps=None,  # list[str]: marker "X"
    special_o_exps=None,  # list[str]: hollow marker "o"
    figname='scatter_max_scale_inDXX.png',
    y_colors=None,  # one color per source; None entries retain Dxx_on coloring
    special_marker_sources=None,  # source names; None applies to all sources
    output_dir=None,
    y_alphas=None,  # one opacity (0 to 1) per source, including special markers
    y_edgecolors=None,  # None entries retain the original darker outlines
    y_linewidths=None,  # nonnegative outline width in points per source
    y_hollow=None,  # True draws default source markers without face colors
    y_sizes=None,  # nonnegative marker area in points squared per source
    reference_groups=None,  # None uses REFERENCE_GROUPS; {} disables references
    reference_data_dir=None,
    y_days=None,  # EXP day per source; None entries follow y_day
    y_wind_sources=None,  # "exp" profiles or "ctrl" at restart_day + source day
    scale_csv_path=DEFAULT_SCALE_CSV_PATH,
    scale_matching="linear",  # linear | nearest; outside CSV time range uses bounds
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

    if scale_matching not in ("linear", "nearest"):
        raise ValueError("scale_matching must be 'linear' or 'nearest'")
    scale_times, scale_radii = load_scale_csv(scale_csv_path)
    y_days = [y_day] * len(y_nc_paths) if y_days is None else list(y_days)
    if len(y_days) != len(y_nc_paths):
        raise ValueError("y_days must have the same length as y_nc_paths")
    y_days = [float(y_day if day is None else day) for day in y_days]
    if any(not np.isfinite(day) or day < 0 or not day.is_integer() for day in y_days):
        raise ValueError("y_days must contain finite nonnegative integer EXP days")
    y_days = [int(day) for day in y_days]
    y_wind_sources = ["exp"] * len(y_nc_paths) if y_wind_sources is None else list(y_wind_sources)
    if len(y_wind_sources) != len(y_nc_paths):
        raise ValueError("y_wind_sources must have the same length as y_nc_paths")
    if any(source not in ("exp", "ctrl") for source in y_wind_sources):
        raise ValueError("y_wind_sources must contain only 'exp' or 'ctrl'")
    y_colors = [None] * len(y_nc_paths) if y_colors is None else list(y_colors)
    if len(y_colors) != len(y_nc_paths):
        raise ValueError("y_colors must have the same length as y_nc_paths")
    for color in y_colors:
        if color is not None:
            mpl.colors.to_rgba(color)  # validate before reading any datasets
    y_alphas = [DEFAULT_SCATTER_ALPHA] * len(y_nc_paths) if y_alphas is None else list(y_alphas)
    if len(y_alphas) != len(y_nc_paths):
        raise ValueError("y_alphas must have the same length as y_nc_paths")
    y_alphas = [float(alpha) for alpha in y_alphas]
    if any(not np.isfinite(alpha) or not 0 <= alpha <= 1 for alpha in y_alphas):
        raise ValueError("y_alphas must contain finite values between 0 and 1")
    y_edgecolors = [None] * len(y_nc_paths) if y_edgecolors is None else list(y_edgecolors)
    if len(y_edgecolors) != len(y_nc_paths):
        raise ValueError("y_edgecolors must have the same length as y_nc_paths")
    for color in y_edgecolors:
        if color is not None:
            mpl.colors.to_rgba(color)
    y_linewidths = [DEFAULT_EDGE_LINEWIDTH] * len(y_nc_paths) if y_linewidths is None else list(y_linewidths)
    if len(y_linewidths) != len(y_nc_paths):
        raise ValueError("y_linewidths must have the same length as y_nc_paths")
    y_linewidths = [float(width) for width in y_linewidths]
    if any(not np.isfinite(width) or width < 0 for width in y_linewidths):
        raise ValueError("y_linewidths must contain finite nonnegative values")
    y_hollow = [False] * len(y_nc_paths) if y_hollow is None else list(y_hollow)
    if len(y_hollow) != len(y_nc_paths):
        raise ValueError("y_hollow must have the same length as y_nc_paths")
    y_sizes = [DEFAULT_MARKER_SIZE] * len(y_nc_paths) if y_sizes is None else list(y_sizes)
    if len(y_sizes) != len(y_nc_paths):
        raise ValueError("y_sizes must have the same length as y_nc_paths")
    y_sizes = [float(size) for size in y_sizes]
    if any(not np.isfinite(size) or size < 0 for size in y_sizes):
        raise ValueError("y_sizes must contain finite nonnegative values")
    if special_marker_sources is not None:
        special_marker_sources = set(special_marker_sources)

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
    if output_dir is not None:
        figdir = os.fspath(output_dir)
    elif iswhite:
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
    with ExitStack() as datasets:
        ctrl_ds = datasets.enter_context(xr.open_dataset(ctrl_nc_path)) if "ctrl" in y_wind_sources else None
        for y_path, source_name, source_marker, source_color, source_alpha, source_edgecolor, source_linewidth, source_hollow, source_size, source_day, wind_source in zip(
            y_nc_paths, y_source_names, y_markers, y_colors, y_alphas, y_edgecolors, y_linewidths, y_hollow, y_sizes, y_days, y_wind_sources
        ):
            ds = datasets.enter_context(xr.open_dataset(y_path))
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

            if wind_source == "ctrl":
                restart_coord = "restart_day" if "restart_day" in ds.coords else "case_day"
                restart_days = ds[restart_coord].sel(exp=exp_vals).values.astype(float)
                tw_profile = ctrl_data_for_exps(
                    ctrl_ds, exp_vals, restart_days + source_day,
                    "tang_wind_lower", method, vtype="mean",
                )
            else:
                tw_profile = y_tang_wind_profile_for_source(ds, source_name, source_day, method)
            tw_y = tw_profile.transpose("exp", "radius_km").values

            x_data = scale_radius_for_days(ctrl_days, scale_times, scale_radii, scale_matching)
            y_data = np.nanmax(tw_y, axis=1)
            paper_colors = cmap(norm(case_day))
            face_colors = paper_colors if source_color is None else np.tile(
                mpl.colors.to_rgba(source_color), (len(exp_vals), 1)
            )
            edge_colors = face_colors.copy()
            edge_colors[:, :3] *= 0.7
            if source_edgecolor is not None:
                edge_colors[:] = mpl.colors.to_rgba(source_edgecolor)

            plot_groups.append(
                {
                    "source": source_name,
                    "day": source_day,
                    "marker": source_marker,
                    "alpha": source_alpha,
                    "edgecolor": source_edgecolor,
                    "no_edge": isinstance(source_edgecolor, str) and source_edgecolor.lower() == "none",
                    "linewidth": source_linewidth,
                    "hollow": source_hollow,
                    "size": source_size,
                    "exp": np.asarray(exp_vals, dtype="U"),
                    "x": x_data,
                    "y": y_data,
                    "face_colors": face_colors,
                    "edge_colors": edge_colors,
                    "case_day": case_day,
                }
            )

        reference_points = load_reference_groups(
            scale_times, scale_radii,
            REFERENCE_GROUPS if reference_groups is None else reference_groups,
            REFERENCE_DATA_DIR if reference_data_dir is None else reference_data_dir,
            y_day, scale_matching,
        )

    if not plot_groups:
        raise ValueError("No y-axis data remained to plot after filtering.")

    # --- figure layout (keep original) ---
    fig = plt.figure(figsize=(10*1.2, 8*1.2))
    ax = fig.add_axes([0.15, 0.15, 0.72, 0.75])

    # Source marker is the default. special_o_exps is drawn first so it stays underneath.
    for igroup, group in enumerate(plot_groups):
        exp_arr = group["exp"]
        use_special = special_marker_sources is None or group["source"] in special_marker_sources
        is_o = np.array([use_special and exp in special_o_exps for exp in exp_arr], dtype=bool)
        is_x = np.array([use_special and exp in special_x_exps for exp in exp_arr], dtype=bool) & (~is_o)
        is_source = ~(is_o | is_x)

        if np.any(is_o):
            ax.scatter(
                group["x"][is_o],
                group["y"][is_o],
                s=group["size"] * 1.1,  # Preserve the slightly larger special circles.
                facecolors="none",
                edgecolors="k" if group["edgecolor"] is None else group["edgecolor"],
                linewidths=group["linewidth"],
                alpha=group["alpha"],
                zorder=5 + igroup,
                marker="o",
            )

        if np.any(is_source):
            ax.scatter(
                group["x"][is_source],
                group["y"][is_source],
                s=group["size"],
                facecolors="none" if group["hollow"] else group["face_colors"][is_source],
                edgecolors="none" if group["no_edge"] else group["edge_colors"][is_source],
                linewidths=group["linewidth"],
                alpha=group["alpha"],
                zorder=10 + igroup,
                marker=group["marker"],
                label=group["source"] if len(plot_groups) > 1 else None,
            )

        if np.any(is_x):
            ax.scatter(
                group["x"][is_x],
                group["y"][is_x],
                s=group["size"],
                c=group["face_colors"][is_x],
                edgecolors="none" if group["no_edge"] else group["edge_colors"][is_x],
                linewidths=group["linewidth"],
                alpha=group["alpha"],
                zorder=20 + igroup,
                marker="X",
            )

    for reference in reference_points:
        if reference["x"].size == 0:
            continue
        source = reference["style"]
        ax.scatter(
            reference["x"], reference["y"],
            s=source.get("size", 35),
            facecolors="none" if source.get("hollow", False) else source.get("color", "black"),
            edgecolors=source.get("edgecolor", source.get("color", "black")),
            linewidths=source.get("linewidth", 0),
            alpha=source.get("alpha", 1.0),
            marker=source.get("marker", "o"),
            zorder=source.get("zorder", 30),
            label=source["label"],
        )

    # --- axes settings (original y axis; scale-radius x axis) ---
    ax.set_yticks(np.arange(0, 9.01, 1.5))
    scale_xmax = max(100.0, np.ceil(np.max(scale_radii) / 100.0) * 100.0)
    ax.set_xticks(np.arange(0, scale_xmax + 1, 100))
    ax.set_ylim(-0.3, 9)
    ax.set_xlim(0, scale_xmax)
    ax.grid(True)
    # ax.set_ylabel("maximum tangential wind\nlast day average [m/s]")
    ## ax.set_ylabel("maximum daily-mean tangential wind\nlast day in EXP [m/s]")
    ax.set_xlabel(r"scale radius ($3\sigma$, km)" + "\nfrom shared CTRL day")
    plotted_days = sorted({group["day"] for group in plot_groups})
    day_text = ", ".join(str(day) for day in plotted_days)
    day_label = "day" if len(plotted_days) == 1 else "days"
    ax.set_ylabel(r"$\mathbf{vortex\ intensity}$" + f" [m/s]\nin EXP {day_label} {day_text}")
    if ax.get_legend_handles_labels()[0]:
        ax.legend(
            loc="best", fontsize=20, frameon=True,
            facecolor="white", edgecolor="black", framealpha=1.0,
            labelspacing=0.6,
            handletextpad=1,
        )

    # -- for Dxx_on colormap
    outpng = os.path.join(figdir, figname)
    # -- for DRYFAC colormap
    # outpng = f"{figdir}/scatter_max_scale_inDRY.png"
    plt.savefig(outpng, dpi=200)
    print("[saved]", outpng)
    #plt.show()
    plt.close(fig)
    return outpng


def cli():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--group", choices=[*EXPERIMENT_GROUPS, "both"], default="both",
        help="Select the experimental overlay (default: produce all configured figures).",
    )
    parser.add_argument("--center-flag", default=DEFAULT_CENTER_FLAG)
    parser.add_argument("--data-dir", help="Directory containing the CTRL and EXP NetCDF files.")
    parser.add_argument("--output-dir", help="Override the default figure directory.")
    parser.add_argument("--reference-data-dir", default=REFERENCE_DATA_DIR,
                        help="Directory containing the thermal-wind reference NetCDF files.")
    parser.add_argument("--y-day", type=int, default=DEFAULT_Y_DAY,
                        help="EXP day used when day_flag is None or omitted (default: %(default)s).")
    parser.add_argument("--scale-csv", default=DEFAULT_SCALE_CSV_PATH,
                        help="CSV containing time_days and scale_6sigma_km.")
    parser.add_argument("--scale-matching", choices=["linear", "nearest"], default="linear",
                        help="Scale lookup method (default: %(default)s); outside times use bounds.")
    args = parser.parse_args()
    datdir = args.data_dir or os.path.join(config.dataPath, "axisy_lowlevel", args.center_flag)

    common = dict(
        center_flag=args.center_flag,
        scale_csv_path=args.scale_csv,
        scale_matching=args.scale_matching,
        ctrl_nc_path=os.path.join(datdir, CTRL_DAILY_FILENAME),
        y_day=args.y_day,
        output_dir=args.output_dir,
        reference_data_dir=args.reference_data_dir,
        special_marker_sources=[ORIGIN_SOURCE["label"]],
        exclude=[
            'RRCE_3km_f00_halfwind_30',
            'cluster_f10_d20',
            'cluster_f10_d25',
            'cluster_f10_d30',

            'RRCE_3km_f00_30p27',
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
        # special_x_exps=[
        #     'RRCE_3km_f00_30p27',
        #     #'RRCE_3km_f00_halfwind_30',
        # ],
        # special_o_exps=[
        #     #20
        #     'RRCE_3km_f00_14p972',
        #     'RRCE_3km_f00_14p986',
        #     'RRCE_3km_f00_15p014',
        #     'RRCE_3km_f00_15p028',
        #     'RRCE_3km_f00_19p972',
        #     #25
        #     'RRCE_3km_f00_19p986',
        #     'RRCE_3km_f00_20p014',
        #     'RRCE_3km_f00_20p028',
        #     'RRCE_3km_f00_24p972',
        #     'RRCE_3km_f00_24p986',
        #     #30
        #     'RRCE_3km_f00_25p014',
        #     'RRCE_3km_f00_25p028',
        #     'RRCE_3km_f00_29p972',
        #     'RRCE_3km_f00_29p986',
        #     'RRCE_3km_f00_30p014',
        #     #35
        #     'RRCE_3km_f00_30p028',
        # ],
    )
    selected = list(EXPERIMENT_GROUPS) if args.group == "both" else [args.group]
    for group_name in selected:
        group = EXPERIMENT_GROUPS[group_name]
        sources = [ORIGIN_SOURCE, *group["sources"]]
        main(
            **common,
            reference_groups=REFERENCE_GROUPS if group.get("references", True) else {},
            y_nc_paths=[os.path.join(datdir, source["filename"]) for source in sources],
            y_source_names=[source["label"] for source in sources],
            y_colors=[source["color"] for source in sources],
            y_markers=[source["marker"] for source in sources],
            y_alphas=[source.get("alpha", DEFAULT_SCATTER_ALPHA) for source in sources],
            y_edgecolors=[source.get("edgecolor") for source in sources],
            y_linewidths=[source.get("linewidth", DEFAULT_EDGE_LINEWIDTH) for source in sources],
            y_hollow=[source.get("hollow", False) for source in sources],
            y_sizes=[source.get("size", DEFAULT_MARKER_SIZE) for source in sources],
            y_days=[source.get("day_flag") for source in sources],
            y_wind_sources=[source.get("wind_source", "exp") for source in sources],
            figname=f"scatter_max_scale_inDXX_{group_name}.png",
        )


if __name__ == "__main__":
    cli()
