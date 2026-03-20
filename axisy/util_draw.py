import numpy as np
import matplotlib.pyplot as plt
import sys, os
import matplotlib as mpl

def set_figure_defalut():
  plt.rcParams.update({'font.size':20,
                       'axes.linewidth':2,
                       'lines.linewidth':5})



def set_black_background():
  plt.rcParams.update({
                       'axes.edgecolor': 'white',
                       'axes.facecolor': 'black',
                       'figure.edgecolor': 'black',
                       'figure.facecolor': 'black',
                       'text.color': 'white',
                       'xtick.color': 'white',
                       'ytick.color': 'white',
                       'axes.labelcolor': 'white',
                      })

def get_cmap(name='colorful'):
  if name=='pwo':
    top = mpl.colormaps['Purples_r']
    bottom = mpl.colormaps['Oranges']
    newcolors = np.vstack((top(np.linspace(0.3, 1, 128)),\
                           bottom(np.linspace(0, 0.7, 128)),\
                         ))
    newcmp = mpl.colors.ListedColormap(newcolors, name='OrangeBlue')
  elif name=='colorful':
    colors = ['w', '#00BFFF', '#3CB371', '#F0E68C', '#FFA500', '#FF6347']
    nodes = np.linspace(0,1,len(colors))
    newcmp = mpl.colors.LinearSegmentedColormap.from_list("cmap", list(zip(nodes, colors)))
  elif name=='cwv':
    # white->wheat->darkcyan->darkblue->(4,130,191)
    colors = np.array([(255,255,255,255), \
                       (241,223,184,255), \
                       (60,137,138,255), \
                       (0,0,133,255), \
                       (4,130,191,255),\
                     ])/255
    nodes = np.linspace(0,1,colors.shape[0])
    newcmp = mpl.colors.LinearSegmentedColormap.from_list("cmap", list(zip(nodes, colors)))
    newcmp.set_over(np.array((0,250,250,255))/255)
  return newcmp

def create_figure_and_axes(lower_right=True):
  fig = plt.figure(figsize=(8,8))
  ax_top   = plt.axes([0.135,0.27,0.7,0.6])
  ax_cbar  = plt.axes([0.855, 0.27, 0.025, 0.6])
  ax_lower = plt.axes([0.135,0.1,0.7,0.15])
  if lower_right:
    ax_lower_right = ax_lower.twinx()
  else: 
    ax_lower_right = None
  return fig, ax_top, ax_cbar, ax_lower, ax_lower_right
  

def draw_upper_pcolor(ax, cax, radius_1d, zc_1d, \
                      data, levels, cmap, extend, \
                      title,title_right=''):
    plt.sca(ax)
    norm = mpl.colors.BoundaryNorm(boundaries=levels, \
              ncolors=256, extend=extend)
    P = plt.pcolormesh(radius_1d, zc_1d, data, cmap=cmap, norm=norm)
    CB = plt.colorbar(cax=cax)
    plt.plot([0, radius_1d.max()], [1,1], '0.75', lw=1, zorder=50)
    plt.xlim(0,550)
    plt.ylim(0,16)  #0km - 15km
    plt.xticks(np.arange(0,551,100), ['']*6)
    plt.ylabel('height [km]')#, fontsize=15)
    plt.grid(True)
    plt.title(f'{title}', loc='left', fontweight='bold')
    plt.title(f'{title_right}', loc='right', fontweight='bold')
    return  P, CB


def get_contour_levels(C):
    """
    Return (min_level_drawn, max_level_drawn, level_interval)

    Compatible with newer Matplotlib where QuadContourSet may not expose
    `collections`. Prefer `C.levels` as the source of contour levels.
    """
    # 1) Get contour levels robustly
    levels = np.asarray(getattr(C, "levels", []), dtype=float)

    if levels.size == 0:
        # fallback (should rarely happen)
        arr = C.get_array()
        if arr is None or len(arr) == 0:
            return np.nan, np.nan, np.nan
        levels = np.asarray(arr, dtype=float)

    # interval (best effort)
    if levels.size >= 2:
        diffs = np.diff(levels)
        nz = diffs[np.abs(diffs) > 0]
        intlev = float(nz[0]) if nz.size > 0 else float(diffs[0])
    else:
        intlev = np.nan

    # 2) Determine which levels are actually drawn
    # If collections exist, mimic your original logic (check get_paths()).
    if hasattr(C, "collections"):
        ncols = min(len(C.collections), levels.size)
        drawn_levels = []
        for i in range(ncols):
            col = C.collections[i]
            # original check: any paths => that level appears on plot
            if len(col.get_paths()) > 0:
                drawn_levels.append(levels[i])

        if len(drawn_levels) == 0:
            # Nothing drawn (e.g., all levels outside data range)
            return np.nan, np.nan, intlev

        drawn_levels = np.asarray(drawn_levels, dtype=float)
        return float(np.nanmin(drawn_levels)), float(np.nanmax(drawn_levels)), intlev

    # 3) Fallback when collections is unavailable: use full level range
    return float(np.nanmin(levels)), float(np.nanmax(levels)), intlev


def draw_upper_contour(ax, radius_1d, zc_1d, \
                       data, levels, lws=[1], color=None,\
                       inline=False, annotation=''):
    plt.sca(ax)
    co = color or 'k'
    C=plt.contour(radius_1d, zc_1d, data, \
                  levels=levels, linewidths=lws, colors=[co])
    ## plt.text(0.985,0.98,\
    ##          f'axisymmetric\n'+\
    ##          f'max:{data.max():.5f}\n'+\
    ##          f'min:{data.min():.5f}',\
    ##          fontsize=12,\
    ##          zorder=12,\
    ##          ha="right", va="top",\
    ##          transform=ax.transAxes,\
    ##          color='0',\
    ##         )
            
    if inline:
        plt.clabel(C, fontsize=12)
    elif not inline:
        minlev, maxlev, intlev = get_contour_levels(C)
        if len(annotation)>0:
          plt.text(0.985,0.98,\
                   f'{annotation}'+\
                   #f'CONTOUR '+\
                   f'FROM {minlev:.1f} '+\
                   f'TO {maxlev:.1f} '+\
                   f'BY {intlev:.1f}',\
                   fontsize=12,\
                   zorder=12,\
                   ha="right", va="top",\
                   transform=ax.transAxes,\
                   color='0',\
                   bbox=dict(boxstyle="square",
                             ec='0',
                             fc='1',
                             ),\
                   )
    return C

def draw_upper_hatch(ax, radius_1d, zc_1d, \
                     data, levels, hat=['/'], edgecolor=None,\
                     annotation_y=0, annotation='',\
                    ):
    plt.sca(ax)
    plt.rcParams['hatch.linewidth'] = 0.3
    edge_co = edgecolor or 'k'
    C=plt.contourf(radius_1d, zc_1d, data, \
                  levels=levels, colors='none',\
                  hatches=hat)
    # For each level, we set the color of its hatch 
    targets = C.collections if hasattr(C, "collections") else [C]
    for coll in targets:
        coll.set_facecolor('none')
        coll.set_edgecolor(edge_co)
        coll.set_linewidth(0.0)
    plt.text(0.985,0.98+annotation_y,\
             f'{annotation}'+\
             f'hatch: '+\
             f'axisymmetric > {levels[0]:.1f} \n',\
             # f'max:{data.max():.2f}; '+\
             # f'min:{data.min():.2f}\n',\
             fontsize=12,\
             zorder=12,\
             ha="right", va="top",\
             transform=ax.transAxes,\
             color='0',\
            )
            
    return C

def draw_lower(ax, ax_top, radius_1d, \
                    data, data_a, ylim, yticks, ylabel, color=None, label='',label_color=None):
    plt.sca(ax)
    plt.plot(radius_1d, data, lw=5, alpha=0.5, c=color)
    C = plt.plot(radius_1d, np.where(data_a>0.5,data,np.nan), lw=5, c=color, label='')
    plt.ylim(ylim)
    plt.yticks(yticks)
    plt.xticks(ax_top.get_xticks())
    plt.xlim(ax_top.get_xlim())
    plt.xlabel('radius [km]')
    plt.ylabel(f'{ylabel}', fontsize=15, color=label_color)
    plt.grid(True)
    return C


def _cumtrapz_1d(y, x, axis=-1):
    """
    Cumulative trapezoidal integral of y(x) along `axis`.
    Returns array with same shape as y, with integral starting at 0.
    """
    y = np.asarray(y)
    x = np.asarray(x)

    # dx along axis
    dx = np.diff(x)  # shape (n-1,)
    # bring axis to last for easier broadcasting
    y_mv = np.moveaxis(y, axis, -1)  # (..., n)
    out = np.zeros_like(y_mv)

    # trapezoid increments: 0.5*(y[k]+y[k+1])*dx[k]
    inc = 0.5 * (y_mv[..., :-1] + y_mv[..., 1:]) * dx  # (..., n-1)
    out[..., 1:] = np.cumsum(inc, axis=-1)

    return np.moveaxis(out, -1, axis)


def psi_from_w(radius_1d, w, rhoz_1d=None, r_axis=-1, z_axis=-2):
    """
    Compute axisymmetric mass streamfunction psi(r,z) from w(r,z) via:
      dpsi/dr = r * w                (Boussinesq)
      dpsi/dr = r * rho0(z) * w      (anelastic; if rhoz_1d given)

    Assumes w has r dimension at r_axis and z dimension at z_axis.
    Returns psi with same shape as w.
    """
    r = np.asarray(radius_1d)
    ww = np.asarray(w)

    # Build weight: r (and optionally rho0(z))
    # Create r broadcast shape
    r_shape = [1] * ww.ndim
    r_shape[r_axis] = r.size
    r_b = r.reshape(r_shape)

    F = r_b * ww

    if rhoz_1d is not None:
        rho = np.asarray(rhoz_1d)
        z_shape = [1] * ww.ndim
        z_shape[z_axis] = rho.size
        rho_b = rho.reshape(z_shape)
        F = rho_b * F

    # Integrate along r, psi(0,z)=0
    psi = _cumtrapz_1d(F, r, axis=r_axis)
    return psi


def psi_from_ur(radius_1d, zz_1d, rwind, rhoz_1d=None, z0_index=0, r_axis=-1, z_axis=-2):
    """
    Compute axisymmetric mass streamfunction psi(r,z) from u_r(r,z)=rwind via:
      dpsi/dz = - r * u_r                  (Boussinesq)
      dpsi/dz = - r * rho0(z) * u_r        (anelastic; if rhoz_1d given)

    Need a reference boundary condition at z=z0: psi(r,z0)=0 (default).
    Assumes rwind has r dimension at r_axis and z dimension at z_axis.
    Returns psi with same shape as rwind.
    """
    r = np.asarray(radius_1d)
    z = np.asarray(zz_1d)
    ur = np.asarray(rwind)

    # r broadcast
    r_shape = [1] * ur.ndim
    r_shape[r_axis] = r.size
    r_b = r.reshape(r_shape)

    G = -r_b * ur

    if rhoz_1d is not None:
        rho = np.asarray(rhoz_1d)
        z_shape = [1] * ur.ndim
        z_shape[z_axis] = rho.size
        rho_b = rho.reshape(z_shape)
        G = rho_b * G

    # Integrate along z with psi(..., z0)=0
    # We will integrate from z0_index upward and downward separately to reduce drift.
    # First compute cumulative from bottom to top, then shift to enforce psi(z0)=0.
    psi = _cumtrapz_1d(G, z, axis=z_axis)

    # Enforce psi at z0_index = 0 by subtracting psi(z0) for each r (and other dims)
    # Take slice at z0_index along z_axis
    slicer = [slice(None)] * psi.ndim
    slicer[z_axis] = z0_index
    psi_z0 = psi[tuple(slicer)]

    # Expand psi_z0 back to psi shape for broadcasting subtraction
    expand_shape = list(psi.shape)
    expand_shape[z_axis] = 1
    psi_z0_expanded = np.expand_dims(psi_z0, axis=z_axis)

    psi = psi - psi_z0_expanded
    return psi


def compute_and_check_streamfunction(radius_1d, zz_1d, rhoz_1d, w, rwind,
                                     use_density=True, z0_index=0, r_axis=-1, z_axis=-2):
    """
    Call two methods to compute psi:
      - from w (integrate in r)
      - from u_r (integrate in z)
    Then compute difference for consistency check.

    Returns (psi_w, psi_ur, dpsi).
    """
    rho = rhoz_1d if use_density else None

    psi_w  = psi_from_w(radius_1d, w,     rhoz_1d=rho, r_axis=r_axis, z_axis=z_axis)
    psi_ur = psi_from_ur(radius_1d, zz_1d, rwind, rhoz_1d=rho,
                         z0_index=z0_index, r_axis=r_axis, z_axis=z_axis)

    dpsi = psi_w - psi_ur
    return psi_w, psi_ur, dpsi


# ----------------------
# Example usage (assume arrays are already loaded):
# psi_w, psi_ur, dpsi = compute_and_check_streamfunction(
#     radius_1d, zz_1d, rhoz_1d, w, rwind,
#     use_density=True,      # anelastic mass streamfunction
#     z0_index=0,            # enforce psi(r, z0)=0 at the lowest level
#     r_axis=-1, z_axis=-2   # common shape: (..., z, r)
# )
#
# # Quick diagnostics
# print("psi_w range:",  np.nanmin(psi_w),  np.nanmax(psi_w))
# print("psi_ur range:", np.nanmin(psi_ur), np.nanmax(psi_ur))
# print("dpsi range:",   np.nanmin(dpsi),   np.nanmax(dpsi))
# print("dpsi RMS:",     np.sqrt(np.nanmean(dpsi**2)))
