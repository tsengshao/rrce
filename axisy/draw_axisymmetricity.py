import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(1,'../')
import config
from netCDF4 import Dataset
import matplotlib as mpl
from mpi4py import MPI

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
iexp = int(sys.argv[1])

nt = config.totalT[iexp]
exp = config.expList[iexp]
if exp=='RRCE_3km_f00':
  nt=2521
else:
  nt=217
if (cpuid==0): print(exp, nt)
dtime = 20

center_flag='czeta0km_positivemean'
datdir=config.dataPath+f"/axisy/{center_flag}/{exp}/"


it=216
fname = f'{datdir}/axmean-{it:06d}.nc'
nc = Dataset(fname, 'r')
radius_1d = nc.variables['radius'][:]/1000 #[km]
zc_1d  = nc.variables['zc'][:]/1000 #[km]

set_black_background()

bounds = np.arange(-5, 5.1, 1)
cmap = plt.cm.RdYlBu
norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=256, extend='both')

fig = plt.figure(figsize=(8,8))
ax_top   = plt.axes([0.15,0.3,0.75,0.6])
ax_cbar  = plt.axes([0.90, 0.3, 0.02, 0.6])
ax_lower = plt.axes([0.15,0.1,0.75,0.2])

plt.sca(ax_top)
rwind = nc.variables['radi_wind'][0,0,:,:]
rwind_a = nc.variables['radi_wind'][0,1,:,:]
plt.pcolormesh(radius_1d, zc_1d, rwind, cmap=cmap, norm=norm)
plt.colorbar(cax=ax_cbar)
plt.contour(radius_1d, zc_1d, rwind_a, levels=[0.5,0.8], linewidths=[1,2], colors=['k'])
plt.xlim(0,radius_1d.max())
plt.title('radi_wind', loc='left', fontweight='bold')
time = (dtime*it)/60 #hour
plt.title(f'{exp}\n{time:.1f}hr', loc='right', fontweight='bold')

plt.sca(ax_lower)
cwv = nc.variables['cwv'][0,0,:]
cwv_a = nc.variables['cwv'][0,1,:]
plt.plot(radius_1d, cwv, lw=5)
plt.xlim(0,radius_1d.max())

plt.show()

