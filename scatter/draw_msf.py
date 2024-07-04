import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(1,'../')
import config
from netCDF4 import Dataset
import matplotlib as mpl
from mpi4py import MPI
import pandas as pd
import matplotlib.pyplot as plt

def set_black_background():
  plt.rcParams.update({
                       'axes.edgecolor': 'white',
                       'axes.facecolor': 'black',
                       'figure.edgecolor': 'black',
                       'figure.facecolor': 'black',
                       'text.color': 'white',
                       'xtick.color': 'white',
                       'ytick.color': 'white',
                      })

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)

nc = Dataset(config.dataPath+"/series/RRCE_3km_f00_10/series_hsf_000000.nc",'r')
zz = nc.variables['zz'][:]
iz1p5 = np.argmin(np.abs(zz-1500))

df = pd.DataFrame(np.zeros((nexp,3)), columns=['restart_day', 'nself', 'nf00'])

for iexp in range(nexp):
  nt = config.totalT[iexp]
  exp = config.expList[iexp]
  dtime = config.getExpDeltaT(exp)    #minutes
  tspdy = int(60*24/dtime)  # number of timestep per day
  nday  = int((nt-1)/tspdy+1)
  #print(exp, nday, nt)

  dum = exp.split('_')
  if (len(dum)==4):
    restart_day = int(dum[-1])
  else:
    restart_day = 0
  
  datpath=config.dataPath+f"/series/{exp}/"

  it=0
  nc = Dataset(datpath+f'series_hsf_{it:06d}.nc', 'r')
  mzeta0 = nc.variables['maxsf'][0,iz1p5]

  it=216
  nc = Dataset(datpath+f'series_hsf_{it:06d}.nc', 'r')
  mzeta1 = nc.variables['maxsf'][0,iz1p5]

  it=restart_day*3*24+217
  nc = Dataset(datpath+f'../RRCE_3km_f00/series_hsf_{it:06d}.nc', 'r')
  mzeta2 = nc.variables['maxsf'][0,iz1p5]

  df.iloc[iexp,0] = restart_day
  df.iloc[iexp,1] = mzeta1/mzeta0
  df.iloc[iexp,2] = mzeta1/mzeta2


plt.rcParams.update({'font.size':20,
                     'axes.linewidth':2,
                     'lines.linewidth':2})
fontcolor = 'white'
set_black_background()

ylim=[3,20]
xlim = [15-0.6 , df['restart_day'].max()+0.6]

colist = [fontcolor, '#55A4FF', '#FF8E55', '#E555FF']

fig, ax = plt.subplots(figsize=(12,10))
plt.scatter(df['restart_day'], df['nself'],s=250,color=colist[1],label='normailzed by day0',zorder=10)
plt.scatter(df['restart_day'], df['nf00'], s=250,color=colist[2],label='normalized by f00',zorder=10)
plt.legend()

yticks=np.arange(0,max(ylim)+1,2)
plt.yticks(yticks)

xticks = np.arange(0,31,1)
xtlabel = xticks.astype(str)
xtlabel[1::2]=''
plt.xticks(xticks, xtlabel)

plt.ylim(ylim)
plt.xlim(xlim)
plt.grid(True)
plt.ylabel('max SF ratio', color=fontcolor)
plt.xlabel('the restart day', color=fontcolor)
plt.title('maxSF@1.5km enhancement in 3days',loc='left',fontweight='bold')
plt.savefig('scatter_msf.png', dpi=250)
plt.show()





