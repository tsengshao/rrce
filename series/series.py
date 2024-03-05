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

outdir=config.dataPath+"/series/"

vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
thData = vvmLoader.loadThermoDynamic(0)
nz, ny, nx = thData['qv'][0].shape
xc, yc, zc = thData['xc'], thData['yc'], thData['zc']
rho = vvmLoader.loadRHO()[:-1]

dataWriter = DataWriter(outdir)

cwv_std = np.zeros(nt)
cwv_mea = np.zeros(nt)
iwp_std = np.zeros(nt)
iwp_mea = np.zeros(nt)
lwp_std = np.zeros(nt)
lwp_mea = np.zeros(nt)
dryfrac = np.zeros(nt)
maxwind = np.zeros(nt)
maxsf0km = np.zeros(nt)
maxsf275km = np.zeros(nt)

for it in range(nt):
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


  cwv_std[it], cwv_mea[it] = np.std(cwv), np.mean(cwv)
  lwp_std[it], lwp_mea[it] = np.std(lwp), np.mean(lwp)
  iwp_std[it], iwp_mea[it] = np.std(iwp), np.mean(iwp)
  dryfrac[it] = np.sum(cwv<30)/cwv.size
  maxwind[it] = np.max((u**2+v**2)**0.5)
  maxsf0km[it] = np.nanmax(hsf0km)
  maxsf275km[it] = np.nanmax(hsf275km)

dataWriter.toNC(f"series_{exp}.nc", \
  data=dict(
    cwv_mean=(["time"], cwv_mea[:]),
    lwp_mean=(["time"], lwp_mea[:]),
    iwp_mean=(["time"], iwp_mea[:]),
    cwv_std=(["time"], cwv_std[:]),
    lwp_std=(["time"], lwp_std[:]),
    iwp_std=(["time"], iwp_std[:]),
    maxwind=(["time"], maxwind[:]),
    dryfrac=(["time"], dryfrac[:]),
    sf000_max=(["time"], maxsf0km[:]),
    sf275_max=(["time"], maxsf275km[:]),
  ),
  coords=dict(
    time=np.arange(nt),
  )
)
