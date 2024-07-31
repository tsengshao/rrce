import matplotlib.pyplot as plt
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

def compute_shortest_distances_vectorized(x_coords, y_coords, x0, y0):
    width = x_coords[-1]-x_coords[0] 
    height = y_coords[-1]-y_coords[0] 
    #dx = np.minimum(np.abs(x_coords - x0), \
    #                width - np.abs(x_coords - x0))
    #dy = np.minimum(np.abs(y_coords[:, np.newaxis] - y0), \
    #                height - np.abs(y_coords[:, np.newaxis] - y0))
    # Apply periodic boundary conditions
    dx = x_coords - x0
    dy = y_coords[:,np.newaxis] - y0
    dx = (dx + width / 2) % width - width / 2
    dy = (dy + height / 2) % height - height / 2
    distances = np.sqrt(dx**2 + dy**2)
    theta = np.arctan2(dy, dx)

    return distances, theta

def convert_uv2rt(u,v,theta):
    u_r  = u*np.cos(theta)+v*np.sin(theta)
    u_th = -u*np.sin(theta)+v*np.cos(theta)
    return u_r, u_th


comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])

nt = config.totalT[iexp]
exp = config.expList[iexp]
if exp!='RRCE_3km_f00': nt=217
if (cpuid==0): print(exp, nt)

center_flag='sf_largest_0'

outdir=config.dataPath+f"/distance/{center_flag}/{exp}/"

# read VVM coordinate
vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
thData = vvmLoader.loadThermoDynamic(0)
nz, ny, nc = thData['qv'][0].shape
xc, yc, zc = thData['xc'][:], thData['yc'][:], thData['zc'][:]
rho = vvmLoader.loadRHO()[:-1]

# read location of maximum SF
## locfile=config.dataPath+f"/horisf/{exp}/maxloc_hrisf_0.00km.txt"
## locts, locx, locy = np.loadtxt(locfile, skiprows=1, usecols=[0,1,2], unpack=True, delimiter=',', dtype=int)
locfile=config.dataPath+f"/find_center/{center_flag}_{exp}.txt"
locts, locx, locy = np.loadtxt(locfile, skiprows=7, usecols=[0,4,5], unpack=True)
locts = locts.astype(int)
locx  = xc[0] + locx*(xc[1]-xc[0])
locy  = yc[0] + locy*(yc[1]-yc[0])

# mpi for time
idxTS, idxTE = tools.get_mpi_time_span(0, nt, cpuid, nproc)
print(cpuid, idxTS, idxTE, idxTE-idxTS)

dataWriter = DataWriter(outdir)
for it in range(idxTS, idxTE):
  if locts[it]!=it: sys.exit('!!ERROR!!: inconsistent timestep')
  #x0, y0 = xc[locx[it]], xc[locy[it]]
  x0, y0 = locx[it], locy[it]
  #print(it, x0, y0)
  distances, theta = compute_shortest_distances_vectorized(xc, yc, x0, y0)
  #u=np.ones(distances.shape)
  #v=np.zeros(distances.shape)+1
  #u_radial, u_tangential = convert_uv2rt(u,v,theta)
  if it==0:
    distances.fill(0)
    theta.fill(0)
  
  dataWriter.toNC(f"dis-{it:06d}.nc", \
    data=dict(
      dis=(["time", "yc", "xc"], \
           distances[np.newaxis, :, :]/1000, \
           dict(height='0.0km', locx=locx[it], locy=locy[it], unit='km')\
          ),\
      angle=(["time", "yc", "xc"], \
           theta[np.newaxis, :, :], \
          ),\
    ),
    coords=dict(
      time=np.ones(1),
      yc=(['yc'], yc),
      xc=(['xc'], xc),
    )
  )



fout = open(f'{outdir}/../dis_{exp}.ctl','w')
ctl=f"""
DSET ^./{exp}/dis-%tm6.nc
DTYPE netcdf
OPTIONS template
TITLE C.Surface variables
UNDEF 99999.
CACHESIZE 10000000
XDEF 384 LINEAR 0. .027027
YDEF 384 LINEAR 0. .027027
ZDEF 1 LEVELS 1000
TDEF {nt} LINEAR 01JAN1998 {config.getExpDeltaT(exp)}mn
VARS 2
  dis=>dis 0 t,y,x dis
  angle=>angle 0 t,y,x angle
ENDVARS
"""
fout.write(ctl)
fout.close()

