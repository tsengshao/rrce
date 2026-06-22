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
  reday=int(exp.split('_')[-1].replace('p','.'))
if (cpuid==0): print(exp, nt)
dtime = 20
exp = 'RRCE_3km_f00'
print(exp, reday)

re_start_it = int(reday*3*24)
nt = 217

re_start_it = np.max([int((reday-1)*3*24), 0])
nt = 217+72

center_flag='czeta0km_positivemean'
fig_flag   ='hov_cwv_f00_4dy'
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
cwv = np.zeros(dims)
lwp = np.zeros(dims)
iwp = np.zeros(dims)
olr = np.zeros(dims)
rain = np.zeros(dims)
rwind_lower = np.zeros(dims)

for it0 in range(nt):
  it = re_start_it + it0
  fname = f'{datdir}/axmean_process-{it:06d}.nc'
  nc    = Dataset(fname, 'r')
  cwv[:,it0,:] = nc.variables['cwv'][0, :]
  rain[:,it0,:] = nc.variables['rain'][0, :]
  rwind_lower[:,it0,:] = nc.variables['radi_wind_lower'][0, :]

time_1d = time_hr_1d/24.
time_units = 'days'
time_int   = 1
# figsize    = (6.5, 10)
# figsize    = (6.5, 13.3)
figsize    = (8, 13.3)

udraw.set_figure_defalut() 
if not iswhite:
  udraw.set_black_background()

varname = 'cwv'
varunits = 'mm'
var     = cwv[0]
var_ax  = cwv[1]
levels  = np.arange(10,61,2)

fig, ax = plt.subplots(figsize=figsize)
cmap = udraw.get_cmap('cwv')
norm = mpl.colors.BoundaryNorm(boundaries=levels, \
          ncolors=256, extend='both')
P  = plt.pcolormesh(radius_1d, time_1d, var, cmap=cmap, norm=norm)
CB = plt.colorbar(P, orientation='vertical')
ctickslevels = levels[::5]
CB.ax.set_yticks(ctickslevels, list(map(str, ctickslevels)))

# draw radial wind for reference
CO = plt.contour(radius_1d, time_1d, rwind_lower[0], levels=[-3., -1.5], colors=['0.75'], linewidths=[2], negative_linestyles='solid')

# draw rainfall
CO_rain = plt.contour(radius_1d, time_1d, rain[0], levels=[1., 5.], colors=['tab:red'], linewidths=[2, 4])
## cs = plt.contourf(radius_1d, time_1d, rain[0], \
##                   levels  = [5, 10000], \
##                   hatches = ['/'], \
##                   colors = 'none', \
##                  )
## for c in cs.collections:
##     c.set_edgecolor("tab:red")   # hatch color
##     c.set_linewidth(2.0)
#CO_lwp = plt.contour(radius_1d, time_1d, lwp[0], levels=[5], colors=['0.5'], linewidths=[2])
#CO_olr = plt.contour(radius_1d, time_1d, olr[0], levels=[100, 150, 200], colors=['0.5'], linewidths=[2])

text = \
       f'red contour   : rain [ 1 and 5 mm/hr]\n'+\
       f'gray contour : radial wind [-3 and -1.5 m/s]'
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
ctickslevels = levels[::5]
CB.ax.set_xticks(ctickslevels, list(map(str, ctickslevels)))
plt.savefig(f'./{figdir}/hov_colorbar.png',dpi=200, transparent=True)
plt.close('all')

