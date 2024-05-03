import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(1,'../')
import config
from netCDF4 import Dataset
import matplotlib as mpl
from mpi4py import MPI

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
ofile = open('seed_time.txt','w')
th=1e-4

for iexp in range(nexp):
  nt = config.totalT[iexp]
  exp = config.expList[iexp]
  dtime = config.getExpDeltaT(exp)    #minutes
  tspdy = int(60*24/dtime)  # number of timestep per day
  nday  = int((nt-1)/tspdy+1)
  #print(exp, nday, nt)
  
  datpath=config.dataPath+f"/series/{exp}/"
  for it in range(nt):
    nc = Dataset(datpath+f'100km/series_conv_{it:06d}.nc', 'r')
    mzeta = nc.variables['max_zeta'][0]
    if (mzeta > th): 
      break
  if it==nt-1 and mzeta <= th:
    mzeta=-999.99

  line = f'{exp:15s} ... max_zeta = {mzeta:.5f} at {it*dtime/60:7.2f} hours ( {it:3d} {it/72:7.3f})'
  print(line)
  ofile.write(line+'\n')
     




