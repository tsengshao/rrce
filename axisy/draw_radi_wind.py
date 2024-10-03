import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(1,'../')
import config
from netCDF4 import Dataset
import matplotlib as mpl
from mpi4py import MPI
import util_draw as udraw

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

udraw.set_figure_defalut() 
udraw.set_black_background()
 

it=216
it=72*3
for it in range(nt):
#for it in [72*3]:
  print(it)
  fname = f'{datdir}/axmean-{it:06d}.nc'
  nc = Dataset(fname, 'r')
  radius_1d = nc.variables['radius'][:]/1000 #[km]
  zc_1d  = nc.variables['zc'][:]/1000 #[km]
 
  plt.close('all') 
  fig, ax_top, ax_cbar, ax_lower, ax_lower_right = \
      udraw.create_figure_and_axes()
  
  varname = 'radi_wind'
  varunit = nc.variables[varname].units
  data = nc.variables[varname][0,0,:,:]
  data_a = nc.variables[varname][0,1,:,:]
  levels  = np.arange(-5,5.1,1)
  cmap    = udraw.get_cmap('pwo')
  
  _ = udraw.draw_upper_pcolor(ax_top, ax_cbar, \
                        radius_1d, zc_1d, \
                        data   = data, \
                        levels = levels, \
                        cmap   = cmap, \
                        extend = 'both',\
                        title  = f'{varname} [{varunit}]',\
                        title_right  = f'{exp}\n{(dtime*it)/60:.1f}hr',\
                       )
  C = udraw.draw_upper_hatch(ax_top,radius_1d, zc_1d,\
                         data   = data_a, \
                         levels = [0.5,100],\
                         hat    = ['//'],\
                        )
  
  
  plt.sca(ax_lower)
  varname = 'cwv'
  varunit = nc.variables[varname].units
  data = nc.variables[varname][0,0,:]
  data_a = nc.variables[varname][0,1,:]
  _ = udraw.draw_lower(ax_lower, ax_top, radius_1d, \
                  data   = data, \
                  data_a = data_a, \
                  ylim   = (20, 65), \
                  yticks = [20, 35, 50], \
                  ylabel = f'{varname} [{varunit}]',\
                  color  = '1',\
                 )
  
  varname = 'radi_wind'
  varunit='m/s'
  idxz=8
  heistr='1km'
  _ = udraw.draw_lower(ax_lower_right, ax_top, radius_1d, \
                  data   = nc.variables[varname][0,0,idxz,:], \
                  data_a = nc.variables[varname][0,1,idxz,:], \
                  ylim   = (-3,3), \
                  yticks = [-3, -1, 1], \
                  ylabel = f'{varname}\n@{heistr} [{varunit}]',\
                  color  = 'C1',\
                 )
  plt.savefig(f'{figdir}/{it:06d}.png',dpi=200)

plt.close('all')
