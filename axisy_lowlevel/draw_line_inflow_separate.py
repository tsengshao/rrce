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
datdir=config.dataPath+f"/axisy_lowlevel/{center_flag}/"

fname = f'{datdir}/lowlevel_inflow_0-500m.npz'
data  = np.load(fname)
explist = data['expList']
rday_1d = data['restart_day']
var_1d  = data['var_1d']
radius_1d = data['radius_1d']
method_1d = data['method_1d']
rwind_init = data['rwind_init']
twind_init = data['twind_init']
rwind_last = data['rwind_last']
twind_last = data['twind_last']
nmet, nexp, nvar, nradius = data['rwind_init'].shape

nexp = len(config.expList)
exp0 = config.expdict[config.expList[0]]

method_dict = {'inflow_daily':{'imet':1,\
                         'ur_text':'{txtstr}-{rday} day',\
                         'scatter_x_label':'restart day average'
                        },\
               'inflow_snapshot':{'imet':0,\
                         'ur_text':'{rday} day (snapshot)',\
                         'scatter_x_label':'restart day snapshot',\
                        },\
              }
iswhite = True
tag = 'inflow_daily'
#tag = 'inflow_snapshot'
mdict = method_dict[tag]
if iswhite:
  figdir = f'./{center_flag}_sap_white/{tag}/'
else:
  figdir = f'./{center_flag}_sap/{tag}/'
os.system(f'mkdir -p {figdir}')

udraw.set_figure_defalut() 
if not iswhite:
  udraw.set_black_background()

for iexp in range(1, nexp):
  exp = explist[iexp]
  rday = rday_1d[iexp]
  func = float if rday%1 > 0 else int
  rday = func(rday)
  print(exp, rday)

  # RRCE
  if not iswhite:
    bbox = dict(boxstyle='round', fc='k', ec='1')
  else:
    bbox = dict(boxstyle='round', fc='1', ec='k')
  
  #fig      = plt.figure(figsize=(10,4))
  fig      = plt.figure(figsize=(10,6))
  ax       = fig.add_axes([0.05,0.15,0.9,0.7])
  idx = mdict['imet']
  _ = udraw.draw_pannel(ax, radius_1d, twind_init[idx,iexp], rwind_init[idx,iexp])
  txtstr = f'{rday-1}' if rday>1 else '0'
  st = mdict['ur_text'].format(txtstr=txtstr,rday=rday)
  #plt.text(0.02, 0.93, \
  #         st, ha='left', va='top', transform=ax.transAxes, bbox=bbox)
  plt.title(st, loc='right', fontweight='bold')
  plt.title('    '+exp0, loc='left', fontweight='bold')
  #plt.tight_layout()
  plt.savefig(f'{figdir}/{exp0}_{rday}dy.png')

  #fig      = plt.figure(figsize=(10,4))
  fig      = plt.figure(figsize=(10,6))
  ax       = fig.add_axes([0.05,0.15,0.9,0.7])
  _ = udraw.draw_pannel(ax, radius_1d, twind_last[1,iexp], rwind_last[1,iexp])
  plt.title('+48 ~ +72 hrs', loc='right', fontweight='bold')
  plt.title(f'    {config.expdict[exp]}', loc='left', fontweight='bold')
  #plt.text(0.98, 0.93, '+48 ~ +72 hrs (avg)', ha='right', va='top', transform=ax.transAxes, bbox=bbox)
  #plt.tight_layout()
  plt.savefig(f'{figdir}/{exp}_3dy.png')
  plt.close('all')

