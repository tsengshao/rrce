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
zz_raw = vvmLoader.loadZZ()[:]

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
#for it in [72*3]:
for it in[0, 720, 1440, 1800, 2160]:
  print(it)
  fname = f'{datdir}/axmean-{it:06d}.nc'
  nc = Dataset(fname, 'r')
  radius_1d = nc.variables['radius'][:]/1000 #[km]
  zc_1d  = nc.variables['zc'][:]/1000 #[km]
  zz_1d  = zz_raw[:zc_1d.size]/1000.

  # historgram array
  #xbins = radius_1d.copy()
  xbins = np.arange(0, radius_1d.max()+0.001, 25)
  ybins = np.arange(0,6.001,0.2)
 
  ### read ccc center files
  # read file, units [km / km3]
  fname = f'{config.dataPath}/cloud/{exp}/ccc_{it:06d}.txt'
  objz, objy, objx, objsize = np.loadtxt(fname, skiprows=8, usecols=[0,1,2,4], unpack=True)
  nobj = np.sum(objsize>0)
  if nobj <= 0: continue
  objsize = np.log10(objsize)

  sdis_ccc, sthe_ccc = r_theta_series(objx, \
                                      objy, \
                                      xc.size*dx, \
                                      yc.size*dy, \
                                      centerx.iloc[it], centery.iloc[it],\
                                     )
  hist, _, _ = np.histogram2d(sdis_ccc, objsize, bins=(xbins,ybins))
  hist = hist.T
  hist = np.where(hist>0, hist, np.nan)

  plt.close('all') 
  fig, ax = plt.subplots(figsize=(10,8))

  levels = np.arange(0, 51, 2)
  norm = mpl.colors.BoundaryNorm(boundaries=levels, \
            ncolors=256, extend='max')

  plt.sca(ax)
  x = (xbins[:-1]+xbins[1:])/2
  y = (ybins[:-1]+ybins[1:])/2
  plt.pcolormesh(x, y, hist, norm=norm, cmap=plt.cm.jet)
  plt.colorbar()
  plt.ylim(ybins.min(), ybins.max())
  plt.ylabel('size '+r'$10^x$')
  plt.title(f'{it/72:.2f} days', loc='left', fontweight='bold')

  plt.savefig(f'{figdir}/{it:06d}.png',dpi=200, transparent=True)
  plt.show()
  
plt.close('all')
