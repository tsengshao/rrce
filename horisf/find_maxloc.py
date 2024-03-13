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
#iexp = int(sys.argv[1])

# for iexp in range(nexp):
for iexp in [3]:
  nt = config.totalT[iexp]
  exp = config.expList[iexp]
  dtime = config.getExpDeltaT(exp)    #minutes
  
  outdir=config.dataPath+f"/horisf/{exp}/"
  print(outdir)
  
  vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
  thData = vvmLoader.loadThermoDynamic(0)
  nz, ny, nx = thData['qv'][0].shape
  xc, yc, zc = thData['xc'], thData['yc'], thData['zc']
  rho = vvmLoader.loadRHO()[:-1]
  
  yloc  = np.zeros(nt)
  xloc  = np.zeros(nt)
  val   = np.zeros(nt)
  tstep = np.zeros(nt)
  for it in range(nt):
    print(it)
    t = it
    hsf0km = np.fromfile(\
               f'{config.dataPath}/horisf/{exp}/hrisf_0.00km_{t:06d}.dat',\
               np.float32).reshape(ny,nx)
    y, x = np.where(hsf0km==np.max(hsf0km))
    yloc[it], xloc[it] = y[0], x[0]
    val[it]  = np.max(hsf0km)
    tstep[it] = t
  
  outdat = np.vstack((tstep, xloc, yloc, val)).T
  np.savetxt(outdir+'maxloc_hrisf_0.00km.txt',\
             outdat,\
             fmt='  %06d, %6d, %6d, %f',\
             header='%6s, %6s, %6s, %s'%('timestep', 'xloc','yloc','maxSF'),\
             comments='',\
            )
