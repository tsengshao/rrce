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
idxTOP = np.argmin(np.abs(zc-18000))+1
zc = zc[:idxTOP]
nz = zc.size


# create r/theta coordinate
radius = np.arange(0, (nx*dx)//1.5, dx) + dx/2
theta  = np.arange(0,360,0.5) + 0.25
theta  = theta*np.pi/180.
theta, radius = np.meshgrid(theta, radius)

# read center file
fname = f'{config.dataPath}/find_center/{center_flag}/{exp}.txt'
center_info, center_loc = axisy.read_center_file(fname, \
                            colname=['center_x','center_y'])


it = 216 

# calculate corespond x/y from r/theta
cx = center_loc['center_x'].iloc[it]*dx
cy = center_loc['center_y'].iloc[it]*dy
x_polar, y_polar  =  axisy.convert_rth2xy(\
                      radius, theta, \
                      cx, cy, \
                      nx*dx, ny*dy, \
                     )
sdis, stheta = axisy.compute_shortest_distances_vectorized(xc, yc, cx, cy)


# read cwv data
nc = Dataset(f'{config.dataPath}/wp/{exp}/wp-{it:06d}.nc', 'r')
cwv = nc.variables['cwv'][0].data #kg/m2
lwp = nc.variables['lwp'][0].data #kg/m2
iwp = nc.variables['iwp'][0].data #kg/m2

# regrid data
rawdata = sdis
data_polar = axisy.regrid_data_c2p(xc_1d = xc,\
                             yc_1d = yc,\
                             rawdata = rawdata,\
                             x_polar = x_polar,\
                             y_polar = y_polar,\
                            )

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
bounds = np.linspace(10, 60, 26)
bounds = np.arange(0, 1150*1e3, 3e3)
norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=bounds.size+2, extend='both')

c = plt.pcolormesh(xc/1000, yc/1000, rawdata, norm=norm, cmap=plt.cm.jet)
cb = plt.colorbar(c)
plt.scatter(cx/1000, cy/1000,s=10,c=['k'])

plt.figure()
plt.scatter(x_polar/1000, y_polar/1000, c=data_polar, s=1, cmap=plt.cm.jet, norm=norm)
plt.colorbar()
plt.scatter(cx/1000, cy/1000,s=10,c=['k'])

plt.figure()
plt.pcolormesh(radius/1000,theta,data_polar,norm=norm,cmap=plt.cm.jet)
plt.colorbar()
plt.contour(radius/1000,theta,(data_polar-radius)<1,levels=[0])
plt.show()











