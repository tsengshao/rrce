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

iswhite = True

center_flag='czeta0km_positivemean'
fig_flag   ='mse'
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

it_start, it_end =  tools.get_mpi_time_span(0, nt, cpuid, nproc)

it=216
it=72*3
#for it in range(it_start, it_end):
for it in [72*3]:
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
  
  P, CB = udraw.draw_upper_pcolor(ax_top, ax_cbar, \
                        radius_1d, zc_1d, \
                        data   = data, \
                        levels = levels, \
                        cmap   = cmap, \
                        extend = 'both',\
                        title  = f'{config.expdict[exp]}',\
                        title_right  = f'{timestr}',\
                       )
  CB.ax.set_title(f'[ {varunit} ]', fontsize=15, fontweight='bold', x=1.8)
  ## C = udraw.draw_upper_hatch(ax_top,radius_1d, zc_1d,\
  ##                        data   = data_a, \
  ##                        levels = [0.5,100],\
  ##                        hat    = ['/'],\
  ##                       )

  varname = 'qi'
  varunit = nc.variables[varname].units
  data    = nc.variables[varname][0,0,:,:]
  data_a  = nc.variables[varname][0,1,:,:]
  #levels  = [0.1,0.3,0.5,1,5,10,20,30,40,50]
  levels  = np.arange(1,101,2)*1e-4

  _ = udraw.draw_upper_contour(ax_top, radius_1d, zc_1d, \
                       data=data, levels=levels, lws=[2], \
                       color='1',\
                       inline=False)

  varname = 'qc'
  varunit = nc.variables[varname].units
  data    = nc.variables[varname][0,0,:,:]
  data_a  = nc.variables[varname][0,1,:,:]
  #levels  = [0.1,0.3,0.5,1,5,10,20,30,40,50]
  levels  = np.arange(1,101,2)*1e-5

  _ = udraw.draw_upper_contour(ax_top, radius_1d, zc_1d, \
                       data=data, levels=levels, lws=[2], \
                       inline=False)

  str4=r'$10^{-4}$'
  str5=r'$10^{-5}$'
  plt.text(0.985,0.98,\
           'qi (white) : FROM '+str4+' BY 2x'+str4+' kg/kg\n'+\
           'qc (black) : FROM '+str5+' BY 2x'+str5+' kg/kg',\
           fontsize=12,\
           zorder=12,\
           ha="right", va="top",\
           transform=ax_top.transAxes,\
           color='0',\
           bbox=dict(boxstyle="square",
                     ec='0',
                     fc='1',
                     ),\
         )



  plt.sca(ax_lower)
  varname = 'cwv'
  c = '1' if not iswhite else '0'
  varunit = nc.variables[varname].units
  data   = nc.variables[varname][0,0,:]
  data_a = nc.variables[varname][0,1,:]
  C0 = udraw.draw_lower(plt.gca(), ax_top, radius_1d, \
                  data   = data, \
                  data_a = np.ones(data_a.shape), \
                  ylim   = (10, 75), \
                  yticks = [10,30,50,70], \
                  ylabel = f'cwv\n[{varunit}]',\
                  color  = c,\
                  label_color = c,\
                 )
  ax_lower_right.remove()

  
  # plt.sca(ax_lower)
  # varname = 'lh'
  # varunit = nc.variables[varname].units
  # data = nc.variables[varname][0,0,:]
  # data_a = nc.variables[varname][0,1,:]
  # C0 = udraw.draw_lower(ax_lower, ax_top, radius_1d, \
  #                 data   = data, \
  #                 data_a = np.ones(data_a.shape), \
  #                 ylim   = (0, 200), \
  #                 yticks = [0,50,100,150,], \
  #                 ylabel = f'Surface Flux\n[{varunit}]',\
  #                 color  = 'C0',\
  #                 label_color = '1',\
  #                )
  # 
  # varname = 'sh'
  # varunit = nc.variables[varname].units
  # data = nc.variables[varname][0,0,:]
  # data_a = nc.variables[varname][0,1,:]
  # C1 = udraw.draw_lower(ax_lower, ax_top, radius_1d, \
  #                 data   = data, \
  #                 data_a = np.ones(data_a.shape), \
  #                 ylim   = (0, 200), \
  #                 yticks = [0, 50, 100, 150], \
  #                 ylabel = f'Surface Flux\n [{varunit}]',\
  #                 color  = 'C1',\
  #                 label_color = '1',\
  #                )
  # plt.legend(C0+C1, ['LH', 'SH'],fontsize=10,loc='upper right')
  plt.savefig(f'{figdir}/{it:06d}.png',dpi=200, transparent=True)
  #plt.show()
  
plt.close('all')
