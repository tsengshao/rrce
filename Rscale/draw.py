import matplotlib.pyplot as plt
import numpy as np
import sys, os
sys.path.insert(1,'../')
import config
import util.tools as tools
from datetime import datetime, timedelta
from netCDF4 import Dataset

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

nexp = len(config.expList)
iexp = int(sys.argv[1])

nt = config.totalT[iexp]
exp = config.expList[iexp]
if exp!='RRCE_3km_f00': nt=217
dtime = config.getExpDeltaT(exp)    #minutes

center_flag = 'sf_largest_0'
datdir=config.dataPath+f"/distance/{center_flag}/{exp}/"

outpath=f'./fig/{center_flag}/{exp}/'
os.system(f'mkdir -p {outpath}')

nc = Dataset(f'{datdir}/axisym-{10:06d}.nc', 'r')
rc = nc.variables['rc'][:]
zc = nc.variables['zc'][:]
izc = np.argmin(np.abs(zc-1000))-1
izc = 8; zhei='951.5m'
nc.close()

#rossby number
# Ro = U/L*f
f = 2*2*np.pi/86400*np.sin(np.pi/180* 10)
func_L_rossby = lambda u: u/f/1000 #[km], u[m/s]
U_rossby = rc*1000*f  #[m/s]

for it in range(nt):
  print(it)
  ncax = Dataset(f'{datdir}/axisym-{it:06d}.nc', 'r')
  ncga = Dataset(f'{datdir}/axisym_gamma-{it:06d}.nc', 'r')
  vname = 'u_tang'
  vname = 'ws'
  ws = ncax[vname][0,izc,:]
  ws_gamma = ncga[vname][0,izc,:]
  
  #idx     = np.nonzero((np.abs(ws-U_rossby))<0.1)[0]
  idx = np.nonzero((U_rossby-ws)<0)[0]
  R_cross = rc[idx[-1]] if len(idx)>=1 else np.nan
  
  fontcolor = 'white'
  set_black_background()
  
  fig = plt.figure(figsize=(12,10))
  ax  = fig.add_axes([0.1, 0.3, 0.8, 0.6])
  ax2 = ax.twinx()
  ax_lo = fig.add_axes([0.1, 0.1, 0.8, 0.18])
  xticks=np.arange(0,801,100)
  
  plt.sca(ax)
  c = 'C0'
  plt.plot([R_cross, R_cross], [0,100], c='0.7', ls='--')
  plt.plot(rc, ws, c=c, alpha=0.5)
  plt.plot(rc, np.where(ws_gamma>0.5, ws, np.nan), c=c, alpha=1)
  plt.plot(rc, U_rossby, '--', c=c, lw=3)
  plt.ylabel(f'{vname} [m/s]')
  plt.ylim(0, 16)
  plt.grid(True)
  plt.gca().yaxis.label.set_color(c)
  plt.gca().tick_params(axis='y', colors=c)
  plt.text(0.01, 0.95, f'@{zhei}', \
           transform=ax.transAxes, \
           ha='left')
  
  plt.sca(ax2)
  c = 'C1'
  plt.plot(rc, func_L_rossby(ws), c=c, alpha=0.5)
  plt.plot(rc, np.where(ws_gamma>0.5, func_L_rossby(ws), np.nan), c=c, alpha=1)
  plt.plot(rc, rc, '--', c=c, lw=3)
  plt.ylabel('R [km]')
  plt.ylim(0, 800)
  plt.xlim(0, xticks.max())
  plt.gca().yaxis.label.set_color(c)
  plt.gca().tick_params(axis='y', colors=c)
  plt.xticks(xticks, ['']*xticks.size)
  
  plt.title(f'{exp}', loc='left', fontweight='bold')
  plt.title(f'{it*dtime/60:.1f} hours', loc='right', fontweight='bold')
  
  cwv = ncax.variables['cwv'][0,:]
  cwv_gamma = ncga.variables['cwv'][0,:]
  plt.sca(ax_lo)
  c = 'w'
  plt.plot(rc, cwv, c=c, alpha=0.5)
  plt.plot(rc, np.where(cwv_gamma>0.5, cwv, np.nan), c=c, alpha=1)
  plt.ylabel('CWV [mm]')
  plt.xticks(xticks)
  plt.yticks(np.arange(10,71,20))
  plt.ylim(10,70)
  plt.xlim(0, 800)
  plt.xlabel('Radius [km]')
  plt.grid(True)
  
  plt.savefig(f'./{outpath}/{vname}_{it:06d}.png', dpi=200)
  plt.close('all')
