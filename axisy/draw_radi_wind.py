import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(1,'../')
import config
from netCDF4 import Dataset
import matplotlib as mpl
from mpi4py import MPI

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

def get_cmap(extend='both'):
  if extend=='both':
    top = mpl.colormaps['Purples_r']
    bottom = mpl.colormaps['Oranges']
    newcolors = np.vstack((top(np.linspace(0.3, 1, 128)),\
                           bottom(np.linspace(0, 0.7, 128)),\
                         ))
    newcmp = mpl.colors.ListedColormap(newcolors, name='OrangeBlue')
    return newcmp
 

def draw_upper_pcolor(ax, cax, radius_1d, zc_1d, \
                      data, levels, cmap, extend, \
                      title,title_right=''):
    plt.sca(ax)
    norm = mpl.colors.BoundaryNorm(boundaries=levels, \
              ncolors=256, extend=extend)
    plt.pcolormesh(radius_1d, zc_1d, data, cmap=cmap, norm=norm)
    plt.colorbar(cax=ax_cbar)
    plt.plot([0, radius_1d.max()], [1,1], '0.75', lw=1, zorder=50)
    plt.xlim(0,550)
    plt.ylim(0,16)  #0km - 15km
    plt.xticks(np.arange(0,551,100), ['']*6)
    plt.ylabel('height [km]', fontsize=15)
    plt.grid(True)
    plt.title(f'{title}', loc='left', fontweight='bold')
    plt.title(f'{title_right}', loc='right', fontweight='bold', fontsize=15)
    return

def get_contour_levels(C):
    ncols  = len(C.collections)
    levels = C.get_array()
    minval = levels[-1]
    maxval = levels[0]
    for i in range(ncols):
        col = C.collections[i]
        if len(col.get_paths())>0:
          maxval = max([maxval, levels[i]])
          minval = min([maxval, levels[i]])
    return minval, maxval, levels[1]-levels[0]

def draw_upper_contour(ax, radius_1d, zc_1d, \
                       data, levels, lws=[1], \
                       inline=False):
    plt.sca(ax)
    C=plt.contour(radius_1d, zc_1d, data, \
                  levels=levels, linewidths=lws, colors=['k'])
    if inline:
        plt.clabel(C, fontsize=12)
    elif not inline:
        minlev, maxlev, intlev = get_contour_levels(C)
        plt.text(0.985,0.98,\
                 f'CONTOUR '+\
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

def draw_lower(ax, ax_top, radius_1d, \
                    data, data_a, ylim, yticks, ylabel, color=None):
    plt.sca(ax)
    plt.plot(radius_1d, data, lw=5, alpha=0.5, c=color)
    plt.plot(radius_1d, np.where(data_a>0.3,data,np.nan), lw=5, c=color)
    plt.ylim(ylim)
    plt.yticks(yticks)
    plt.xticks(ax_top.get_xticks())
    plt.xlim(ax_top.get_xlim())
    plt.xlabel('radius [km]')
    plt.ylabel(f'{ylabel}', fontsize=15, color=color)
    plt.grid(True)
    return

plt.rcParams.update({'font.size':20,
                     'axes.linewidth':2,
                     'lines.linewidth':5})

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])

nt = config.totalT[iexp]
exp = config.expList[iexp]
if exp=='RRCE_3km_f00':
  nt=2521
else:
  nt=217
if (cpuid==0): print(exp, nt)
dtime = 20

center_flag='czeta0km_positivemean'
fig_flag   ='radi_wind'
datdir=config.dataPath+f"/axisy/{center_flag}/{exp}/"
figdir=f'./{center_flag}/{fig_flag}/{exp}/'
os.system(f'mkdir -p {figdir}')


it=216
it=72*3
for it in range(nt):
  print(it)
  fname = f'{datdir}/axmean-{it:06d}.nc'
  nc = Dataset(fname, 'r')
  radius_1d = nc.variables['radius'][:]/1000 #[km]
  zc_1d  = nc.variables['zc'][:]/1000 #[km]
  
  set_black_background()
 
  plt.close('all') 
  fig = plt.figure(figsize=(8,8))
  ax_top   = plt.axes([0.15,0.27,0.7,0.6])
  ax_cbar  = plt.axes([0.88, 0.27, 0.025, 0.6])
  ax_lower = plt.axes([0.15,0.1,0.7,0.15])
  ax_lower_right = ax_lower.twinx()
  
  varname = 'radi_wind'
  varunit = nc.variables[varname].units
  rwind = nc.variables[varname][0,0,:,:]
  rwind_a = nc.variables[varname][0,1,:,:]
  levels  = np.arange(-5,5.1,1)
  cmap    = get_cmap('both')
  
  _ = draw_upper_pcolor(ax_top, ax_cbar, \
                        radius_1d, zc_1d, \
                        data   = rwind, \
                        levels = levels, \
                        cmap   = cmap, \
                        extend = 'both',\
                        title  = f'{varname} [{varunit}]',\
                        title_right  = f'{exp}\n{(dtime*it)/60:.1f}hr',\
                       )
  C = draw_upper_contour(ax_top,radius_1d, zc_1d,\
                         data   = rwind_a, \
                         levels = [0.3,0.5,0.9],\
                         lws    = [1],\
                         inline = True
                        )
  
  
  plt.sca(ax_lower)
  varname = 'cwv'
  varunit = nc.variables[varname].units
  cwv = nc.variables[varname][0,0,:]
  cwv_a = nc.variables[varname][0,1,:]
  _ = draw_lower(ax_lower, ax_top, radius_1d, \
                  data   = cwv, \
                  data_a = cwv_a, \
                  ylim   = (20, 65), \
                  yticks = [20, 35, 50], \
                  ylabel = f'{varname} [{varunit}]',\
                  color  = '1',\
                 )
  
  varname = 'radi_wind'
  varunit='m/s'
  idxz=8
  _ = draw_lower(ax_lower_right, ax_top, radius_1d, \
                  data   = nc.variables[varname][0,0,idxz,:], \
                  data_a = nc.variables[varname][0,1,idxz,:], \
                  ylim   = (-3,3), \
                  yticks = [-3, -1, 1], \
                  ylabel = f'{varname}\n@{zc_1d[idxz]}km [{varunit}]',\
                  color  = 'C1',\
                 )
  plt.savefig(f'{figdir}/{it:06d}.png',dpi=200)

plt.close('all')
