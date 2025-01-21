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

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])

iswhite = True

nt = config.totalT[iexp]
exp = config.expList[iexp]
nt = 217
if exp=='RRCE_3km_f00' or exp=='RRCE_3km_f10':
  reday=0
else:
  reday=int(exp.split('_')[-1])
if (cpuid==0): print(exp, nt)
dtime = 20
exp = 'RRCE_3km_f00'
print(exp, reday)

re_start_it = int(reday*3*24)
nt = 217

re_start_it = np.max([int((reday-1)*3*24), 0])
nt = 217+72

center_flag='czeta0km_positivemean'
fig_flag   ='hov_inflow_f00_4dy'
datdir=config.dataPath+f"/axisy/{center_flag}/{exp}/"
if iswhite:
  figdir=f'./{center_flag}_white/{fig_flag}/'
else:
  figdir=f'./{center_flag}/{fig_flag}/'
os.system(f'mkdir -p {figdir}')

vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
zz_raw = vvmLoader.loadZZ()[:-1]

fname = f'{datdir}/axmean_process-{0:06d}.nc'
nc = Dataset(fname, 'r')
radius_1d = nc.variables['radius'][:]/1.e3
zc_1d     = nc.variables['zc'][:]/1.e3
ens_1d    = np.array(['mean', 'axisym'])
time_hr_1d  = (re_start_it+np.arange(nt))*dtime/60 #hours
print(time_hr_1d[0], time_hr_1d[-1], time_hr_1d[-1]-time_hr_1d[0])

dims = (ens_1d.size, nt, radius_1d.size)
rwind_lower = np.zeros(dims)
twind_lower = np.zeros(dims)
conv_lower  = np.zeros(dims)

for it0 in range(nt):
  it = re_start_it + it0
  fname = f'{datdir}/axmean_process-{it:06d}.nc'
  nc    = Dataset(fname, 'r')
  rwind_lower[:,it0,:] = nc.variables['radi_wind_lower'][0, :]
  twind_lower[:,it0,:] = nc.variables['tang_wind_lower'][0, :]
  conv_lower[:,it0,:]  = nc.variables['conv_lower'][0, :]

time_1d = time_hr_1d.copy()
time_1d = time_hr_1d/24.
time_units = 'days'
time_int   = 1
figsize    = (6.5, 10)
figsize    = (6.5, 13.3)
figsize    = (8, 13.3)

udraw.set_figure_defalut() 
if not iswhite:
  udraw.set_black_background()

varname = 'radi_wind'
varunits = 'm/s'
var     = rwind_lower[0]
var_ax  = rwind_lower[1]
levels  = [-10, -5, -3, -2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5,  2, 3, 5, 10]
inner_length = 10 #km
indxinner = np.argmin(np.abs(radius_1d-inner_length))
loc_maxconv = radius_1d[np.argmax(conv_lower[0,:,indxinner:], axis=1)+indxinner]

# varname = 'tang_wind'
# varunits = 'm/s'
# var     = twind_lower[0]
# var_ax  = twind_lower[1]
# levels  = [-10, -5, -3, -2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5,  2, 3, 5, 10]
# inner_length = 10 #km
# indxinner = np.argmin(np.abs(radius_1d-inner_length))
# loc_maxconv = radius_1d[np.argmax(conv_lower[0,:,indxinner:], axis=1)+indxinner]


fig, ax = plt.subplots(figsize=figsize)
cmap = udraw.get_cmap('pwo')
norm = mpl.colors.BoundaryNorm(boundaries=levels, \
          ncolors=256, extend='both')
P  = plt.pcolormesh(radius_1d, time_1d, var, cmap=cmap, norm=norm)
CB = plt.colorbar(P, orientation='vertical')
CB.ax.set_yticks(levels, list(map(str, levels)))
cs = plt.contourf(radius_1d, time_1d, var_ax, \
                  levels  = [0.9, 10000], \
                  hatches = ['/'], \
                  colors  = 'none', \
                 )
cs = plt.contour(radius_1d, time_1d, var_ax, \
                  levels  = [0.9, 10000], \
                  colors  = ['k'], \
                  linewidths = [0.5],\
                )
psize = 10
plt.scatter(loc_maxconv, time_1d, s=psize, c='0')
text = f'{varname} [{varunits}, 0-500m]\n'+\
       f'hatch: axisymmetric > 0.9\n'+\
       f'dot: maximum convergence away from {inner_length:.0f}km'
plt.text(0.99, 0.99, text, \
                     fontsize = 8, \
                     va='top', ha='right', \
                     transform = ax.transAxes,\
                     color='k',\
                     bbox=dict(boxstyle="square",\
                               ec='0',\
                               fc=(1,1,1,0.3)),\
        )
plt.yticks(np.arange(0, time_1d.max()+0.0001, time_int))
plt.xticks(np.arange(0, radius_1d.max()+1, 100))
plt.ylim(time_1d.min(), time_1d.max())
plt.xlabel('radius [km]')
plt.ylabel(f'simulation time [{time_units}]')
plt.title(f'{config.expdict[exp]}', loc='left', fontweight='bold', fontsize=20)
plt.title(f'{time_1d.min():.0f} - {time_1d.max():.0f} days', loc='right', fontweight='bold', fontsize=15)
plt.savefig(f'{figdir}/{varname}_{exp}_{reday:d}.png', dpi=200, transparent=True)
plt.close('all')

### save colorbar
fig, ax = plt.subplots(figsize=(12, 1), layout='constrained')
CB=fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
             cax=ax, orientation='horizontal')
CB.ax.set_xticks(levels, list(map(str, levels)))
plt.savefig(f'./{figdir}/hov_colorbar.png',dpi=200, transparent=True)
plt.close('all')

