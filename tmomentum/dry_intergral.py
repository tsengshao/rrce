import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(1,'../')
import config
from netCDF4 import Dataset
import matplotlib as mpl
import util.tools as tools


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

dry_twind_last = np.zeros((nexp, nradius))

iexp = 1 # expnum
for iexp in range(nexp):
#for iexp in [18]:
    print(iexp)
    idx  = 1 # daily mean
    time = np.arange(0, 24*3*60*60+0.0001, 10)
    dt = time[1]-time[0]
    twind_2d = np.zeros((time.size, radius_1d.size))
    
    coriolis     = 2 * (2*np.pi/86400) * np.sin(10*np.pi/180)
    
    rwind_0 = rwind_init[idx, iexp, 0]
    dr = radius_1d[1]-radius_1d[0] * 1e3
    for i in range(time.size-1):
      vorticity_1d = twind_2d[i] / radius_1d / 1e3 + \
                     np.gradient(twind_2d[i]) / dr
      #tandency = -1 * rwind_0 * (coriolis+vorticity_1d)
      tandency = -1 * rwind_0 * (coriolis)
      twind_2d[i+1] = twind_2d[i] + tandency * dt
      #print(i, twind_2d[i+1].max(), tandency.max())
      if np.any(np.isnan(twind_2d)) or np.max(twind_2d)>80:
          print('ERROR ! overflow !')
          print(i, twind_2d[i+1].max(), tandency.max())
          sys.exit()
    dry_twind_last[iexp,:] = twind_2d[86400:,:].mean(axis=0)
    if False:
        fig, ax = plt.subplots()
        x = radius_1d.copy()
        y = time.copy() / 86400
        C = plt.contour(x, y, twind_2d)
        plt.clabel(C)
        plt.title(explist[iexp])
        plt.show()

xpoint = rwind_init[idx, :, 0, :].min(axis=1)
dry_point = dry_twind_last.max(axis=1)
ypoint = twind_last[idx, :, 0, :].max(axis=1)

fig, ax = plt.subplots()
plt.scatter(xpoint, dry_point, color='r')
plt.scatter(xpoint, ypoint, color='k')
plt.xlim(-3.5, -0.5)
plt.ylim(-1, 10)
plt.savefig('fig_only_coriolis.png', dpi=200)
plt.show()

sys.exit()
