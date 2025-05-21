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
import multiprocessing

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
                         'ur_text':'{exp0} {txtstr}-{rday} day',\
                         'scatter_x_label':'restart day average'
                        },\
               'inflow_snapshot':{'imet':0,\
                         'ur_text':'{exp0} {rday} day (snapshot)',\
                         'scatter_x_label':'restart day snapshot',\
                        },\
              }
iswhite = True
tag = 'inflow_daily'
#tag = 'inflow_snapshot'
mdict = method_dict[tag]
if iswhite:
  figdir = f'./{center_flag}_white/{tag}/'
else:
  figdir = f'./{center_flag}/{tag}/'
os.system(f'mkdir -p {figdir}')

udraw.set_figure_defalut() 
if not iswhite:
  udraw.set_black_background()

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

###### prepare dryfrac
# /data/C.shaoyu/rrce/data/series/RRCE_3km_f00/series_000300.nc
datdir=config.dataPath+f"/series/RRCE_3km_f00/"
def read_series(fname,varname):
    nc = Dataset(fname,'r')
    out = nc.variables[varname][0].data
    nc.close()
    return out
series_dryfrac = np.zeros(rday_1d.size)
series_cwvstd  = np.zeros(rday_1d.size)
for itt in range(rday_1d.size):
    idy = rday_1d[itt]
    it0, it1 = int((idy-1)*24*3), int(idy*24*3)
    it0 = max(0, it0); it1 = max(0, it1)
    print('dry_frac ... ', itt, idy, it0, it1)
    if it1-it0 > 0:
        fname_fmt = f'{datdir}'+'series_{it:06d}.nc'
        with multiprocessing.Pool(processes=5) as pool:
            series = pool.starmap(read_series, \
                              [ (fname_fmt.format(it=it),'dryfrac') for it in range(it0,it1)])
            series_cwv = pool.starmap(read_series, \
                              [ (fname_fmt.format(it=it),'cwv_std') for it in range(it0,it1)])
    else:
        series = [0]
        series_cwv = [0]
    series_dryfrac[itt] = np.mean(series)
    series_cwvstd[itt] = np.mean(series_cwv)


###### maximum radius ##########
nsen   = 2
x_data = series_dryfrac
y_data = np.max(twind_last[mdict['imet'],1:,0,:], axis=1)
c_data = rday_1d[1:]
x_data = x_data[1:nexp]
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
plt.yticks(np.arange(0,9.1,1.5))
plt.xticks(np.arange(0,0.81,0.1))
plt.xlim(-0.05, 0.8)
plt.ylim(-0.3, 9)
plt.grid(True)
plt.xlabel(f'dry fraction')
plt.ylabel('maximum tangential wind\nlast day average [m/s]')
plt.savefig(f'{figdir}/scatter_df_tang.png', dpi=200)


###### inflow ##########
nsen   = 2
x_data = series_dryfrac
#y_data = np.max(twind_last[mdict['imet'],1:,0,:], axis=1)
y_data = np.min(rwind_init[mdict['imet'],1:,0,:], axis=1)
c_data = rday_1d[1:]
x_data = x_data[1:nexp]
y_data = y_data[:nexp]
c_data = c_data[:nexp]

udraw.set_figure_defalut()
if not iswhite:
  udraw.set_black_background()
fig = plt.figure(figsize=(10,8))
ax  = fig.add_axes([0.2, 0.15, 0.67, 0.75])
cax = fig.add_axes([0.89, 0.15, 0.03, 0.7])
plt.sca(ax)
plt.scatter(x_data[:-nsen], y_data[:-nsen], s=300, c=c_data[:-nsen], norm=norm, cmap=cmap,zorder=10)
plt.scatter(x_data[-nsen:], y_data[-nsen:], s=300, c=c_data[-nsen:], norm=norm, cmap=cmap,zorder=10, marker='X')
CB=fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
       cax=cax, orientation='vertical', extend='max')
CB.ax.set_title('restart\nday', loc='left', fontsize=20)
CB.ax.set_yticks([0,10,15,20,25,30])
plt.sca(ax)
#plt.yticks(np.arange())
plt.xticks(np.arange(0,0.81,0.1))
plt.xlim(-0.05, 0.8)
plt.ylim(0.3, -3)
plt.grid(True)
plt.xlabel(f'dry fraction')
plt.ylabel('maximum radial wind\ninitial day average [m/s]')
plt.savefig(f'{figdir}/scatter_df_radi.png', dpi=200)



###### maximum radius ##########
x_data = series_cwvstd
y_data = np.max(twind_last[mdict['imet'],1:,0,:], axis=1)
c_data = rday_1d[1:]
x_data = x_data[1:nexp]
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
plt.ylim(-1, 10)
plt.grid(True)
plt.xlabel(f'cwv std [mm]')
plt.ylabel('maximum tangential wind\nlast day average [m/s]')
plt.savefig(f'{figdir}/scatter_cwvstd_tang.png', dpi=200)
plt.show()

