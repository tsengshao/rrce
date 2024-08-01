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
                       'axes.labelcolor': 'white',
                      })

plt.rcParams.update({'font.size':20,
                     'axes.linewidth':2,
                     'lines.linewidth':5})

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)

center_flag = 'sf_largest_0'

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
  
  #../../data/find_center/sf_largest_0_RRCE_3km_f00.txt
  datdir=config.dataPath+f"/find_center/"
  
  # read hei
  f=open(f'{datdir}/{center_flag}_{exp}.txt','r')
  line = f.read().split('\n')[2]
  zhei = float(line.split()[2])
  
  data = np.loadtxt(f'{datdir}/{center_flag}_{exp}.txt', skiprows=7, usecols=[0,1])
  mzeta0 = data[0,1]
  mzeta1 = data[216,1]


  data = np.loadtxt(f'{datdir}/{center_flag}_RRCE_3km_f00.txt', skiprows=7, usecols=[0,1])
  it=restart_day*3*24+216
  mzeta2 = data[it,1]

  df.iloc[iexp,0] = restart_day
  df.iloc[iexp,1] = mzeta1/mzeta0
  df.iloc[iexp,2] = mzeta1/mzeta2


fontcolor = 'white'
set_black_background()

ylim=[6,20]
xlim = [10-0.6 , df['restart_day'].max()+0.6]

colist = [fontcolor, '#55A4FF', '#FF8E55', '#E555FF']

fig, ax = plt.subplots(figsize=(12,10))
plt.scatter(df['restart_day'], df['nself'],s=250,color=colist[1],label='normailzed by day0',zorder=10)
plt.scatter(df['restart_day'], df['nf00'], s=250,color=colist[2],label='normalized by f00',zorder=10)
plt.legend()

yticks=np.arange(0,max(ylim)+1,2)
plt.yticks(yticks)

xticks = np.arange(0,31,2)
xtlabel = xticks.astype(str)
#xtlabel[1::2]=''
plt.xticks(xticks, xtlabel)

plt.ylim(ylim)
plt.xlim(xlim)
plt.grid(True)
plt.ylabel('center SF ratio')
plt.xlabel('the restart day')
plt.title(f'centerSF@{zhei:.1f}m enhancement in 3days',loc='left',fontweight='bold')
plt.savefig('scatter_msf_center.png', dpi=250)
#plt.show()





