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

idxTS, idxTE = tools.get_mpi_time_span(0, nt, cpuid, nproc)
print(cpuid, idxTS, idxTE, idxTE-idxTS)
  
dataWriter = DataWriter(outdir)
for it in range(idxTS, idxTE):
  print(exp, it)
  time = it*dtime #minutes
  dyData = vvmLoader.loadDynamic(it)
  u = dyData['u'][0, 0] # 2d, first layer
  v = dyData['v'][0, 0] # 2d, first layer

  nc  = Dataset(f'{config.dataPath}/wp/{exp}/wp-{it:06d}.nc', 'r')
  cwv = nc.variables['cwv'][0,:,:]
  lwp = nc.variables['lwp'][0,:,:]
  iwp = nc.variables['iwp'][0,:,:]

  hsf0km = np.fromfile(\
             f'{config.dataPath}/horisf/{exp}/hrisf_0.00km_{it:06d}.dat',\
             np.float32).reshape(ny,nx)
  hsf275km = np.fromfile(\
             f'{config.dataPath}/horisf/{exp}/hrisf_2.75km_{it:06d}.dat',\
             np.float32).reshape(ny,nx)

  dataWriter.toNC(f"series_{it:06d}.nc", \
    data=dict(
      cwv_mean  = (["time"], [np.mean(cwv)]),
      lwp_mean  = (["time"], [np.mean(lwp)]),
      iwp_mean  = (["time"], [np.mean(iwp)]),
      cwv_std   = (["time"], [np.std(cwv)]),
      lwp_std   = (["time"], [np.std(lwp)]),
      iwp_std   = (["time"], [np.std(iwp)]),
      maxwind   = (["time"], [np.max((u**2+v**2)**0.5)]),
      dryfrac   = (["time"], [np.sum(cwv<30)/cwv.size]),
      sf000_max = (["time"], [np.nanmax(hsf0km)]),
      sf275_max = (["time"], [np.nanmax(hsf275km)]),
    ),
    coords=dict(
      time=[it*dtime],
    )
  )
