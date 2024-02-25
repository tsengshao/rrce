import numpy as np
import sys, os
sys.path.insert(1,'../')
import config
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.calculator as calc
import util.tools as tools
from util.dataWriter import DataWriter
from mpi4py import MPI

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])

nt = config.totalT[iexp]
exp = config.expList[iexp]
if (cpuid==0): print(exp, nt)

outdir="../../data/cwv/"+exp+'/'

vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
thData = vvmLoader.loadThermoDynamic(0)
nz, ny, nc = thData['qv'][0].shape
xc, yc, zc = thData['xc'], thData['yc'], thData['zc']
rho = vvmLoader.loadRHO()[:-1]

idxTS, idxTE = tools.get_mpi_time_span(0, nt, cpuid, nproc)
print(cpuid, idxTS, idxTE, idxTE-idxTS)
dataWriter = DataWriter(outdir)

for it in range(idxTS, idxTE):
  thData = vvmLoader.loadThermoDynamic(it)
  qv = thData['qv'][0] #3d, kg/kg
  cwv = np.trapz(qv*rho[:,np.newaxis,np.newaxis], x=zc, axis=0)
  if (cpuid==0):
    print('it=',it, ', cwv_range=(%.2f, %.2f)'%(cwv.min(), cwv.max()))

  dataWriter.toNC(f"cwv-{it:06d}.nc", \
    data=dict(
      cwv=(["time", "yc", "xc"], cwv[np.newaxis, :, :]),
    ),
    coords=dict(
      time=np.ones(1),
      yc=(['yc'], yc),
      xc=(['xc'], xc),
    )
  )
