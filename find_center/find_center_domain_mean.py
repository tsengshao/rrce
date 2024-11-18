import numpy as np
import sys, os, time
sys.path.insert(1,'../')
import config
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.calculator as calc
import util.tools as tools
from util.dataWriter import DataWriter
from mpi4py import MPI
from datetime import datetime, timedelta
from netCDF4 import Dataset
import scipy.ndimage as scimage
import matplotlib.pyplot as plt
import matplotlib as mpl

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

  plt.rcParams.update({'font.size':15,
                       'axes.linewidth':2,
                       'lines.linewidth':1})

def calculate_weighted_centroid(x_coords, y_coords, weights_in, L_x, L_y):
    xx, yy = np.meshgrid(x_coords, y_coords)
    xx[weights_in<0] -= L_x
    yy[weights_in<0] -= L_y
    weights = np.abs(weights_in)
    sum_weights = np.sum(weights)
    cx = np.sum(xx*weights)/sum_weights 
    cy = np.sum(yy*weights)/sum_weights 
    print('cx, cy : ', cx, cy)
    return cx%L_x, cy%L_y


def calculate_weighted_centroid_periodic(x_coords, y_coords, weights_in, L_x, L_y, only_positive):
    # Convert to angles
    theta_x = (2 * np.pi * np.array(x_coords) / L_x )
    theta_y = (2 * np.pi * np.array(y_coords) / L_y )
    theta_x, theta_y = np.meshgrid(theta_x, theta_y)

    ##------------------------------------------------
    ## find the positive value centeroid
    ## ------
    # count postive center
    weights = np.where(weights_in>=0, weights_in, 0)
    sum_weights = np.sum(weights)
    if sum_weights>0:
      s_x = np.sum(weights * np.sin(theta_x)) / sum_weights
      c_x = np.sum(weights * np.cos(theta_x)) / sum_weights
      s_y = np.sum(weights * np.sin(theta_y)) / sum_weights
      c_y = np.sum(weights * np.cos(theta_y)) / sum_weights
      if np.abs(s_y)<5e-17: s_y = 0
      if np.abs(s_x)<5e-17: s_x = 0
      if np.abs(c_y)<5e-17: c_y = 0
      if np.abs(c_x)<5e-17: c_x = 0
      shift_theta_x = np.arctan2(s_x, c_x)
      shift_theta_y = np.arctan2(s_y, c_y)
      shift_centroid_x = (shift_theta_x * L_x) / (2 * np.pi)
      shift_centroid_y = (shift_theta_y * L_y) / (2 * np.pi)
    else:
      shift_theta_x    = 0
      shift_theta_y    = 0
      shift_centroid_x = 0
      shift_centroid_y = 0
    shift_centroid_x %= L_x
    shift_centroid_y %= L_y
    print(shift_centroid_x, shift_centroid_y)

    if only_positive: 
      # if only_positive = False, calculate positive centeroid only positive weights
      return shift_centroid_x, shift_centroid_y
   
     
    ## -------------------------------- 
    ## deal with nagitive value, let negative contribute to the distance, not value
    ## ----
    # shift reference point of theta coordinate
    theta_x = (theta_x - shift_theta_x)%(np.pi*2)
    theta_y = (theta_y - shift_theta_y)%(np.pi*2)
   
    idx=weights_in<0
    theta_x[idx] *= -1
    theta_y[idx] *= -1
    weights = np.abs(weights_in)

    # Compute weighted mean sine and cosine
    sum_weights = np.sum(weights)
    s_x = np.sum(weights * np.sin(theta_x)) / sum_weights
    c_x = np.sum(weights * np.cos(theta_x)) / sum_weights
    s_y = np.sum(weights * np.sin(theta_y)) / sum_weights
    c_y = np.sum(weights * np.cos(theta_y)) / sum_weights
    print('s_x, c_x, len_x: ',s_x, c_x, np.sqrt(s_x**2+c_x**2))
    print('s_y, c_y, len_y: ',s_y, c_y, np.sqrt(s_y**2+c_y**2))
    if np.abs(s_y)<5e-17: s_y = 0
    if np.abs(s_x)<5e-17: s_x = 0
    if np.abs(c_y)<5e-17: c_y = 0
    if np.abs(c_x)<5e-17: c_x = 0
    # Compute mean angles
    mean_theta_x = np.arctan2(s_x, c_x)
    mean_theta_y = np.arctan2(s_y, c_y)
    print('mean_theta_x:',mean_theta_x)
    print('mean_theta_y:',mean_theta_y)
 
    # Convert mean angles back to coordinates
    centroid_x = (mean_theta_x * L_x) / (2 * np.pi) + shift_centroid_x
    centroid_y = (mean_theta_y * L_y) / (2 * np.pi) + shift_centroid_y

    # negative contribution
    print('negative contribution, x:', centroid_x-shift_centroid_x)
    print('negative contribution, y:', centroid_y-shift_centroid_y)

    # Ensure the centroid is within the bounds
    centroid_x %= L_x
    centroid_y %= L_y

    return centroid_x, centroid_y

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])
str_kernel = sys.argv[2]

exp = config.expList[iexp]
nt = config.totalT[iexp]
dtime = config.getExpDeltaT(exp)
if exp=='RRCE_3km_f00':
  nt = int(35*72+1)
else:
  nt = int(3*72+1)

exp = 'rcemip_mg_square_diag2'
nt  = 217
str_kernel = '0km'
dtime = 20 #min

print(exp, nt)
if str_kernel=='0km':
  vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
  nc = vvmLoader.loadDynamic(4)
  zz = vvmLoader.loadZZ()[:-1]
else:
  path=f"{config.dataPath}/convolve/RRCE_3km_f00_15/{str_kernel}/conv-000004.nc"
  nc = Dataset(path, 'r')
  zz = nc.variables['zz'][:]; nz=zz.size
xc = nc.variables['xc'][:]; nx=xc.size
yc = nc.variables['yc'][:]; ny=yc.size
dx, dy = np.diff(xc)[0], np.diff(yc)[0]

iheit = np.argmin(np.abs(zz-1000))

str_type = f'czeta{str_kernel}_positivemean'
outdir=config.dataPath+f"/find_center/{str_type}/"
os.system('mkdir -p '+outdir)

width=15
fout = open(f'{outdir}/{exp}.txt','w')
fout.write(\
f"""********** center info **********
variables: convolution zeta with {str_kernel} gaussion kernel
level    : {zz[iheit]} meter ( {iheit} / surface 0 )
threshold: domain mean
center index start from: 0
********** center info **********
""")
fout.write(f"{'ts':>{width}s} {'mean':>{width}s} {'max':>{width}s} {'parea_ratio[%]':>{width}s} {'center_x':>{width}s} {'center_y':>{width}s} {'max_locx':>{width}s} {'max_locy':>{width}s} {'posi_mean':>{width}s}\n")

plt.close('all')
#for it in range(0,nt,int(3*60/dtime)):
#for it in [int(30*72)]:
for it in range(nt):
  print('-----', exp, it, '-----')
  if str_kernel=='0km':
    vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
    nc = vvmLoader.loadDynamic(it)
  else:
    path=f"{config.dataPath}/convolve/{exp}/{str_kernel}/conv-{it:06d}.nc"
    nc = Dataset(path, 'r')
  czeta = nc.variables['zeta'][0,iheit,:,:]


  # **** idealized test **********
  ## xic = np.arange(xc.size)
  ## yic = np.arange(yc.size)
  ## xc2,yc2 = np.meshgrid(xic,yic)

  ## czeta = np.ones(czeta.shape)*0.

  ## indata = nc.variables['zeta'][0,iheit,:,:]
  ## #czeta = np.roll(np.where(indata>5e-5, -indata, 0), -int(xc.size/6), axis=1)
  ## single = np.where(indata>5e-5, indata, 0) 
  ## czeta  = np.copy(single)
  ## czeta  += np.roll(-single,-int(xc.size*1/6),axis=1)
  ## czeta  += np.roll(-single, int(xc.size*1/6),axis=1)

  #czeta = np.where(np.abs(czeta)>5e-5, czeta, 0)
  #czeta = np.where(czeta<=-5e-5, czeta, 0)
  #czeta = np.where(czeta>=5e-5, czeta, 0)

  ## r  = np.sqrt((xc2-xc.size*2/6)**2+(yc2-yc.size*2/6)**2)
  ## czeta = np.where(r<50,1e-5,czeta)
  ## czeta *= 1e-5
  #czeta[192:,:192]=0.
  ## # czeta = np.where(r<30,30,czeta)
  ## ## czeta = np.where(r<10,40,czeta)

  ## r  = np.sqrt((xc2-xc.size*3/6)**2+(yc2-yc.size*5/6)**2)
  ## czeta = np.where(r<20,-10,czeta)

  ## # r  = np.sqrt((xc2-xc.size*3/4)**2+(yc2-yc.size/2)**2)
  ## # czeta += np.where(r<30,50,0)

  # czeta *= 1e-5
  # ******************************

  mean_value = czeta.mean()
  posi_mean_value = np.mean(czeta[czeta>0])
  mean_ix, mean_iy = calculate_weighted_centroid_periodic(\
                         x_coords   = np.arange(czeta.shape[1]), \
                         y_coords   = np.arange(czeta.shape[0]), \
                         weights_in = czeta, \
                         L_x        = czeta.shape[1], \
                         L_y        = czeta.shape[0], \
                         only_positive = True, \
                     )
  print(mean_value)
  print(posi_mean_value)
  print(mean_ix, mean_iy)
  print('90th, 99th:', np.percentile(czeta*1e5, [90,99]))

  max_iy, max_ix = np.unravel_index(np.argmax(czeta, axis=None), czeta.shape)
  max_value = czeta[max_iy, max_ix]

  hori_size = np.sum(czeta>0)/nx/ny*100

  plt.close('all')
  set_black_background()
  levels = [-100,-50,-20,-10,-5,-0.1,0.1,5,10,20,50,100]
  cmap = mpl.colors.ListedColormap(plt.cm.bwr(np.linspace(0.1,0.9,256)))
  norm = mpl.colors.BoundaryNorm(levels, cmap.N, extend='both')
  plt.figure(figsize=(10,8))
  PC=plt.pcolormesh(czeta*1e5,cmap=plt.cm.bwr,norm=norm)
  CB=plt.colorbar(PC, extend='both')
  CB.ax.set_yticks(levels)
  CB.ax.set_title(r'10$^{-5}$'+' '+r'$s^{-1}$', fontsize=12)
  plt.scatter(mean_ix, mean_iy, s=100,c='g')
  plt.plot([xc.size/2, xc.size/2],[0,yc.size], 'k-')
  plt.plot([0, xc.size],[yc.size/2,yc.size/2], 'k-')
  plt.xlim(0,xc.size)
  plt.ylim(0,yc.size)
  plt.xticks(np.linspace(0,xc.size,5), np.linspace(0,xc.size,5)*dx/1000)
  plt.yticks(np.linspace(0,yc.size,5), np.linspace(0,yc.size,5)*dy/1000)
  plt.xlabel('[km]')
  plt.ylabel('[km]')
  # plt.title('idealized triple vortex')
  # os.system(f'mkdir -p ./fig_example/')
  # plt.savefig('./fig_example/2_triple_vortex.png')

  plt.title(f'{exp} / conzeta-{str_kernel}',fontweight='bold', loc='left', fontsize=15)
  if exp=='RRCE_3km_f00':
    plt.title(f'{it*dtime/60/24:.1f}day ({it:06d})', fontweight='bold', loc='right', fontsize=12)
  else:
    plt.title(f'{it*dtime/60:.1f}hr ({it:06d})', fontweight='bold', loc='right', fontsize=12)
  figPath = f'./ani_ens_center/{exp}/'
  os.system(f'mkdir -p {figPath}')
  plt.savefig(f'{figPath}/{str_kernel}_{it:06d}.png',dpi=250)
  #plt.show(block=True)

  fout.write(f"{it:{width}d} {mean_value:{width}.4e} {max_value:{width}.4e} {hori_size:{width}.4f} {mean_ix:{width}.4e} {mean_iy:{width}.4e} {max_ix:{width}d} {max_iy:{width}d} {posi_mean_value:{width}.4e}\n")
fout.close()

