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
day2num = int(24*60/dtime)
nt=(nt-1)//day2num

iswhite = True

center_flag='czeta0km_positivemean'
fig_flag   ='mse_ccc_daily'
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

# get array coordinate
fname = f'{datdir}/axmean-{10:06d}.nc'
nc = Dataset(fname, 'r')
radius_1d = nc.variables['radius'][:]/1000 #[km]
zc_1d  = nc.variables['zc'][:]/1000 #[km]
zz_1d  = zz_raw[:zc_1d.size]/1000.
rho_1d = rho_raw[:zc_1d.size]

idy_start, idy_end =  tools.get_mpi_time_span(0, nt, cpuid, nproc)

#for idy in range(idy_start, idy_end):
for idy in [0, 2, 9, 19, 24, 29]:
  print(idy)
  if idy > nt: continue
  fname = f'{datdir}/axmean_daily-{idy:06d}.nc'
  nc = Dataset(fname, 'r')

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

  t0, t1 = idy*24, (idy+1)*24
  timestr = f'+{t0:.0f} ~ +{t1:.0f} hrs'
  if exp=='RRCE_3km_f00':
    timestr = f'{t0/24:.0f} ~ {t1/24:.0f} days'
  
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

  # varname = 'w'
  # varunit = nc.variables[varname].units
  # #data    = nc.variables[varname][0,0,:,:]
  # data    = data_w.copy()
  # levels  = [0.05, 1000]
  # _ = udraw.draw_upper_contour(ax_top, radius_1d, zc_1d, \
  #                      data=data, levels=levels, lws=[4], \
  #                      color='r', inline=False)

  varname = 'qi'
  varunit = nc.variables[varname].units
  data = nc.variables[varname][0,0,:,:]
  data_a = nc.variables[varname][0,1,:,:]
  #levels  = [0.1,0.3,0.5,1,5,10,20,30,40,50]
  levels  = np.arange(1,101,2)*1e-4

  _ = udraw.draw_upper_contour(ax_top, radius_1d, zc_1d, \
                       data=data, levels=levels, lws=[2], \
                       color='1',\
                       inline=False)

  varname = 'qc'
  varunit = nc.variables[varname].units
  data = nc.variables[varname][0,0,:,:]
  data_a = nc.variables[varname][0,1,:,:]
  #levels  = [0.1,0.3,0.5,1,5,10,20,30,40,50]
  levels  = np.arange(1,101,2)*1e-5

  _ = udraw.draw_upper_contour(ax_top, radius_1d, zc_1d, \
                       data=data, levels=levels, lws=[2], \
                       inline=False)

  varname = 'w'
  varunit = nc.variables[varname].units
  data = nc.variables[varname][0,0,:,:]
  data_a = nc.variables[varname][0,1,:,:]
  plt.sca(ax_top)
  plt.contourf(radius_1d, zz_1d, data, levels=[0.05,10000],\
               colors=['#FF005E'], alpha=0.5, zorder=100)

  str4=r'$10^{-4}$'
  str5=r'$10^{-5}$'
  str6=r'0.05'
  plt.text(0.985,0.98,\
           'qi (white) : FROM '+str4+' BY 2x'+str4+' kg/kg\n'+\
           'qc (black) : FROM '+str5+' BY 2x'+str5+' kg/kg\n'+\
           'w  (red)     : >= '+str6+' m/s',\
           fontsize=12,\
           zorder=12,\
           ha="right", va="top", ma='left',\
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
  data = nc.variables[varname][0,0,:]
  data_a = nc.variables[varname][0,1,:]
  C0 = udraw.draw_lower(plt.gca(), ax_top, radius_1d, \
                  data   = data, \
                  data_a = np.ones(data.shape), \
                  ylim   = (10, 75), \
                  yticks = [10,30,50,70], \
                  ylabel = f'cwv\n[{varunit}]',\
                  color  = c,\
                  label_color = c,\
                 )

  plt.sca(ax_lower_right)
  ### read ccc center files
  # read file, units [km / km3]
  hist_all = np.zeros(radius_1d.size-1)
  for itt in np.arange(idy*day2num, min([(idy+1)*day2num,nt*day2num])):
    fname = f'{config.dataPath}/cloud/{exp}/ccc_{itt:06d}.txt'
    objz, objy, objx, size = \
        np.loadtxt(fname, skiprows=8, usecols=[0,1,2,4], unpack=True)
    nobj = np.sum(size>0)
    sdis_ccc, _ = r_theta_series(objx, \
                                 objy, \
                                 xc.size*dx, \
                                 yc.size*dy, \
                                 centerx.iloc[itt], centery.iloc[itt],\
                                )
    hist = np.histogram(sdis_ccc, bins=radius_1d)
    hist_all += hist[0]/day2num
  co = '#FEB06F'
  #plt.hist(sdis_ccc, bins=radius_1d, color=co)
  x = (radius_1d[:-1]+radius_1d[1:])/2
  area = np.pi*(radius_1d[1:]**2-radius_1d[:-1]**2)
  plt.bar(x, hist_all/area*100, width=radius_1d[1]-radius_1d[0], color=co)
  plt.ylim(0, 0.8125)
  plt.yticks([0, 0.25, 0.5, 0.75], fontsize=13)
  #plt.ylim(0, 0.325)
  #plt.yticks([0,0.1,0.2,0.3])
  # plt.ylim(0,32.5)
  # plt.yticks([0,10,20,30])
  plt.ylabel(r'$C^3$ density'+'\n'+r'$10^{-2}$ [#/$km^{2}$]', color=co, fontsize=15)
  plt.gca().tick_params(axis='y', labelcolor=co)

  ## plt.sca(ax_lower_right)
  ## varname = 'w'
  ## c = '1' if not iswhite else '0'
  ## idxz=np.argmin(np.abs(zz_1d-5))
  ## varunit = nc.variables[varname].units
  ## #data   = nc.variables[varname][0,0,idxz,:]
  ## #data_a = nc.variables[varname][0,1,idxz,:]
  ## data   = data_w[idxz,:]
  ## co = '#FEB06F'
  ## C0 = udraw.draw_lower(plt.gca(), ax_top, radius_1d, \
  ##                 data   = data, \
  ##                 data_a = np.ones(data.shape), \
  ##                 ylim   = (-0.05, 0.1125), \
  ##                 yticks = [-0.05, 0, 0.05, 0.1], \
  ##                 ylabel = f'w\n[{varunit}]',\
  ##                 color  = co,\
  ##                 label_color = co,\
  ##                )

  plt.savefig(f'{figdir}/{idy:06d}.png',dpi=200, transparent=True)
  #plt.show()
  
plt.close('all')
