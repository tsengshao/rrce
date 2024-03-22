import numpy as np
import sys, os
sys.path.insert(1,'../')
import config
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.calculator as calc
import util.tools as tools
from util.dataWriter import DataWriter
from mpi4py import MPI
import scipy as sci

# ========== Gaussian Kernel =========
def getGaussianWeight(kernelSize, std=1, normalize=True):
    gaussian1D = sci.signal.windows.gaussian(kernelSize, std)
    gaussian2D = np.outer(gaussian1D, gaussian1D)
    if normalize:
        gaussian2D /= gaussian2D.sum()
    return gaussian2D

def getExpandSize(weight):
    if weight.shape[0] % 2 == 1:
        expandSize = (weight.shape[0] - 1) // 2
    else:
        expandSize = (weight.shape[0] - 1) // 2 + 1
    return expandSize

def getGaussianConvolve(data, kernel, method="fft"):
    """method: direct / fft (error: O(1e-16))"""
    ny, nx = data.shape[1], data.shape[2]
    expandLength = min(nx, ny)
    expandSize = getExpandSize(kernel)
    expandData = np.pad(data,
                        pad_width=((0, 0),
                                   (expandLength//2, expandLength//2),
                                   (expandLength//2, expandLength//2)),
                        mode="wrap")
    convData = np.zeros(shape=data.shape)

    for i in range(data.shape[0]):
        #print(i, data.shape[0])
        convData[i] = sci.signal.correlate(expandData[i], kernel, method=method)[2*expandSize:-2*expandSize+1, 2*expandSize:-2*expandSize+1]
    return convData

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])

exp = config.expList[iexp]
nt = config.totalT[iexp]
print(exp, nt)

vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
thData = vvmLoader.loadDynamic(0)
nz, ny, nx = thData['zeta'][0].shape
xc, yc, zc = thData['xc'][:], thData['yc'][:], thData['zc'][:]
dx, dy = np.diff(xc)[0], np.diff(yc)[0]
rho = vvmLoader.loadRHO()[:-1]
rhoz = vvmLoader.loadRHOZ()[:-1]
zz = vvmLoader.loadZZ()[:-1]

klength=100 #km

idxTS, idxTE = tools.get_mpi_time_span(0, nt, cpuid, nproc)
print(cpuid, idxTS, idxTE, idxTE-idxTS)

outdir=config.dataPath+"/convolve/"+exp+f'/{klength}km/'
os.system('mkdir -p '+outdir)
dataWriter = DataWriter(outdir)

kernel=getGaussianWeight(nx, std=klength/6/3)

for it in range(idxTS, idxTE):
  print(it)
  dyData = vvmLoader.loadDynamic(it)
  zeta = getGaussianConvolve(dyData['zeta'][0,:,:], kernel)
  u = getGaussianConvolve(dyData['u'][0,:,:], kernel)
  v = getGaussianConvolve(dyData['v'][0,:,:], kernel)
  
  dim4d=['time', 'zc', 'yc', 'xc']
  dataWriter.toNC(f"conv-{it:06d}.nc", \
    data=dict(
      zeta  =(dim4d, zeta[np.newaxis,:,:,:], {'units':'s-1'}),\
      u     =(dim4d, u[np.newaxis,:,:,:], {'units':'m/s'}),\
      v     =(dim4d, v[np.newaxis,:,:,:], {'units':'m/s'})
    ),
    coords=dict(
      time=np.ones(1),
      zc=(['zc'], zc),
      yc=(['yc'], yc),
      xc=(['xc'], xc),
    )
  )

