import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(1,'../')
import config
from netCDF4 import Dataset
import matplotlib as mpl
from mpi4py import MPI
import pandas as pd

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
th=1e-4

cols = np.array(['init', '2hr', '6hr', '12hr'])
contime = np.array([0.33333, 2, 6, 12])
ncols = cols.size
df = pd.DataFrame(np.zeros((nexp, ncols))*np.nan, columns=cols, index=config.expList)

for iexp in range(nexp):
  nt = config.totalT[iexp]
  exp = config.expList[iexp]
  dtime = config.getExpDeltaT(exp)    #minutes
  tspdy = int(60*24/dtime)  # number of timestep per day
  nday  = int((nt-1)/tspdy+1)
  #print(exp, nday, nt)
  
  datpath=config.dataPath+f"/series/{exp}/"
  continuous = 0
  continuous2 = 0
  is_filled = np.ones(ncols)*False

  for it in range(nt):
    nc = Dataset(datpath+f'100km/series_conv_{it:06d}.nc', 'r')
    mzeta = nc.variables['max_zeta'][0]

    if (mzeta > 1e-4):
      continuous += 1
    else:
      continuous = 0

    for idef in range(contime.size):
      if ( continuous >= contime[idef]*60/dtime and not is_filled[idef] ):
        df.iloc[iexp, idef] = (it-continuous)*dtime/60
        is_filled[idef] = True


    if ( np.all(is_filled) ):
      continue
  print(df.iloc[iexp,:])

df.to_csv('seed_time.csv',float_format='%10.2f',index_label='exp_name')
