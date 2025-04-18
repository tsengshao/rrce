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

fname = f'{datdir}/cwv.npz'
data  = np.load(fname)
cwv_init = data['cwv_init']
cwv_last = data['cwv_last']

nexp = len(config.expList)
exp0 = config.expdict[config.expList[0]]

method_dict = {'daily':{'imet':1,\
                         'ur_text':'{exp0} {txtstr}-{rday} day',\
                         'scatter_x_label':'restart day average'
                        },\
               'snapshot':{'imet':0,\
                         'ur_text':'{exp0} {rday} day (snapshot)',\
                         'scatter_x_label':'restart day snapshot',\
                        },\
              }

iswhite = True
tag = 'snapshot'
tag = 'daily'
mdict = method_dict[tag]
if iswhite:
  figdir = f'./{center_flag}_white/{tag}/'
else:
  figdir = f'./{center_flag}/{tag}/'
os.system(f'mkdir -p {figdir}')

udraw.set_figure_defalut() 
if not iswhite:
  udraw.set_black_background()

if False:
  for iexp in range(1, nexp):
    exp = explist[iexp]
    rday = rday_1d[iexp]
    print(exp, rday)
    
    if not iswhite:
      bbox = dict(boxstyle='round', fc='k', ec='1')
    else:
      bbox = dict(boxstyle='round', fc='1', ec='k')
   
    line_obj = [] 
    fig, ax = plt.subplots(1, 1, figsize=(10,6), sharex=True)
    #plt.subplots_adjust(left=0.1)
    idx = mdict['imet']
    P1 = plt.plot(radius_1d, twind_last[1,iexp,0], c='C0')
    plt.ylim([0, 10])
    plt.ylabel('last tangential wind [m/s]')
    line_obj+=P1
    
    ax2 = ax.twinx()
    P2 = plt.plot(radius_1d, cwv_init[1,iexp,0], c='C1')
    plt.ylim([10,60])
    plt.ylabel('init cwv [mm]')
    line_obj+=P2
    plt.legend(line_obj, ['wind', 'cwv'])
  
    plt.title(f'{exp}', loc='left', fontweight='bold')
    plt.show()

#####
## draw scatter 
#####
bounds=np.array('0 10 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30'.split()).astype(int)
newcolors = np.vstack((
                       [[0.8,0.8,0.8,1]],\
                       [[0.5,0.5,0.5,1]],\
                       plt.cm.Greens(np.linspace(0.2,0.9,5)),
                       plt.cm.Oranges(np.linspace(0.2,0.9,5)),
                       plt.cm.Blues(np.linspace(0.2,0.9,5))
                     ))
cmap = mpl.colors.ListedColormap(newcolors, name='OrangeBlue')
cmap.set_under((0.7,0.7,0.7))
cmap.set_over(plt.cm.Purples(0.7))
norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

###### maximum gradient ##########
nsen   = 2
#gradient = np.gradient(cwv_init[mdict['imet'],1:,0,:], radius_1d/1000., axis=1)
#x_data = np.min(gradient, axis=1)
x_data = np.max(cwv_init[mdict['imet'],1:,0,:], axis=1) - \
         np.min(cwv_init[mdict['imet'],1:,0,:], axis=1)
y_data = np.max(twind_last[mdict['imet'],1:,0,:], axis=1)
c_data = rday_1d[1:]
x_data = x_data[:nexp]
y_data = y_data[:nexp]
c_data = c_data[:nexp]

udraw.set_figure_defalut() 
if not iswhite:
  udraw.set_black_background()
fig = plt.figure(figsize=(10,8))
ax  = fig.add_axes([0.15, 0.15, 0.72, 0.75])
cax = fig.add_axes([0.89, 0.15, 0.03, 0.7])
plt.sca(ax)
plt.scatter(x_data[:-nsen], y_data[:-nsen], s=300, c=c_data[:-nsen], norm=norm, cmap=cmap,zorder=10)
plt.scatter(x_data[-nsen:], y_data[-nsen:], s=300, c=c_data[-nsen:], norm=norm, cmap=cmap,zorder=10, marker='X')
CB=fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
       cax=cax, orientation='vertical', extend='max')
CB.ax.set_title('restart\nday', loc='left', fontsize=20)
CB.ax.set_yticks([0,10,15,20,25,30])
plt.sca(ax)
#plt.yticks(np.arange(0,9.01,1.5))
#plt.xticks(np.arange(-3,0.01,0.5))
#plt.ylim(-0.3, 9)
#plt.xlim(0.1, -3)
plt.grid(True)
plt.xlabel(f'CWV contrast\n{mdict["scatter_x_label"]} [mm]')
plt.ylabel('maximum tangential wind\nlast day average [m/s]')
plt.savefig(f'{figdir}/scatter_grad_cwv.png', dpi=200)
plt.show()

