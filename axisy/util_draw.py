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
    ncols  = len(C.collections)
    levels = C.get_array()
    minval = np.max(levels)
    maxval = np.min(levels)
    for i in range(ncols):
        col = C.collections[i]
        if len(col.get_paths())>0:
          maxval = max([maxval, levels[i]])
          minval = min([minval, levels[i]])
        #print(minval, maxval)
    return minval, maxval, levels[1]-levels[0]


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
    plt.rcParams['hatch.linewidth'] = 1
    edge_co = edgecolor or 'k'
    C=plt.contourf(radius_1d, zc_1d, data, \
                  levels=levels, colors='none',\
                  hatches=hat)
    # For each level, we set the color of its hatch 
    for i, collection in enumerate(C.collections):
        collection.set_edgecolor(edge_co)
        collection.set_edgecolor("face")
        collection.set_linewidth(0.000000000001)
    plt.text(0.985,0.98+annotation_y,\
             f'hatch: '+\
             f'{annotation}'+\
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

