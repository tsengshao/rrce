import numpy as np
import sys, os
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

def label_periodic(a):
  label_structure = [[0,1,0],\
                     [1,1,1],\
                     [0,1,0]]
  label_array, num_features = scimage.label(a>0.5,  structure=label_structure)
  for iy in range(label_array.shape[0]):
    if label_array[iy, 0] > 0 and label_array[iy, -1] > 0:
        label_array[label_array == label_array[iy, -1]] = label_array[iy, 0]
  for ix in range(label_array.shape[1]):
    if label_array[0, ix] > 0 and label_array[-1, ix] > 0:
        label_array[label_array == label_array[-1, ix]] = label_array[0, ix]
  new_label_table = np.sort(np.unique(label_array))
  dum = np.zeros(label_array.shape, dtype=np.int32)
  for ilab in range(new_label_table.size):
    dum[ label_array==new_label_table[ilab] ] = ilab
  label_array = np.copy(dum)
  num_features = np.unique(label_array).size-1
  return label_array, num_features

def calculate_weighted_centroid_periodic(x_coords, y_coords, weights, L_x, L_y):
    # Convert to angles
    theta_x = (2 * np.pi * np.array(x_coords)) / L_x
    theta_y = (2 * np.pi * np.array(y_coords)) / L_y
    # Compute weighted mean sine and cosine
    sum_weights = np.sum(weights)
    s_x = np.sum(weights * np.sin(theta_x)) / sum_weights
    c_x = np.sum(weights * np.cos(theta_x)) / sum_weights
    s_y = np.sum(weights * np.sin(theta_y)) / sum_weights
    c_y = np.sum(weights * np.cos(theta_y)) / sum_weights
    # Compute mean angles
    mean_theta_x = np.arctan2(s_x, c_x)
    mean_theta_y = np.arctan2(s_y, c_y)
    # Convert mean angles back to coordinates
    centroid_x = (mean_theta_x * L_x) / (2 * np.pi)
    centroid_y = (mean_theta_y * L_y) / (2 * np.pi)
    # Ensure the centroid is within the bounds
    if centroid_x < 0:
        centroid_x += L_x
    if centroid_y < 0:
        centroid_y += L_y
    return centroid_x, centroid_y

def label_centroid(a, label_array, target_input=None):
  if type(target_input) != type(None):
    target_label = np.array([target_input])
  else:
    dum = np.unique(label_array)
    target_label = dum[dum>0]
  label_left  = np.unique(label_array[:,0])[1:]
  label_top   = np.unique(label_array[0,:])[1:]
  ny, nx = label_array.shape
  center_y = np.zeros(target_label.size)
  center_x = np.zeros(target_label.size)
  for ilab in range(target_label.size):
    tlabel = target_label[ilab]
    y_coords, x_coords = np.where(label_array==tlabel)
    weights = a[y_coords, x_coords]
    cx, cy = calculate_weighted_centroid_periodic(\
      x_coords, y_coords, weights, nx, ny)
  ## method 1
  ##   shift_x   = 0
  ##   shift_y   = 0
  ##   dum_input  = np.copy(a)
  ##   dum_label  = np.copy(label_array)
  ##   if tlabel in label_left:
  ##     shift_x   = a.shape[1]//4
  ##     dum_input = np.roll(dum_input,shift_x,axis=1)
  ##     dum_label = np.roll(dum_label,shift_x,axis=1)
  ##   if tlabel in label_top:
  ##     shift_y   = a.shape[0]//2
  ##     dum_input = np.roll(dum_input,shift_y,axis=0)
  ##     dum_label = np.roll(dum_label,shift_y,axis=0)
  ##   cy, cx = scimage.center_of_mass(dum_input, dum_label, tlabel)
  ##   cx = ( cx - shift_x ) % ( nx )
  ##   cy = ( cy - shift_y ) % ( ny )
    center_x[ilab] = cx
    center_y[ilab] = cy
  center_x = np.where(center_x>nx-0.5,center_x-nx,center_x)
  center_y = np.where(center_y>ny-0.5,center_y-ny,center_y)
  if len(target_label)==1:
    return center_y[0], center_x[0]
  else:
    return center_y, center_x


comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])
#iexp = cpuid

exp = config.expList[iexp]
nt = config.totalT[iexp]
dtime = config.getExpDeltaT(exp)
print(exp, nt)
#  if exp=='RRCE_3km_f00':
#    nt = int(35*72+1)
#  else:
#    nt = int(3*72+1)

path=f"{config.dataPath}/horimsf/{exp}/horimsf-000000.nc"
nc = Dataset(path, 'r')
zz = nc.variables['zz'][:]; nz=zz.size
xc = nc.variables['xc'][:]; nx=xc.size
yc = nc.variables['yc'][:]; ny=yc.size
dx, dy = np.diff(xc)[0], np.diff(yc)[0]

iheit = np.argmin(np.abs(zz-1000))
threshold=0.

outdir=config.dataPath+"/find_center/"
os.system('mkdir -p '+outdir)

width=10
fout = open(f'{outdir}/sf_largest_0_{exp}.txt','w')
#fout = open('test.txt','w')
fout.write(\
f"""********** center info **********
variables: stream function
level    : {zz[iheit]} meter ( {iheit} / surface 0 )
threshold: {threshold}
center index start from: 0
********** center info **********
""")
fout.write(f"{'ts':>{width}s} {'mean':>{width}s} {'max':>{width}s} {'hori_size':>{width}s} {'center_x':>{width}s} {'center_y':>{width}s}\n")

for it in range(nt):
  print(exp, it)
  path=f"{config.dataPath}/horimsf/{exp}/horimsf-{it:06d}.nc"
  nc = Dataset(path, 'r')
  msf = nc.variables['sf'][0,iheit,:,:]
  label_array, num_features = label_periodic(msf>=threshold)

  if num_features>0:
    label_size  = scimage.sum_labels(np.ones(label_array.shape), \
                                     label_array, \
                                     range(1,num_features+1))
    largest_id  = np.argmax(label_size)+1
    center_y, center_x = label_centroid(msf, label_array, largest_id)
    label_max  = scimage.maximum(msf, \
                                 label_array, \
                                 largest_id)
    label_mean  = scimage.mean(msf, \
                               label_array, \
                               largest_id)
    fout.write(f"{it:{width}d} {label_mean:{width}.2f} {label_max:{width}.2f} {label_size[largest_id-1]**0.5:{width}.2f} {center_x:{width}.2f} {center_y:{width}.2f}\n")
  else:
    fout.write(f"{it:{width}d} {0:{width}.2f} {0:{width}.2f} {0:{width}.2f} {0:{width}.0f} {0:{width}.0f}\n")
fout.close()

