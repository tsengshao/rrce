import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(1,'../')
import config
from netCDF4 import Dataset
import matplotlib as mpl
from mpi4py import MPI
import util_draw as udraw
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.tools as tools
from matplotlib.collections import LineCollection
import matplotlib.patheffects as mpl_pe

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

center_flag='czeta0km_positivemean'
outdir=config.dataPath+f"/axisy_lowlevel/{center_flag}/"
datdir=config.dataPath+f"/axisy/{center_flag}/"
os.system(f'mkdir -p {outdir}')

fname = f'{datdir}/RRCE_3km_f00_10/axmean_process-{0:06d}.nc'
nc = Dataset(fname, 'r')
radius_1d = nc.variables['radius'][:]/1.e3
zc_1d     = nc.variables['zc'][:]/1.e3
ens_1d    = np.array(['mean', 'axisym'])
nens = ens_1d.size
nradi = radius_1d.size
dtime = 20
 
nexp = len(config.expList)
dims = (nexp, nens, nradi) 
expList     = np.array(config.expList)
restart_day = np.zeros(nexp)
rwind_init        = np.zeros(dims)
twind_init        = np.zeros(dims)
rwind_init_daily  = np.zeros(dims)
twind_init_daily  = np.zeros(dims)
rwind_last        = np.zeros(dims)
twind_last        = np.zeros(dims)
rwind_last_daily  = np.zeros(dims)
twind_last_daily  = np.zeros(dims)

for iexp in range(nexp):
  exp = expList[iexp]

  if exp=='RRCE_3km_f00' or exp=='RRCE_3km_f10':
    rday = 0 
    rce_it0, rce_it1 = 0, 1
  else:
    rday = float(exp.split('_')[-1].replace('p','.'))
    rce_it0, rce_it1 = int((rday-1)*72), int((rday)*72)
  restart_day[iexp] = rday
   
  print(iexp, exp, restart_day[iexp])
 
  # process initial daily 
  nit = rce_it1 - rce_it0
  print(rce_it0, rce_it1, nit)
  for it in range(rce_it0, rce_it1):
    fname = f'{datdir}/RRCE_3km_f00/axmean_process-{it:06d}.nc'
    nc    = Dataset(fname, 'r')
    rwind_init_daily[iexp] += nc.variables['radi_wind_lower'][0, :] / nit
    twind_init_daily[iexp] += nc.variables['tang_wind_lower'][0, :] / nit
 
  # process initial wind 
  fname = f'{datdir}/RRCE_3km_f00/axmean_process-{rce_it1-1:06d}.nc'
  nc    = Dataset(fname, 'r')
  rwind_init[iexp] += nc.variables['radi_wind_lower'][0, :]
  twind_init[iexp] += nc.variables['tang_wind_lower'][0, :]

  # create last days 
  it0, it1 = 145, 217
  nit = it1 - it0
  for it in range(it0, it1):
    fname = f'{datdir}/{exp}/axmean_process-{it:06d}.nc'
    nc    = Dataset(fname, 'r')
    rwind_last_daily[iexp] += nc.variables['radi_wind_lower'][0, :] / nit
    twind_last_daily[iexp] += nc.variables['tang_wind_lower'][0, :] / nit

  fname = f'{datdir}/{exp}/axmean_process-{it1-1:06d}.nc'
  nc    = Dataset(fname, 'r')
  rwind_last[iexp] += nc.variables['radi_wind_lower'][0, :]
  twind_last[iexp] += nc.variables['tang_wind_lower'][0, :]
  
  
fname = f'{outdir}/lowlevel_inflow_0-500m.npz'
np.savez(fname, 
         nexp        = nexp, \
         expList     = expList, \
         restart_day = restart_day, \
         var_1d      = ens_1d, \
         radius_1d   = radius_1d, \
         method_1d   = ('instant', 'daily'),\
         dims        = ('method_1d', 'expList', 'var_1d', 'radius_1d'),\
         rwind_init  = np.stack((rwind_init,\
                                 rwind_init_daily)),\
         twind_init  = np.stack((twind_init,\
                                 twind_init_daily)),\
         rwind_last  = np.stack((rwind_last,\
                                 rwind_last_daily)),\
         twind_last  = np.stack((twind_last,\
                                 twind_last_daily)),\
        )
