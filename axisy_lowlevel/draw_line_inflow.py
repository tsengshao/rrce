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

for iexp in range(1, nexp):
  exp = explist[iexp]
  rday = rday_1d[iexp]
  print(exp, rday)
  
  fig, axs = plt.subplots(2, 1, figsize=(10,6), sharex=True)
  plt.subplots_adjust(left=0.1)
  if not iswhite:
    bbox = dict(boxstyle='round', fc='k', ec='1')
  else:
    bbox = dict(boxstyle='round', fc='1', ec='k')
  
  plt.sca(axs[0])
  idx = mdict['imet']
  _ = udraw.draw_pannel(plt.gca(), radius_1d, twind_init[idx,iexp], rwind_init[idx,iexp])

  plt.title(f'{config.expdict[exp]}', loc='left', fontweight='bold')
  txtstr = f'{rday-1}' if rday>1 else '0'
  plt.text(0.98, 0.93, mdict['ur_text'].format(exp0=exp0,txtstr=txtstr,rday=rday), ha='right', va='top', transform=axs[0].transAxes, bbox=bbox)

  plt.sca(axs[1])
  _ = udraw.draw_pannel(plt.gca(), radius_1d, twind_last[1,iexp], rwind_last[1,iexp])
  plt.text(0.98, 0.93, '+48 ~ +72 hrs (avg)', ha='right', va='top', transform=axs[1].transAxes, bbox=bbox)

  fig.text(0.96, 0.5, 'tang_wind [m/s]', va='center', color='#E25508', fontweight='bold', rotation='vertical')
  fig.text(0.03, 0.5, 'radi_wind [m/s]', va='center', color='#7262AC', fontweight='bold', rotation='vertical')
  plt.savefig(f'{figdir}/{exp}.png')
  plt.close('all')


bounds=np.array('0 10 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30'.split()).astype(int)
newcolors = np.vstack((
                       [[0.8,0.8,0.8,1]],\
                       plt.cm.Greens(np.linspace(0.2,0.9,1)),
                       plt.cm.Oranges(np.linspace(0.2,0.9,5)),
                       plt.cm.Blues(np.linspace(0.2,0.9,5)),
                       plt.cm.Purples(np.linspace(0.2,0.9,5))
                     ))
cmap = mpl.colors.ListedColormap(newcolors, name='OrangeBlue')
cmap.set_under((0.7,0.7,0.7))
cmap.set_over(plt.cm.Purples(0.95))
norm = mpl.colors.BoundaryNorm(bounds, cmap.N)



###### maximum radius ##########
x_data = np.min(rwind_init[mdict['imet'],1:,0,:], axis=1)
y_data = np.max(twind_last[mdict['imet'],1:,0,:], axis=1)
c_data = rday_1d[1:]
x_data = x_data[:nexp]
y_data = y_data[:nexp]
c_data = c_data[:nexp]

udraw.set_figure_defalut() 
if not iswhite:
  udraw.set_black_background()
fig = plt.figure(figsize=(10,8))
ax  = fig.add_axes([0.13, 0.1, 0.8, 0.8])
cax = fig.add_axes([0.83, 0.3, 0.03, 0.5])
plt.sca(ax)
plt.plot([-100,100],[100,-100],c='0.5',lw=3)
plt.scatter(x_data, y_data, s=300, c=c_data, norm=norm, cmap=cmap,zorder=10)
CB=fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
       cax=cax, orientation='vertical', extend='max')
CB.ax.set_title('restart\nday')
#CB.ax.set_yticks([5,12.5,15.5,20.5,25.5,30.5],['0','10','15','20','25','30'])
CB.ax.set_yticks([0,10,15,20,25,30])
plt.sca(ax)
plt.xlim(-3.5, 0.5)
plt.ylim(-1, 10)
plt.grid(True)
plt.xlabel(f'maximum radial wind / {mdict["scatter_x_label"]} [m/s]')
plt.ylabel('maximum tangential wind / last day average [m/s]')
plt.savefig(f'{figdir}/scatter_max_radi.png', dpi=200)
plt.show()


###### shortest axisy inflow  ##########
x_data = np.min(rwind_init[mdict['imet'],1:,0,:], axis=1)
thld = 0.5
x_data = []
for i in range(0,nexp):
  idx = np.where( (rwind_init[mdict['imet'],i,1,:]-0.5) > 0)[0]
  if len(idx)==0:
    x_data.append(radius_1d[-1])
  else:
    x_data.append(radius_1d[idx[0]])
y_data = np.max(twind_last[mdict['imet'],:,0,:], axis=1)
c_data = rday_1d[:]
x_data = x_data[:nexp]
y_data = y_data[:nexp]
c_data = c_data[:nexp]

udraw.set_figure_defalut() 
if not iswhite:
  udraw.set_black_background()
fig = plt.figure(figsize=(10,8))
ax  = fig.add_axes([0.13, 0.1, 0.8, 0.8])
cax = fig.add_axes([0.83, 0.3, 0.03, 0.5])
plt.sca(ax)
plt.scatter(x_data, y_data, s=300, c=c_data, norm=norm, cmap=cmap,zorder=10)
CB=fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
       cax=cax, orientation='vertical', extend='max')
CB.ax.set_title('restart\nday')
#CB.ax.set_yticks([5,12.5,15.5,20.5,25.5,30.5],['0','10','15','20','25','30'])
CB.ax.set_yticks([0,10,15,20,25,30])
plt.sca(ax)
plt.xlim(-60, 600)
plt.ylim(-1, 10)
plt.grid(True)
plt.title(f'axisymetric > {thld:.2f}', loc='right', fontsize=15)
plt.xlabel(f'closest distance of axisymetric inflow/ {mdict["scatter_x_label"]} [km]')
plt.ylabel('maximum tangential wind / last day average [m/s]')
plt.savefig(f'{figdir}/scatter_closest_axisy_dis.png', dpi=200)
plt.show()


###### length of axisy inflow  ##########
x_data = np.min(rwind_init[mdict['imet'],1:,0,:], axis=1)
thld = 0.5
x_data = []
for i in range(0,nexp):
  condi = rwind_init[mdict['imet'],i,1,:]-0.5 > 0
  idx = np.where( condi )[0]
  if len(idx)==0:
    x_data.append(0)
  else:
    idx0 = idx[0]
    for ir in range(idx0, radius_1d.size):
      if not condi[ir]:
          length=radius_1d[ir] - radius_1d[idx0]
          break
    x_data.append(length)
y_data = np.max(twind_last[mdict['imet'],:,0,:], axis=1)
c_data = rday_1d[:]
x_data = x_data[:nexp]
y_data = y_data[:nexp]
c_data = c_data[:nexp]

udraw.set_figure_defalut() 
if not iswhite:
  udraw.set_black_background()
fig = plt.figure(figsize=(10,8))
ax  = fig.add_axes([0.13, 0.1, 0.8, 0.8])
cax = fig.add_axes([0.15, 0.8, 0.5, 0.03])
plt.sca(ax)
plt.scatter(x_data, y_data, s=300, c=c_data, norm=norm, cmap=cmap,zorder=10)
CB=fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
       cax=cax, orientation='horizontal', extend='max')
CB.ax.set_title('restart day')
#CB.ax.set_yticks([5,12.5,15.5,20.5,25.5,30.5],['0','10','15','20','25','30'])
CB.ax.set_xticks([0,10,15,20,25,30])
plt.sca(ax)
plt.xlim(-50, 500)
plt.ylim(-1, 10)
plt.grid(True)
plt.title(f'axisymetric > {thld:.2f}', loc='right', fontsize=15)
plt.xlabel(f'length of axisymetric inflow/ {mdict["scatter_x_label"]} [km]')
plt.ylabel('maximum tangential wind / last day average [m/s]')
plt.savefig(f'{figdir}/scatter_lengh_axisy.png', dpi=200)
plt.show()


###### axisymetric inflow intensity ##########
x_data = np.mean(rwind_init[mdict['imet'],1:,0,:] * rwind_init[mdict['imet'],1:,1,:], axis=1)
y_data = np.max(twind_last[mdict['imet'],1:,0,:], axis=1)
c_data = rday_1d[1:]
x_data = x_data[:nexp]
y_data = y_data[:nexp]
c_data = c_data[:nexp]

udraw.set_figure_defalut() 
if not iswhite:
  udraw.set_black_background()
fig = plt.figure(figsize=(10,8))
ax  = fig.add_axes([0.13, 0.1, 0.8, 0.8])
cax = fig.add_axes([0.83, 0.3, 0.03, 0.5])
plt.sca(ax)
plt.scatter(x_data, y_data, s=300, c=c_data, norm=norm, cmap=cmap,zorder=10)
CB=fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
       cax=cax, orientation='vertical', extend='max')
CB.ax.set_title('restart\nday')
#CB.ax.set_yticks([5,12.5,15.5,20.5,25.5,30.5],['0','10','15','20','25','30'])
CB.ax.set_yticks([0,10,15,20,25,30])
plt.sca(ax)
plt.xlim(-2, 0.2)
plt.ylim(-1, 10)
plt.grid(True)
plt.title(f'mean( axisymetric * radi_wind )', loc='right', fontsize=15)
plt.xlabel(f'intensity of axisymetric radial wind / {mdict["scatter_x_label"]}')
plt.ylabel('maximum tangential wind / last day average [m/s]')
plt.savefig(f'{figdir}/scatter_axisy_radi.png', dpi=200)
plt.show()







