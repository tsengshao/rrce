import numpy as np
import sys, os
sys.path.insert(1,'../')
import config
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.calculator as calc
import util.tools as tools
from util.dataWriter import DataWriter
from netCDF4 import Dataset
from mpi4py import MPI
from datetime import datetime, timedelta

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])
klenstr = sys.argv[2] if len(sys.argv)>2 else '100km'
tlev    = 1.5 #km

nt = config.totalT[iexp]
exp = config.expList[iexp]
dtime = config.getExpDeltaT(exp)    #minutes

outdir=config.dataPath+f"/series/{exp}/{klenstr}/"
print(outdir)

vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
thData = vvmLoader.loadThermoDynamic(0)
nz, ny, nx = thData['qv'][0].shape
xc, yc, zc = thData['xc'], thData['yc'], thData['zc']
rho = vvmLoader.loadRHO()[:-1]
zz = vvmLoader.loadZZ()[:-1]

idxTS, idxTE = tools.get_mpi_time_span(0, nt, cpuid, nproc)
print(cpuid, idxTS, idxTE, idxTE-idxTS)
  
dataWriter = DataWriter(outdir)
for it in range(idxTS, idxTE):
  print(exp, it)
  time = it*dtime #minutes

  nc  = Dataset(f'{config.dataPath}/convolve/{exp}/{klenstr}/conv-{it:06d}.nc', 'r')
  zz   = nc.variables['zz'][:]
  izz = np.argmin(np.abs(zz-tlev))
  zeta = nc.variables['zeta'][0,izz,:,:]

  dataWriter.toNC(f"series_conv_{it:06d}.nc", \
    data=dict(
      max_zeta    = (["time"], [np.max(zeta)]),
      area_zeta1  = (["time"], [np.sum(zeta>=1e-4)*9], {'units':'km','threshold':1e-4}),
      area_zeta2  = (["time"], [np.sum(zeta>=1e-3)*9], {'units':'km','threshold':1e-3}),
    ),
    coords=dict(
      time=[it*dtime],
    ),
    attrs=dict(
      discription=f'zeta field at {tlev:.2f}km under {klenstr} gassiuan convolution'
    ),
  )
