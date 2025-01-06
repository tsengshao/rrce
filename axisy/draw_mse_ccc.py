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
import util_axisymmetric as axisy

def r_theta_series(x_series, y_series, L_x, L_y, x0, y0):
    # Apply periodic boundary conditions
    dx = x_series - x0
    dy = y_series - y0
    dx = (dx + L_x / 2) % L_x - L_x / 2
    dy = (dy + L_y / 2) % L_y - L_y / 2
    distances = np.sqrt(dx**2 + dy**2)
    theta = np.arctan2(dy, dx)
    return distances, theta


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
fig_flag   ='mse_ccc'
datdir=config.dataPath+f"/axisy/{center_flag}/{exp}/"
if iswhite:
  figdir=f'./{center_flag}_white/{fig_flag}/{exp}/'
else:
  figdir=f'./{center_flag}/{fig_flag}/{exp}/'
os.system(f'mkdir -p {figdir}')

vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
zz_raw  = vvmLoader.loadZZ()[:]
rho_raw = vvmLoader.loadRHO()[:]

udraw.set_figure_defalut()
if not iswhite:
  udraw.set_black_background()

# read domain info
vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
nc = vvmLoader.loadDynamic(4)
zz = vvmLoader.loadZZ()[:-1]/1.e3
xc = nc.variables['xc'][:]/1.e3; nx=xc.size
yc = nc.variables['yc'][:]/1.e3; ny=yc.size
zc = nc.variables['zc'][:]/1.e3; ny=yc.size
dx, dy = np.diff(xc)[0], np.diff(yc)[0]

### read center and calculate distance
# read center file
center_flag='czeta0km_positivemean'
fname = f'{config.dataPath}/find_center/{center_flag}/{exp}.txt'
center_info, center_loc = axisy.read_center_file(fname, \
                            colname=['center_locx','center_locy'])
# calculate corespond x/y from r/theta
centerx = center_loc['center_locx']*dx
centery = center_loc['center_locy']*dy


it_start, it_end =  tools.get_mpi_time_span(0, nt, cpuid, nproc)

it=216
it=72*3
#for it in range(it_start, it_end):
for it in [0, 72*3]:
#for it in[0, 720, 1440, 1800, 2160]:
#for it in range(720, 2161, 72*1):
  print(it)
  fname = f'{datdir}/axmean-{it:06d}.nc'
  nc = Dataset(fname, 'r')
  radius_1d = nc.variables['radius'][:]/1000 #[km]
  zc_1d  = nc.variables['zc'][:]/1000 #[km]
  zz_1d  = zz_raw[:zc_1d.size]/1000.
  rho_1d = rho_raw[:zc_1d.size]

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

  """
  # calculate massflux and streamfunction
  varname = 'sf'
  varunit = 'kg/m/s'

  # from left to right
  data_mf = nc.variables['w'][0,0,:,:]*rho_1d[:,np.newaxis]
  data_sf = np.cumsum(data_mf, axis=1) * np.diff(radius_1d)[0]*1000

  # from right(dry) to left(moist)
  data_mf = nc.variables['w'][0,0,:,:]*rho_1d[:,np.newaxis]
  data_sf = np.cumsum(data_mf[:,::-1], axis=1) * np.diff(radius_1d)[0]*1000 * -1
  data_sf = data_sf[:,::-1]

  # data_mf = nc.variables['radi_wind'][0,0,:,:]*rho_1d[:,np.newaxis]
  # data_sf = np.cumsum(data_mf, axis=0) * np.gradient(zz_1d)[:,np.newaxis]*1000 * -1

  levels  = np.arange(-100, 101,1)
  _ = udraw.draw_upper_contour(ax_top, radius_1d, zc_1d, \
                       data=data_sf/1000., levels=levels, lws=[2], \
                       color='1',\
                       inline=False)
  # _ = udraw.draw_upper_contour(ax_top, radius_1d, zc_1d, \
  #                      data=data_mf*100., levels=levels, lws=[2], \
  #                      color='1',\
  #                      inline=False)
  """

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

  plt.sca(ax_lower_right)
  ### read ccc center files
  # read file, units [km / km3]
  fname = f'{config.dataPath}/cloud/{exp}/ccc_{it:06d}.txt'
  objz, objy, objx, size = np.loadtxt(fname, skiprows=8, usecols=[0,1,2,4], unpack=True)
  nobj = np.sum(size>0)

  sdis_ccc, _ = r_theta_series(objx, \
                               objy, \
                               xc.size*dx, \
                               yc.size*dy, \
                               centerx.iloc[it], centery.iloc[it],\
                              )
  co = '#FEB06F'
  plt.hist(sdis_ccc, bins=radius_1d, color=co)
  plt.ylim(0, 32.5)
  plt.yticks([0,10,20,30])
  plt.ylabel(r'$C^3$'+' [#]', color=co)
  plt.gca().tick_params(axis='y', labelcolor=co)

  plt.savefig(f'{figdir}/{it:06d}.png',dpi=200, transparent=True)
  #plt.show()
  
plt.close('all')
