import numpy as np
import sys, os
sys.path.insert(1, "../")

import config
from concurrent.futures import ProcessPoolExecutor, as_completed

import matplotlib.pyplot as plt
import matplotlib as mpl
from netCDF4 import Dataset
from matplotlib.ticker import FixedLocator, FixedFormatter
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


def is_integer_like(x, tol=1e-6):
    # True if x is within tol of an integer
    return abs(x - round(x)) < tol

def set_figure_default():
    plt.rcParams.update({
        "font.size": 20,
        "axes.linewidth": 2,
        "lines.linewidth": 5,
    })


def choose_pool_params(nt, max_workers=10):
    cpu = os.cpu_count() or 4
    cap = min(cpu, max_workers)

    if nt >= 2000:
        n_workers = min(8, cap)
        chunksize = 80
    elif nt >= 500:
        n_workers = min(6, cap)
        chunksize = 40
    else:
        n_workers = min(4, cap)
        chunksize = 20

    chunksize = max(1, min(chunksize, nt))
    return n_workers, chunksize


def create_cmap_segmented():
    # Do NOT include 31 in ticks
    tick_vals = np.array(
        "0 10 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30".split(),
        dtype=float,
    )

    # Segmented bins; keep last edge at 30.5 so values up to 30 map to last bin,
    # and values > 30.5 go to "over" color when extend="max".
    bounds = np.r_[tick_vals - 0.5, 30.5]

    newcolors = np.vstack((
        [[0.8, 0.8, 0.8, 1.0]],
        [[0.5, 0.5, 0.5, 1.0]],
        plt.cm.Greens(np.linspace(0.2, 0.9, 5)),
        plt.cm.Oranges(np.linspace(0.2, 0.9, 5)),
        plt.cm.Blues(np.linspace(0.2, 0.9, 5)),
        np.atleast_2d(plt.cm.Purples(0.7)),
    ))

    cmap = mpl.colors.ListedColormap(newcolors, name="SegmentedCmap")
    cmap.set_under((0.7, 0.7, 0.7))
    cmap.set_over(plt.cm.Purples(0.7))

    norm = mpl.colors.BoundaryNorm(bounds, cmap.N, clip=False)
    return tick_vals, bounds, cmap, norm


def parse_restart_day(exp):
    if exp in ("RRCE_3km_f00", "RRCE_3km_f10"):
        return 0.0
    return float(exp.split("_")[-1].replace("p", "."))


def get_cwv_stats(datdir, it, dry_thresh=30.0):
    # Read CWV field once, compute mean, std, and dry fraction
    fn = os.path.join(datdir, f"wp-{it:06d}.nc")
    with Dataset(fn, "r") as nc:
        cwv = nc.variables["cwv"][0, ...]
        cwv_mean = float(cwv.mean())
        cwv_std  = float(cwv.std())
        dry_frac = float((cwv < dry_thresh).mean())
    return it, cwv_mean, cwv_std, dry_frac


def _chunk_worker(datdir, it_list, dry_thresh):
    # Process a chunk of time indices in one process call
    out = []
    for it in it_list:
        out.append(get_cwv_stats(datdir, int(it), dry_thresh=dry_thresh))
    return out


def load_cwv_and_dryfrac_parallel(datdir, nt, n_workers=4, chunksize=20, dry_thresh=30.0):
    its = np.arange(nt, dtype=int)
    chunks = [its[i:i+chunksize] for i in range(0, nt, chunksize)]

    results = []
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(_chunk_worker, datdir, ch, dry_thresh) for ch in chunks]
        for future in as_completed(futures):
            results.extend(future.result())

    results.sort(key=lambda x: x[0])
    cwv_mean = np.array([m for _, m, _, _ in results], dtype=float)
    cwv_std  = np.array([s for _, _, s, _ in results], dtype=float)
    dry_frac = np.array([d for _, _, _, d in results], dtype=float)
    return cwv_mean, cwv_std, dry_frac


def add_colorbar(fig, ax, cmap, norm, bounds, tick_vals, title="Dxx_on", loc='left'):
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])

    # Inset colorbar at bottom-left of the axes
    # height is a fraction of the parent axes height
    width_frac = 0.035
    height_frac = 3/5
    margin = 0.06
    if loc=='right':
        x0 = 1.0 - width_frac - margin
    else:
        x0 = margin
    y0 = 0.02
    cax = inset_axes(
        ax,
        width=f"{100.0*width_frac:.1f}%",
        height=f"{100.0 * height_frac:.1f}%",
        loc="lower left",
        # bbox_to_anchor=(0.06, 0.02, 1, 1),   # (x0, y0, w, h) in axes fraction
        bbox_to_anchor=(x0, y0, 1, 1),   # (x0, y0, w, h) in axes fraction
        bbox_transform=ax.transAxes,
        borderpad=0.0,
    )


    cbar = fig.colorbar(
        sm,
        cax=cax,
        orientation="vertical",
        extend="neither",
        boundaries=bounds,
    )

    # Put tick marks at bin centers, but show labels only for selected ticks
    centers = 0.5 * (bounds[:-1] + bounds[1:])
    label_set = {0, 10, 15, 20, 25, 30}
    labels = [str(int(t)) if int(t) in label_set else "" for t in tick_vals]

    cbar.ax.yaxis.set_major_locator(FixedLocator(centers))
    cbar.ax.yaxis.set_major_formatter(FixedFormatter(labels))
    cbar.ax.minorticks_off()
    cbar.ax.tick_params(which="minor", left=False, right=False)

    # Title above colorbar
    cbar.ax.set_title(title, pad=13, fontweight="bold")

    return cbar


def main():
    set_figure_default()
    tick_vals, bounds, cmap, norm = create_cmap_segmented()

    # If argv[1] exists, plot only that exp index; else plot all exps
    if len(sys.argv) >= 2:
        iexp = int(sys.argv[1])
        exp_list = [config.expList[iexp]]
    else:
        exp_list = list(config.expList)

    # Figure 1: CWV mean series
    fig1, ax1 = plt.subplots(figsize=(14, 10))
    ax1.set_title("CWV domain mean [mm]", loc="left", fontweight="bold")
    ax1.set_xlabel("Time [days]")
    ax1.set_ylabel("CWV [mm]")

    # Figure 2: dry fraction series
    fig2, ax2 = plt.subplots(figsize=(14, 10))
    ax2.set_title("Dry fraction (CWV<30mm)", loc="left", fontweight="bold")
    ax2.set_xlabel("Time [days]")
    ax2.set_ylabel("Dry fraction")

    # Figure 3: CWV std series
    fig3, ax3 = plt.subplots(figsize=(14, 10))
    ax3.set_title("CWV std series", loc="left", fontweight="bold")
    ax3.set_xlabel("Time [days]")
    ax3.set_ylabel("CWV std. [mm]")

    for exp in exp_list:
        if exp == "RRCE_3km_f00_25p07": continue
        print(exp)
        idx = config.expList.index(exp)
        dtime = config.getExpDeltaT(exp)  # minutes


        if exp == "RRCE_3km_f00":
            nt = 72 * 35 + 1
        else:
            nt = 217

        rday = parse_restart_day(exp)
        datdir = os.path.join(config.dataPath, "wp", exp)

        n_workers, chunksize = choose_pool_params(nt, max_workers=10)

        cwv_series, cwv_std_series, dryfrac_series = load_cwv_and_dryfrac_parallel(
            datdir=datdir,
            nt=nt,
            n_workers=n_workers,
            chunksize=chunksize,
            dry_thresh=30.0,
        )
        
        x = rday + np.arange(nt) * dtime / 60.0 / 24.0
        
        # Line style/color
        if exp == "RRCE_3km_f00":
            lc = "k"
            lw = 8
            zorder = 1
        else:
            lc = cmap(norm(rday))
            #lw = 4
            lw = 3
            zorder = 5
        
        # Dashed line if restart day has decimals
        ls = "-"# if is_integer_like(rday) else ':'
        
        ax1.plot(x, cwv_series, c=lc, lw=lw, ls=ls, zorder=zorder, label=exp)
        ax2.plot(x, dryfrac_series, c=lc, lw=lw, ls=ls, zorder=zorder, label=exp)
        ax3.plot(x, cwv_std_series, c=lc, lw=lw, ls=ls, zorder=zorder, label=exp)

    # Styling for fig1
    ax1.set_ylim(20, 45)
    ax1.set_xlim(0, 35)
    ax1.grid(True)
    
    # Styling for fig2
    ax2.set_ylim(0.0, 0.8)
    ax2.set_xlim(0, 35)
    ax2.grid(True)
    
    # Styling for fig3 (adjust if needed)
    #ax3.set_ylim(0.0, 15)
    ax3.set_xlim(0, 35)
    ax3.grid(True)
    
    # Add the same segmented colorbar to all figures
    add_colorbar(fig1, ax1, cmap, norm, bounds, tick_vals, loc='left')
    add_colorbar(fig2, ax2, cmap, norm, bounds, tick_vals, loc='right')
    add_colorbar(fig3, ax3, cmap, norm, bounds, tick_vals, loc='right')
    
    fig1.savefig("./cwv.png", bbox_inches="tight", dpi=300)
    fig2.savefig("./dryfraction.png", bbox_inches="tight", dpi=300)
    fig3.savefig("./cwv_std.png", bbox_inches="tight", dpi=300)
    #plt.show()


if __name__ == "__main__":
    main()
