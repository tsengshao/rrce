import matplotlib.pyplot as plt
import matplotlib as mpl
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
import numba
from netCDF4 import Dataset
import util_axisymmetric as axisy


comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])

nt = config.totalT[iexp]
exp = config.expList[iexp]
if exp!='RRCE_3km_f00': nt=217
if (cpuid==0): print(exp, nt)

center_flag='czeta0km_positivemean'
outdir=config.dataPath+f"/axisy/{center_flag}/{exp}/"
os.system(f'mkdir -p {outdir}')

# read VVM coordinate
vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
thData = vvmLoader.loadThermoDynamic(0)
nz, ny, nx = thData['qv'][0].shape
xc, yc, zc = thData['xc'][:], thData['yc'][:], thData['zc'][:]
dx, dy = np.diff(xc)[0], np.diff(yc)[0]
rho = vvmLoader.loadRHO()[:-1]
pibar = vvmLoader.loadPIBAR()[:-1]
idxTOP = np.argmin(np.abs(zc-18000))
zc = zc[:idxTOP]
nz = zc.size


# create r/theta coordinate
radius_1d = np.arange(0, (nx*dx)//2, dx) + dx/2
theta_1d  = np.arange(0,360,0.5) + 0.25
theta_1d  = theta_1d*np.pi/180.
theta, radius = np.meshgrid(theta_1d, radius_1d)

# read center file
fname = f'{config.dataPath}/find_center/{center_flag}/{exp}.txt'
center_info, center_loc = axisy.read_center_file(fname, \
                            colname=['center_x','center_y'])


it = 216

## # create nc file
## outNC = Dataset(f'{outdir}/axisy-{it:06d}.nc', 'w', format='NTECDF4')
## time_nc  = outNC.createDimension("time", None)
## zc_nc = outNC.createDimension("zc", nz)
## r_nc  = outNC.createDimension("radius", radius_1d.size)
## th_nc = outNC.createDimension("theta", theta_1d.size)
## 



# calculate corespond x/y from r/theta
cx = center_loc['center_x'].iloc[it]*dx
cy = center_loc['center_y'].iloc[it]*dy
x_polar, y_polar  =  axisy.convert_rth2xy(\
                      radius, theta, \
                      cx, cy, \
                      nx*dx, ny*dy, \
                     )
sdis, stheta = axisy.compute_shortest_distances_vectorized(xc, yc, cx, cy)


# read data
dataCollector = axisy.data_collector(exp, it, idztop=idxTOP+1)
radial_dict, tangential_dict = dataCollector.get_radial_and_tangential_wind(stheta)
data_dict = tangential_dict

# regrid data
if data_dict['ndim']=='3d':
  rawdata = data_dict['data'][8,:,:]
elif data_dict['ndim']=='2d':
  rawdata = data_dict['data']
data_polar = axisy.regrid_data_c2p(xc_1d = xc,\
                             yc_1d = yc,\
                             rawdata = rawdata,\
                             x_polar = x_polar,\
                             y_polar = y_polar,\
                            )

############ quick view
plt.figure()
plt.scatter(x_polar/1000,y_polar/1000,c=radius/1000,s=1)
plt.colorbar()
plt.title('radius')
plt.figure()
plt.scatter(x_polar/1000,y_polar/1000,c=theta*180/np.pi,s=1)
plt.colorbar()
plt.title('theta')

# draw
fig = plt.figure()
bounds = np.arange(20, 60, 2)
bounds = np.linspace(-20, 20, 21)
bounds = np.arange(0, 300, 20)
bounds = np.arange(-250, 251, 10)
bounds = np.arange(-5, 5.1, 1)

cmap   = plt.cm.jet
cmap = plt.cm.RdYlBu

norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=256, extend='both')

c = plt.pcolormesh(xc/1000, yc/1000, rawdata, norm=norm, cmap=cmap)
cb = plt.colorbar(c)
plt.scatter(cx/1000, cy/1000,s=10,c=['k'])

plt.figure()
plt.scatter(x_polar/1000, y_polar/1000, c=data_polar, s=1, cmap=cmap, norm=norm)
plt.colorbar()
plt.scatter(cx/1000, cy/1000,s=10,c=['k'])

plt.figure()
plt.pcolormesh(radius/1000,theta,data_polar,norm=norm,cmap=cmap)
plt.colorbar()
plt.show()



