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
fig_flag   ='mse'
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
#for it in [72*3]:
#for it in[1]:
  print(it)
  fname = f'{datdir}/axmean-{it:06d}.nc'
  nc = Dataset(fname, 'r')
  radius_1d = nc.variables['radius'][:]/1000 #[km]
  zc_1d  = nc.variables['zc'][:]/1000 #[km]
  zz_1d  = zz_raw[:zc_1d.size]/1000.
  
 
  plt.close('all') 
  fig, ax_top, ax_cbar, ax_lower, ax_lower_right = \
      udraw.create_figure_and_axes(lower_right=True)
  ax_lower.set_zorder(10)
  ax_lower.patch.set_visible(False)
  
  varname = 'mse'
  varunit = nc.variables[varname].units
  data = nc.variables[varname][0,0,:,:]
  data_a = nc.variables[varname][0,1,:,:]
  levels  = np.arange(305,350,2)
  cmap    = udraw.get_cmap('colorful')
  
  timestr = f'{(dtime*it)/60:.1f}hr'
  if exp=='RRCE_3km_f00': timestr = f'{(dtime*it)/60/24:.1f}day'
  
  _ = udraw.draw_upper_pcolor(ax_top, ax_cbar, \
                        radius_1d, zc_1d, \
                        data   = data, \
                        levels = levels, \
                        cmap   = cmap, \
                        extend = 'both',\
                        title  = f'{varname.upper()} [{varunit}]',\
                        title_right  = f'{exp}\n{timestr}',\
                       )
  ## C = udraw.draw_upper_hatch(ax_top,radius_1d, zc_1d,\
  ##                        data   = data_a, \
  ##                        levels = [0.5,100],\
  ##                        hat    = ['/'],\
  ##                       )

  varname = 'qc'
  varunit = nc.variables[varname].units
  data    = nc.variables[varname][0,0,:,:]
  data_a  = nc.variables[varname][0,1,:,:]
  levels  = np.arange(1,50.1,1)

  _ = udraw.draw_upper_contour(ax_top, radius_1d, zc_1d, \
                       data=data*1e5, levels=levels, lws=[1], \
                       inline=False, annotation=f'{varname} '+'['+r'$10^{-5}$'+f' {varunit}] ')

  C = udraw.draw_upper_hatch(ax_top,radius_1d, zc_1d,\
                         data   = data_a, \
                         levels = [0.1,100],\
                         hat    = ['/////'],\
                         annotation_y = -0.07,\
                         annotation   = 'qc '
                        )

  plt.sca(ax_lower_right)
  varname = 'cwv'
  varunit = nc.variables[varname].units
  data   = nc.variables[varname][0,0,:]
  data_a = nc.variables[varname][0,1,:]
  C0 = udraw.draw_lower(ax_lower_right, ax_top, radius_1d, \
                  data   = data, \
                  data_a = np.ones(data_a.shape), \
                  ylim   = (20, 60), \
                  yticks = [20,30,40,50,], \
                  ylabel = f'cwv\n[{varunit}]',\
                  color  = '1',\
                  label_color = '1',\
                 )

  
  plt.sca(ax_lower)
  varname = 'lh'
  varunit = nc.variables[varname].units
  data = nc.variables[varname][0,0,:]
  data_a = nc.variables[varname][0,1,:]
  C0 = udraw.draw_lower(ax_lower, ax_top, radius_1d, \
                  data   = data, \
                  data_a = np.ones(data_a.shape), \
                  ylim   = (0, 200), \
                  yticks = [0,50,100,150,], \
                  ylabel = f'Surface Flux\n[{varunit}]',\
                  color  = 'C0',\
                  label_color = '1',\
                 )
  
  varname = 'sh'
  varunit = nc.variables[varname].units
  data = nc.variables[varname][0,0,:]
  data_a = nc.variables[varname][0,1,:]
  C1 = udraw.draw_lower(ax_lower, ax_top, radius_1d, \
                  data   = data, \
                  data_a = np.ones(data_a.shape), \
                  ylim   = (0, 200), \
                  yticks = [0, 50, 100, 150], \
                  ylabel = f'Surface Flux\n [{varunit}]',\
                  color  = 'C1',\
                  label_color = '1',\
                 )
  plt.legend(C0+C1, ['LH', 'SH'],fontsize=10,loc='upper right')
  plt.savefig(f'{figdir}/{it:06d}.png',dpi=200)
  
plt.close('all')
