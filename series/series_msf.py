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
  hsf0km = np.fromfile(\
             f'{config.dataPath}/horisf/{exp}/hrisf_0.00km_{it:06d}.dat',\
             np.float32).reshape(ny,nx)
  hsf275km = np.fromfile(\
             f'{config.dataPath}/horisf/{exp}/hrisf_2.75km_{it:06d}.dat',\
             np.float32).reshape(ny,nx)

  dataWriter.toNC(f"series_hsf_{it:06d}.nc", \
    data=dict(
      sf000_max = (["time"], [np.nanmax(hsf0km)]),
      sf275_max = (["time"], [np.nanmax(hsf275km)]),
    ),
    coords=dict(
      time=[it*dtime],
    )
  )
