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
day2num = int(24*60/dtime)
nt=(nt-1)//day2num

iswhite=True

center_flag='czeta0km_positivemean'
fig_flag   ='tang_wind_one_daily'
datdir=config.dataPath+f"/axisy/{center_flag}/{exp}/"
if iswhite:
  figdir=f'./{center_flag}_white/{fig_flag}/{exp}/'
else:
  figdir=f'./{center_flag}/{fig_flag}/{exp}/'
os.system(f'mkdir -p {figdir}')

vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
zz_raw = vvmLoader.loadZZ()[:]

udraw.set_figure_defalut() 
if not iswhite:
  udraw.set_black_background()

idy_start, idy_end =  tools.get_mpi_time_span(0, nt, cpuid, nproc)

it=216
it=72*3
for idy in range(idy_start, idy_end):
#for idy in [0, 2, 9, 19, 24, 29]:
  print(idy)
  if idy > nt: continue

  fname = f'{datdir}/axmean_daily-{idy:06d}.nc'
  nc = Dataset(fname, 'r')
  radius_1d = nc.variables['radius'][:]/1000 #[km]
  zc_1d  = nc.variables['zc'][:]/1000. #[km]
  zz_1d  = zz_raw[:zc_1d.size]/1000.
 
  plt.close('all') 
  fig, ax_top, ax_cbar, ax_lower, ax_lower_right = \
      udraw.create_figure_and_axes(lower_right=False)
  
  varname = 'tang_wind'
  hei = 0.5
  idx_hei = np.argmin(np.abs(zz_1d-hei))
  hei = zz_1d[idx_hei]
  heistr=f'{zz_1d[idx_hei]*1e3:.1f}m'

  varunit = nc.variables[varname].units
  data = nc.variables[varname][0,0,:,:]
  data_a = nc.variables[varname][0,1,:,:]
  levels  = [-10, -5, -3, -2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5,  2, 3, 5, 10]
  cmap    = udraw.get_cmap('pwo')
  
  t0, t1 = idy*24, (idy+1)*24
  timestr = f'+{t0:.0f} ~ +{t1:.0f} hrs'
  if exp=='RRCE_3km_f00':
    timestr = f'{t0/24:.0f} ~ {t1/24:.0f} days'
  
  P, CB = udraw.draw_upper_pcolor(ax_top, ax_cbar, \
                        radius_1d, zz_1d, \
                        data   = data, \
                        levels = levels, \
                        cmap   = cmap, \
                        extend = 'both',\
                        # title  = f'{varname} [{varunit}]',\
                        # title_right  = f'{exp}\n{timestr}',\
                        title  = f'{config.expdict[exp]}',\
                        title_right  = f'{timestr}',\
                       )
  CB.ax.set_yticks(levels, list(map(str, levels)))
  CB.ax.tick_params(labelsize=18)
  CB.ax.set_title(f'[ {varunit} ]', fontsize=15, fontweight='bold', x=1.8)
  C = udraw.draw_upper_hatch(ax_top,radius_1d, zz_1d,\
                         data   = data_a, \
                         levels = [0.9,100],\
                         hat    = ['/'],\
                        )
  #plt.plot(radius_1d[[0,-1]], [hei, hei], '-', c='0.4', lw=2, zorder=100)
  plt.xticks(np.arange(0,551,100),np.arange(0,551,100))
  plt.xlabel('radius [km]')
  
  ax_lower.remove()
  plt.savefig(f'{figdir}/{idy:06d}.png', dpi=200, transparent=True)

plt.close('all')
