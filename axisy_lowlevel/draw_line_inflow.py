import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(1,'../')
import config
from netCDF4 import Dataset
import matplotlib as mpl
from mpi4py import MPI
import util_draw as udraw
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.tools as tools
from matplotlib.collections import LineCollection
import matplotlib.patheffects as mpl_pe

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

x_rday      = []
y_tmax_init = []
y_rmax_init = []
y_tmax_3dy  = []
y_rmax_3dy  = []


for iexp in range(1,19):

  nt = config.totalT[iexp]
  exp = config.expList[iexp]
  dtime = 20

  if exp=='RRCE_3km_f00' or exp=='RRCE_3km_f10':
    restart_day = 0 
    rce_it0, rce_it1 = 0, 1
  else:
    restart_day = int(exp.split('_')[-1])
    rce_it0, rce_it1 = (restart_day-1)*72, (restart_day)*72
  x_rday.append(restart_day)
   
  center_flag='czeta0km_positivemean'
  fig_flag   ='line_inflow'
  datdir=config.dataPath+f"/axisy/{center_flag}/{exp}/"
  figdir=f'./{center_flag}/{fig_flag}/'
  os.system(f'mkdir -p {figdir}')

  print(iexp, exp, restart_day)
  
  fname = f'{datdir}/axmean_process-{0:06d}.nc'
  nc = Dataset(fname, 'r')
  radius_1d = nc.variables['radius'][:]/1.e3
  zc_1d     = nc.variables['zc'][:]/1.e3
  ens_1d    = np.array(['mean', 'axisym'])
  time_hr_1d  = np.arange(nt)*dtime/60 #hours
  
  dims = (ens_1d.size, radius_1d.size)
 
  rwind_init = np.zeros(dims)
  twind_init = np.zeros(dims)
  nit = rce_it1 - rce_it0
  print(rce_it0, rce_it1, nit)
  for it in range(rce_it0, rce_it1):
    fname = f'{datdir}/../RRCE_3km_f00/axmean_process-{it:06d}.nc'
    nc    = Dataset(fname, 'r')
    rwind_init += nc.variables['radi_wind_lower'][0, :] / nit
    twind_init += nc.variables['tang_wind_lower'][0, :] / nit
  
  ## fname = f'{datdir}/../RRCE_3km_f00/axmean_process-{rce_it1:06d}.nc'
  ## nc    = Dataset(fname, 'r')
  ## rwind_init += nc.variables['radi_wind_lower'][0, :]
  ## twind_init += nc.variables['tang_wind_lower'][0, :]

  y_tmax_init.append(twind_init[0].max())
  y_rmax_init.append(rwind_init[0].min())
  
  # create last days 
  rwind_3rd  = np.zeros(dims)
  twind_3rd  = np.zeros(dims)
  it0, it1 = 145, 217
  nit = it1 - it0
  for it in range(it0, it1):
    fname = f'{datdir}/axmean_process-{it:06d}.nc'
    nc    = Dataset(fname, 'r')
    rwind_3rd += nc.variables['radi_wind_lower'][0, :] / nit
    twind_3rd += nc.variables['tang_wind_lower'][0, :] / nit
  y_tmax_3dy.append(twind_3rd[0].max())
  y_rmax_3dy.append(rwind_3rd[0].min())
  
  
  udraw.set_figure_defalut() 
  udraw.set_black_background()
  
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
  
  fig, axs = plt.subplots(2, 1, figsize=(10,6), sharex=True)
  plt.subplots_adjust(left=0.1)
  bbox = dict(boxstyle='round', fc='k', ec='1')
  
  plt.sca(axs[0])
  _ = draw_pannel(plt.gca(), radius_1d, twind_init, rwind_init)
  plt.title(f'{exp}', loc='left', fontweight='bold')
  #plt.text(0.98, 0.93, 'INIT', ha='right', va='top', transform=axs[0].transAxes, bbox=bbox)
  txtstr = f'{restart_day-1}' if restart_day>1 else '0'
  plt.text(0.98, 0.93, f'RCE {txtstr}-{restart_day} day', ha='right', va='top', transform=axs[0].transAxes, bbox=bbox)

  plt.sca(axs[1])
  _ = draw_pannel(plt.gca(), radius_1d, twind_3rd, rwind_3rd)
  plt.text(0.98, 0.93, '3rd day', ha='right', va='top', transform=axs[1].transAxes, bbox=bbox)

  fig.text(0.03, 0.5, 'tang_wind [m/s]', va='center', color='C0', fontweight='bold', rotation='vertical')
  fig.text(0.96, 0.5, 'radi_wind [m/s]', va='center', color='C1', fontweight='bold', rotation='vertical')
  plt.savefig(f'{figdir}/{exp}.png')
  plt.close('all')
  # plt.show()


bounds=np.array('10 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30'.split()).astype(int)
newcolors = np.vstack((
                       plt.cm.Greens(np.linspace(0.2,0.9,1)),
                       plt.cm.Oranges(np.linspace(0.2,0.9,5)),
                       plt.cm.Blues(np.linspace(0.2,0.9,5)),
                       plt.cm.Purples(np.linspace(0.2,0.9,5))
                     ))
cmap = mpl.colors.ListedColormap(newcolors, name='OrangeBlue')
cmap.set_under((0.7,0.7,0.7))
cmap.set_over(plt.cm.Purples(0.95))
norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

udraw.set_figure_defalut() 
udraw.set_black_background()
fig = plt.figure(figsize=(10,8))
ax  = fig.add_axes([0.13, 0.1, 0.8, 0.8])
#cax = fig.add_axes([0.12, 0.86, 0.35, 0.03])
cax = fig.add_axes([0.8, 0.35, 0.03, 0.5])
plt.sca(ax)
plt.plot([-100,100],[100,-100],c='0.5',lw=3)
plt.scatter(y_rmax_init, y_tmax_3dy, s=300, c=x_rday, norm=norm, cmap=cmap,zorder=10)
CB=fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
       cax=cax, orientation='vertical', extend='both', label='restart_day')
plt.sca(ax)
plt.xlim(-3.5, 0.5)
plt.ylim(-1, 10)
plt.grid(True)
plt.xlabel('radial_wind_restart_day [m/s]')
plt.ylabel('tangential_wind_3rd_day [m/s]')
plt.savefig(f'{figdir}/scatter.png', dpi=200)
plt.show()




