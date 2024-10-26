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
  return newcmp

def draw_twoline(ax, x, y2, c):
  # _  = plt.plot(x, y2[0], c=c, alpha=0.5)
  # L0 = plt.plot(x, np.where(y2[1]>0.5, y2[0], np.nan),\
  #               c=c, alpha=1)

  """
  lwidths = y2[1]*10 + 1
  points  = np.array([x, y2[0]]).T.reshape(-1, 1, 2)
  segments = np.concatenate([points[:-1], points[1:]], axis=1)
  lc = LineCollection(segments, \
                      linewidths = lwidths,\
                      color = c, \
                      #path_effects=[mpl_pe.Stroke(linewidth=1, foreground='g'), mpl_pe.Normal()],\
                     )
  ax.add_collection(lc)
  """
  lc = plt.scatter(x, np.where(y2[1]<0.5, y2[0],np.nan), s=y2[1]**2*50+10, c='none', ec=c, marker='o', alpha=1)
  lc = plt.scatter(x, np.where(y2[1]>=0.5,y2[0],np.nan), s=y2[1]**2*50+10, c=c, marker='o', alpha=1)
  
  return lc

def draw_pannel(ax, x, twind, rwind):
  plt.sca(ax)
  xlim = (0, x.max())
  L0 = draw_twoline(plt.gca(), x, twind, 'C0')
  plt.xlim(xlim)
  plt.yticks(np.arange(0,10.1,2))
  plt.ylim(-1, 9)
  plt.grid(True)

  ax_twinx = ax.twinx()
  L1 = draw_twoline(plt.gca(), x, rwind, 'C1')
  plt.xlim(xlim)
  plt.yticks(np.arange(-10,0.11, 1))
  plt.ylim(0.5, -4.5)

  return 

