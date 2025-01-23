import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(1,'../')
import config
from netCDF4 import Dataset
import matplotlib as mpl
import util.tools as tools
import numba

plt.rcParams.update({'font.size':23,
                     'axes.linewidth':2,
                     'lines.linewidth':5})

def get_colormap():
    bounds=np.array('0 10 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30'.split()).astype(int)
    newcolors = np.vstack((
                           [[0.8,0.8,0.8,1]],\
                           [[0.5,0.5,0.5,1]],\
                           #plt.cm.Reds(np.linspace(0.2,0.9,1)),
                           plt.cm.Greens(np.linspace(0.2,0.9,5)),
                           plt.cm.Oranges(np.linspace(0.2,0.9,5)),
                           plt.cm.Blues(np.linspace(0.2,0.9,5))
                         ))
    cmap = mpl.colors.ListedColormap(newcolors, name='OrangeBlue')
    cmap.set_under((0.7,0.7,0.7))
    cmap.set_over(plt.cm.Purples(0.7))
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    return cmap, bounds, norm



@numba.jit
def integral(time, radius_1d, rwind_0, coriolis_deg, f_only=False):
    coriolis     = 2 * (2*np.pi/86400) * np.sin(coriolis_deg*np.pi/180)
    dr = (radius_1d[1]-radius_1d[0]) * 1e3 #meter
    nt, nr = time.size, radius_1d.size
    vorticity_1d = np.zeros(nr)
    dt = time[1] - time[0]
    twind_2d = np.zeros((nt, nr))*np.nan
    twind_2d[0,:] = 0.
    twind_2d[:,-1] = 0.
    for i in range(nt-1):
        for j in range(nr-1):
            vorticity_1d[j] = twind_2d[i,j] / radius_1d[j] / 1e3 + \
                              (twind_2d[i,j+1]-twind_2d[i,j]) / dr
            if f_only:
                tandency = -1 * rwind_0[j] * (coriolis)
            else:
                tandency = -1 * rwind_0[j] * (coriolis+vorticity_1d[j])

            twind_2d[i+1,j] = twind_2d[i,j] + tandency * dt
            if np.isnan(twind_2d[i+1,j]) or twind_2d[i+1,j]>80:
                print('ERROR ! overflow !')
                print(i, twind_2d[i,j], tandency, twind_2d[i+1,j], tandency)
                return twind_2d
    return twind_2d

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

dry_twind_last = np.zeros((nexp, nradius))*np.nan
fonly_twind_last = np.zeros((nexp, nradius))*np.nan
overflow_tab   = np.zeros((2,nexp),dtype=bool)

iexp = 1 # expnum
for iexp in range(nexp):
#for iexp in [8,13,16,17,18]:
    print(iexp)
    time = np.arange(0, 24*3*60*60+0.0001, 10)
    rwind_0 = rwind_init[1, iexp, 0] # first index is daily mean
    rwind_0 = np.where(rwind_0>0, 0, rwind_0)
    dt = time[1] - time[0]
    twind_2d = integral(time, radius_1d, rwind_0, coriolis_deg=10)
    twind_2d_fonly = integral(time, radius_1d, rwind_0, coriolis_deg=10, f_only=True)
    idx = int(86400//dt) 
    dry_twind_last[iexp,:] = twind_2d[idx:,:].mean(axis=0)
    fonly_twind_last[iexp,:] = twind_2d_fonly[idx:,:].mean(axis=0)

    # record overflow or not
    if np.any(np.isnan(twind_2d[-1,:])):
        overflow_tab[0, iexp] = True
    if np.any(np.isnan(twind_2d_fonly[-1,:])):
        overflow_tab[1, iexp] = True

    if True:
        plt.close('all')
        fig = plt.figure(figsize=(8,12))
        ax    = fig.add_axes([0.1, 0.4, 0.8, 0.5])
        axlow = fig.add_axes([0.1, 0.1, 0.8, 0.25])
        axlow_t = axlow.twinx()

        x = radius_1d.copy()
        y = time.copy() / 86400

        plt.sca(ax)
        levs = [0,1,2,3,5,10,15,20,30,40,50,60,70]
        C = plt.contour(x, y, twind_2d, levels=levs, linewidths=[2])
        plt.clabel(C)
        plt.grid(True)
        plt.title(explist[iexp])

        plt.sca(axlow)
        L0 = plt.plot(x, rwind_init[1,iexp,0,:], \
                      c='#7262AC',\
                      label='initial_radwind_vvm')
        plt.yticks(np.linspace(-5,0,5))
        plt.ylim(0.5, -5)
        plt.xlim(0, radius_1d[-1])
        plt.grid(True)

        plt.sca(axlow_t)
        L1 = plt.plot(x, dry_twind_last[iexp], \
                      c='#E25508', ls=':',\
                      label='last_tangwind_dry')
        L2 = plt.plot(x, twind_last[1,iexp,0,:],\
                      c='#E25508',\
                      label='last_tangwind_vvm')
        plt.yticks(np.linspace(0,30,5))
        plt.ylim(-3, 30)
        plt.xlim(0, radius_1d[-1])
        plt.grid(True)

        plt.legend(L0+L1+L2,
                   ['initial_radwind_vvm', \
                    'last_tangwind_dry', \
                    'last_tangwind_vvm'],
                   loc='upper right',
                   fontsize=12,
                  )
 
        plt.savefig(f'./fig/absvor_{explist[iexp]}.png',dpi=200)

idx=1
xpoint = rwind_init[idx, :, 0, :].min(axis=1)
dry_point = dry_twind_last.max(axis=1)
fonly_point = fonly_twind_last.max(axis=1)
ypoint = twind_last[idx, :, 0, :].max(axis=1)

#### draw####
cmap, bounds, norm = get_colormap()
plt.close('all')
fig = plt.figure(figsize=(10,8))
ax  = fig.add_axes([0.15, 0.15, 0.72, 0.75])
plt.sca(ax)

plt.scatter(xpoint, fonly_point, color='g', s=300, label='coriolis_only')
plt.scatter(xpoint, dry_point, color='r', s=300, label='interact')
plt.scatter(xpoint, ypoint, color='k', s=300, label='VVM')
plt.legend(loc='upper left')
plt.sca(ax)
plt.ylim(-0.6, 30)
plt.xlim(0.06, -3)
plt.grid(True)

plt.savefig('./fig/scatter.png', dpi=200)
plt.show()

