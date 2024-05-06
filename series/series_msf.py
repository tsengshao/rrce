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

nt = config.totalT[iexp]
exp = config.expList[iexp]
dtime = config.getExpDeltaT(exp)    #minutes

outdir=config.dataPath+f"/series/{exp}/"
print(outdir)

nc = Dataset(f'{config.dataPath}/horimsf/{exp}/horimsf-000010.nc', 'r')
msf = nc.variables['sf'][0,:,:,:]
nz, ny, nz = msf.shape
xc, yc, zz = nc.variables['xc'][:], nc.variables['yc'][:], nc.variables['zz'][:]

idxTS, idxTE = tools.get_mpi_time_span(0, nt, cpuid, nproc)
print(cpuid, idxTS, idxTE, idxTE-idxTS)
  
dataWriter = DataWriter(outdir)
for it in range(idxTS, idxTE):
  print(exp, it)
  time = it*dtime #minutes
  nc = Dataset(f'{config.dataPath}/horimsf/{exp}/horimsf-{it:06d}.nc', 'r')
  msf = np.nanmax(nc.variables['sf'][0,:,:,:], axis=(1,2))

  dataWriter.toNC(f"series_hsf_{it:06d}.nc", \
    data=dict(
      maxsf = (["time", "zz"], [msf]),
    ),
    coords=dict(
      time = [it*dtime],
      zz   = zz,
    )
  )
