import numpy as np
import sys, os, time
sys.path.insert(1,'../')
import config
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.calculator as calc
import util.tools as tools
from util.dataWriter import DataWriter
import util_axisymmetric as axisy
import util_draw as udraw
import multiprocessing

import pandas as pd
from datetime import datetime, timedelta
from netCDF4 import Dataset
import scipy.ndimage as scimage
import matplotlib.pyplot as plt
import matplotlib as mpl

nexp = len(config.expList)
iexp = int(sys.argv[1])

exp = config.expList[iexp]
nt = config.totalT[iexp]
dtime = config.getExpDeltaT(exp)
if exp=='RRCE_3km_f00':
  nt = int(35*72+1)
else:
  nt = int(3*72+1)
print(exp, nt)

######
# read vvm cooridnate
######
vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
nc = vvmLoader.loadDynamic(4)
zz = vvmLoader.loadZZ()[:-1]
xc = nc.variables['xc'][:]; nx=xc.size
yc = nc.variables['yc'][:]; ny=yc.size
dx, dy = np.diff(xc)[0], np.diff(yc)[0]
rhoz = vvmLoader.loadRHOZ()[:-1]

######
# read center file
######
center_flag_dict = {'positive_zeta_centorid':['czeta0km_positivemean','center'],\
                    'zeta_max':['czeta0km_positivemean','max'],\
                    'con150km_zeta_max':['czeta150km_positivemean','max'],\
                    'stream_func_min':['sf_positivemean','max'],\
                   }
for key, value in center_flag_dict.items():
    center_flag = value[0]
    fname = f'{config.dataPath}/find_center/{center_flag}/{exp}.txt'
    center_info, center_loc = axisy.read_center_file(fname, \
                                colname=[f'{value[1]}_locx',f'{value[1]}_locy'])
    center_flag_dict[key].append(center_loc)

def draw_example(data, sdis, method):
    plt.close('all')
    udraw.set_figure_defalut()
    udraw.set_black_background()
    levels = [-100,-50,-30,-20,-10,-5,0,5,10,20,30,50,100]
    cmap = mpl.colors.ListedColormap(plt.cm.bwr(np.linspace(0.1,0.9,256)))
    norm = mpl.colors.BoundaryNorm(levels, cmap.N, extend='both')
    plt.figure(figsize=(10,8))
    PC=plt.pcolormesh(data,cmap=plt.cm.bwr,norm=norm)
    CB=plt.colorbar(PC, extend='both')
    CB.ax.set_yticks(levels)
    CB.ax.set_title(r'10$^{-5}$'+' '+r'$s^{-1}$', fontsize=12)
    C = plt.contour(sdis/1e3,levels=np.arange(0,451,50), colors='k')
    plt.clabel(C)

    #plt.scatter(mean_ix, mean_iy, s=100,c='g')
    plt.plot([xc.size/2, xc.size/2],[0,yc.size], 'k-')
    plt.plot([0, xc.size],[yc.size/2,yc.size/2], 'k-')
    plt.xlim(0,xc.size)
    plt.ylim(0,yc.size)
    plt.xticks(np.linspace(0,xc.size,5), np.linspace(0,xc.size,5)*dx/1000)
    plt.yticks(np.linspace(0,yc.size,5), np.linspace(0,yc.size,5)*dy/1000)
    plt.xlabel('[km]')
    plt.ylabel('[km]')

    plt.title(f'{exp} / {method}',fontweight='bold', loc='left', fontsize=15)
    if exp=='RRCE_3km_f00':
        plt.title(f'{it*dtime/60/24:.1f}day ({it:06d})', fontweight='bold', loc='right', fontsize=12)
    else:
        plt.title(f'{it*dtime/60:.1f}hr ({it:06d})', fontweight='bold', loc='right', fontsize=12)
    figPath = f'./ani_{method}/{exp}/'
    os.system(f'mkdir -p {figPath}')
    plt.savefig(f'{figPath}/{center_flag}_{it:06d}.png',dpi=250)
    plt.show(block=True)


def calculate_results(it,kernel_radius, method, iheit,dodraw=False):
    # read vvm data
    nc = vvmLoader.loadDynamic(it)
    u  = nc.variables['u'][0,:iheit,:,:].mean(axis=0)
    v  = nc.variables['v'][0,:iheit,:,:].mean(axis=0)
    if method=='convective_mass_flux':
        wrho  = nc.variables['w'][0,:iheit,:,:]*\
                    rhoz[:iheit,np.newaxis,np.newaxis]
        wrho  = np.where(wrho>0,wrho,0)
        wrho  = np.trapz(wrho,x=zz[:iheit],axis=0)
        data = wrho.copy()
    elif method=='total_mass_flux':
        wrho  = nc.variables['w'][0,:iheit,:,:]*\
                    rhoz[:iheit,np.newaxis,np.newaxis]
        wrho  = np.trapz(wrho,x=zz[:iheit],axis=0)
        data = wrho.copy()
    elif method=='convergence':
        # convergence
        dudx = np.gradient(u, dx, axis=-1)
        dudx[..., 0] =  (u[...,1] - u[...,-1])/2/dx
        dudx[...,-1] =  (u[...,0] - u[...,-2])/2/dx
        dvdy = np.gradient(v, dy, axis=-2)
        dvdy[...,0, :] =  (u[...,1,:] - u[...,-1,:])/2/dy
        dudx[...,-1,:] =  (u[...,0,:] - u[...,-2,:])/2/dy
        con = -1*dudx-1*dvdy
        data = con.copy()
    else:
        sys.exit('ERROR!!: please input correct method')

    # calculate corespond x/y from r/theta
    # mean convergence
    results = {}
    for key, value in center_flag_dict.items():
        cx = value[2].iloc[it,0]*dx
        cy = value[2].iloc[it,1]*dy
        sdis, stheta = axisy.compute_shortest_distances_vectorized(xc, yc, cx, cy)
        idx = (sdis<=kernel_radius)
        results[key] = np.mean(data[idx])

    if dodraw:
        draw_example(data, sdis, method)

    return it, results

#####
# prepare center filter
######
kernel_radius   = 300*1e3 #meter
kernel_str      = f'{kernel_radius/1e3:.0f}km'
target_lev = 500.
iheit = np.argmin(np.abs(zz-target_lev))

method = 'convective_mass_flux'
scale  = 1
units  = 'kg/m/s'

# method = 'total_mass_flux'
# scale  = 1
# units  = 'kg/m/s'

method = 'convergence'
scale  = 1e-5
units  = r'$10^{-5}$ $m^{2}s^{-2}$'

figPath = f'./fig_upward_proxy/'
os.system(f'mkdir -p {figPath}')
fname = f'{config.dataPath}/find_center/center_{method}/{exp}.pkl'

if not os.path.isfile(fname):
    cores = 10
    records = pd.DataFrame(columns=center_flag_dict.keys())
    # Use multiprocessing to fetch variable data in parallel
    with multiprocessing.Pool(processes=cores) as pool:
        dum = pool.starmap(calculate_results, [(it,kernel_radius,method,iheit,False) for it in range(nt)])
    for i in range(len(dum)):
        records.loc[dum[i][0]] = dum[i][1]
    records = records.sort_index()
    fdir=os.path.dirname(fname)
    os.system(f'mkdir -p {fdir}')
    records.to_pickle(fname)
else:
    records = pd.read_pickle(fname)

######
## draw all timeseries
######
udraw.set_figure_defalut()
plt.rcParams.update({ 'lines.linewidth':2})
x = np.arange(nt)/72
fig, ax = plt.subplots(figsize=(16,7))
plt.plot(x, records/scale)
plt.legend(records.columns)
plt.title(f'{config.expdict[exp]} / {method}', loc='left', fontweight='bold')
plt.title(f'region radius: {kernel_str}\nlowlevel 0-{target_lev:.0f}m', loc='right', fontweight='bold')
plt.xlabel('days')
plt.ylabel(f'{units}')
plt.tight_layout()
plt.savefig(f'{figPath}/{exp}_{method}_{target_lev:.0f}m_all.png',dpi=250)

######
## draw penta version
######
plt.rcParams.update({ 'lines.linewidth':5})
penta2dy   = 72*5
nt_penta   = nt//penta2dy
penta_df = pd.DataFrame(index=np.arange(nt_penta),\
                          columns=center_flag_dict.keys())
for i in range(nt_penta):
    i0 = int(penta2dy*(i))
    i1 = int(penta2dy*(i+1))+1
    penta_df.iloc[i] = np.mean(records.iloc[i0:i1,:], axis=0)

x = np.arange(nt_penta)
x_str = [f'{i*5:.0f}~{(i+1)*5:.0f}\ndays' for i in range(nt_penta)]
fig, ax = plt.subplots(figsize=(16,7))
plt.plot(x, penta_df/scale)
plt.legend(records.columns)
plt.title(f'{config.expdict[exp]} / {method}', loc='left', fontweight='bold')
plt.title(f'region radius: {kernel_str}\nlowlevel 0-{target_lev:.0f}m', loc='right', fontweight='bold')
plt.xticks(x, x_str,fontsize=15)
plt.ylabel(f'{units}')
plt.tight_layout()
plt.savefig(f'{figPath}/{exp}_{method}_{target_lev:.0f}m_penta.png',dpi=250)
plt.show()
plt.close('all')
    
