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

center_flag='czeta0km_positivemean'
fig_flag   ='tang_wind'
datdir=config.dataPath+f"/axisy/{center_flag}/{exp}/"
figdir=f'./{center_flag}/{fig_flag}/{exp}/'
os.system(f'mkdir -p {figdir}')

vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
zz_raw = vvmLoader.loadZZ()[:]

udraw.set_figure_defalut() 
udraw.set_black_background()

it_start, it_end =  tools.get_mpi_time_span(0, nt, cpuid, nproc)

it=216
it=72*3
for it in range(it_start, it_end):
#for it in range(nt):
#for it in [72*3]:
  print(it)
  fname = f'{datdir}/axmean-{it:06d}.nc'
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
  levels  = np.arange(-2,2.1,0.2)
  cmap    = udraw.get_cmap('pwo')
  
  timestr = f'{(dtime*it)/60:.1f}hr'
  if exp=='RRCE_3km_f00': timestr = f'{(dtime*it)/60/24:.1f}day'
  
  P, CB = udraw.draw_upper_pcolor(ax_top, ax_cbar, \
                        radius_1d, zz_1d, \
                        data   = data, \
                        levels = levels, \
                        cmap   = cmap, \
                        extend = 'both',\
                        title  = f'{varname} [{varunit}]',\
                        title_right  = f'{exp}\n{timestr}',\
                       )
  C = udraw.draw_upper_hatch(ax_top,radius_1d, zz_1d,\
                         data   = data_a, \
                         levels = [0.5,100],\
                         hat    = ['//'],\
                        )
  plt.plot(radius_1d[[0,-1]], [hei, hei], '-', c='0.4', lw=2, zorder=100)
  
  
  plt.sca(ax_lower)
  ## varname = 'cwv'
  ## varunit = nc.variables[varname].units
  ## data = nc.variables[varname][0,0,:]
  ## data_a = nc.variables[varname][0,1,:]
  ## _ = udraw.draw_lower(ax_lower, ax_top, radius_1d, \
  ##                 data   = data, \
  ##                 data_a = data_a, \
  ##                 ylim   = (20, 65), \
  ##                 yticks = [20, 35, 50], \
  ##                 ylabel = f'{varname} [{varunit}]',\
  ##                 color  = '1',\
  ##                )
  
  varname = 'tang_wind'
  varunit='m/s'
  idx_hei = np.argmin(np.abs(zz_1d-0.5))
  heistr0=f'{zz_1d[idx_hei]*1e3:.1f}m'
  C0 = udraw.draw_lower(ax_lower, ax_top, radius_1d, \
                  data   = nc.variables[varname][0,0,idx_hei,:], \
                  data_a = nc.variables[varname][0,1,idx_hei,:], \
                  ylim   = (-3,3), \
                  yticks = [-1.5,0,1.5], \
                  ylabel = f'{varname} [{varunit}]',\
                  label  = f'@{heistr0}',\
                  color  = 'C0',\
                  label_color  = '1',\
                 )

  varname = 'tang_wind'
  varunit='m/s'
  idx_hei = np.argmin(np.abs(zz_1d-0.2))
  heistr1=f'{zz_1d[idx_hei]*1e3:.1f}m'
  C1 = udraw.draw_lower(ax_lower, ax_top, radius_1d, \
                  data   = nc.variables[varname][0,0,idx_hei,:], \
                  data_a = nc.variables[varname][0,1,idx_hei,:], \
                  ylim   = (-3,3), \
                  yticks = [-1.5,0,1.5], \
                  ylabel = f'{varname} [{varunit}]',\
                  label  = f'@{heistr1}',\
                  color  = 'C1',\
                  label_color  = '1',\
                 )
  plt.legend([C0[0],C1[0]], [f'@{heistr0}', f'@{heistr1}'], loc='upper right', fontsize=10)
  plt.savefig(f'{figdir}/{it:06d}.png',dpi=200)

plt.close('all')
