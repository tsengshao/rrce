import matplotlib.pyplot as plt
import numpy as np
import sys, os
sys.path.insert(1,'../')
import config
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.calculator as calc
import util.tools as tools
from util.dataWriter import DataWriter
from mpi4py import MPI
from datetime import datetime, timedelta
import numba
from netCDF4 import Dataset

def convert_uv2rt(u,v,theta):
    u_r  = u*np.cos(theta)+v*np.sin(theta)
    u_th = -u*np.sin(theta)+v*np.cos(theta)
    return u_r, u_th

@numba.njit(parallel=False)
def ax_average3d(var3d, dis_idx, ax_nx):
    nz, ny, nx = var3d.shape
    output = np.zeros((nz,ax_nx))
    total = np.zeros((nz,ax_nx))
    for ij in range(ny):
      for ii in range(nx):
        idis = dis_idx[ij,ii]
        output[:,idis] += var3d[:,ij,ii]
        total[:, idis] += 1
    return output/total

@numba.njit(parallel=False)
def ax_average2d(var2d, dis_idx, ax_nx):
    ny, nx = var2d.shape
    output = np.zeros((ax_nx))
    total = np.zeros((ax_nx))
    for ij in range(ny):
      for ii in range(nx):
        idis = dis_idx[ij,ii]
        output[idis] += var2d[ij,ii]
        total[idis] += 1
    return output/total

# ---- find the ax_x index ------------
@numba.njit(parallel=True)
def find_index_numba(dis, xb):
  ny, nx = dis.shape
  dis_idx = np.zeros((ny,nx),int)
  for ix in numba.prange(ny):
    for iy in numba.prange(nx):
      for ip in range(xb.size-1):
        condi = (xb[ip]<=dis[iy,ix])*(xb[ip+1]>dis[iy,ix])
        if condi:
          dis_idx = int(ip)
          break
  return dis_idx

def find_index_where(dis, ax_xb):
  dis_idx = np.zeros(dis.shape,int)
  for i in range(ax_xb.size-1):
    idx = (ax_xb[i]<=dis)*(ax_xb[i+1]>dis)
    dis_idx[idx]=int(i)
  return dis_idx

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])

nt = config.totalT[iexp]
exp = config.expList[iexp]
if (cpuid==0): print(exp, nt)

center_flag = 'sf_largest_0'
outdir=config.dataPath+f"/distance/{center_flag}/{exp}/"

# read VVM coordinate
vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
thData = vvmLoader.loadThermoDynamic(0)
nz, ny, nc = thData['qv'][0].shape
xc, yc, zc = thData['xc'][:], thData['yc'][:], thData['zc'][:]
rho = vvmLoader.loadRHO()[:-1]
pibar = vvmLoader.loadPIBAR()[:-1]

# mpi for time
idxTS, idxTE = tools.get_mpi_time_span(0, nt, cpuid, nproc)
print(cpuid, idxTS, idxTE, idxTE-idxTS)

# new coordinate
ax_xb = np.arange(0, 901, 5)  #5km
ax_xc = (ax_xb[:-1]+ax_xb[1:])/2

dataWriter = DataWriter(outdir)
for it in range(idxTS, idxTE):
  # ---- read the data ------------
  nc = Dataset(f'{outdir}/dis-{it:06d}.nc','r')
  angle = nc.variables['angle'][0].data
  dis   = nc.variables['dis'][0].data

  nc = Dataset(f'{config.dataPath}/wp/{exp}/wp-{it:06d}.nc', 'r')
  cwv = nc.variables['cwv'][0].data #kg/m2
  lwp = nc.variables['lwp'][0].data #kg/m2
  iwp = nc.variables['iwp'][0].data #kg/m2

  dyData = vvmLoader.loadDynamic(it)
  u = dyData['u'][0].data #3d, m/s
  v = dyData['v'][0].data #3d, m/s
  w = dyData['w'][0].data #3d, m/s
  zeta = dyData['zeta'][0].data #3d
  u_radial, u_tangential = convert_uv2rt(u,v,angle[np.newaxis,:,:])

  thData = vvmLoader.loadThermoDynamic(it)
  qv = thData['qv'][0].data #3d, kg/kg
  qc = thData['qc'][0].data #3d, kg/kg
  qr = thData['qr'][0].data #3d, kg/kg
  qi = thData['qi'][0].data #3d, kg/kg
  th = thData['th'][0].data #3d, K
  temp = calc.getTemperature(th, piBar=pibar[:,np.newaxis,np.newaxis])
  tv  = temp*(1+0.61*qv-(qr+qc+qi))
  mse = ( 1004*temp + 9.8*zc[:,np.newaxis,np.newaxis] + 2.5e6*qv ) / 1004
  
  radData = vvmLoader.loadRadiation(it)
  dtradsw = radData['dtradsw'][0].data #shortwave_heating_rate, K/s
  dtradlw = radData['dtradlw'][0].data #longwave_heating_rate, K/s

  sufData = vvmLoader.loadSurface(it)
  rain = sufData['sprec'][0].data*3600 #2d, mm/hr

  # ---- find the ax_x index ------------
  #dis_idx_numba = find_index_numba(dis, ax_xb)
  #dis_idx_where = find_index_where(dis, ax_xb)
  dis_idx = find_index_where(dis, ax_xb)

  #axisymmertic mean
  naxxc=ax_xc.size
  ax_radi = ax_average3d(u_radial,     dis_idx, naxxc)
  ax_tang = ax_average3d(u_tangential, dis_idx, naxxc)
  ax_w    = ax_average3d(w,            dis_idx, naxxc)
  ax_zeta = ax_average3d(zeta,         dis_idx, naxxc)
  ax_qv   = ax_average3d(qv,           dis_idx, naxxc)
  ax_qc   = ax_average3d(qc,           dis_idx, naxxc)
  ax_qi   = ax_average3d(qi,           dis_idx, naxxc)
  ax_qr   = ax_average3d(qr,           dis_idx, naxxc)
  ax_th   = ax_average3d(th,           dis_idx, naxxc)
  ax_tv   = ax_average3d(tv,           dis_idx, naxxc)
  ax_temp = ax_average3d(temp,         dis_idx, naxxc)
  ax_mse  = ax_average3d(mse,          dis_idx, naxxc)
  ax_dtradsw = ax_average3d(dtradsw,   dis_idx, naxxc)
  ax_dtradlw = ax_average3d(dtradlw,   dis_idx, naxxc)

  ax_rain = ax_average2d(rain,         dis_idx, naxxc)
  ax_cwv  = ax_average2d(cwv,          dis_idx, naxxc)
  ax_lwp  = ax_average2d(lwp,          dis_idx, naxxc)
  ax_iwp  = ax_average2d(iwp,          dis_idx, naxxc)
  #ax_sample = np.histogram(dis, bins=ax_xb)[0]
  ax_sample = np.histogram(dis_idx, np.arange(0, ax_xb.size)-0.5)[0]

  dataWriter.toNC(f"axisym-{it:06d}.nc", \
    data=dict(
      u_radi=(["time", "zc", "rc"], ax_radi[np.newaxis, :, :], {'units':'m s-1'}),\
      u_tang=(["time", "zc", "rc"], ax_tang[np.newaxis, :, :], {'units':'m s-1'}),\
      w     =(["time", "zc", "rc"], ax_w[np.newaxis,:,:],      {'units':'m s-1'}),\
      zeta  =(["time", "zc", "rc"], ax_zeta[np.newaxis,:,:],   {'units':'s-1'}),\
      qv    =(["time", "zc", "rc"], ax_qv[np.newaxis,:,:],     {'units':'kg kg-1'}),\
      qc    =(["time", "zc", "rc"], ax_qc[np.newaxis,:,:],     {'units':'kg kg-1'}),\
      qi    =(["time", "zc", "rc"], ax_qi[np.newaxis,:,:],     {'units':'kg kg-1'}),\
      qr    =(["time", "zc", "rc"], ax_qr[np.newaxis,:,:],     {'units':'kg kg-1'}),\
      th    =(["time", "zc", "rc"], ax_th[np.newaxis,:,:],     {'units':'K'}),\
      temp  =(["time", "zc", "rc"], ax_temp[np.newaxis,:,:],   {'units':'K'}),\
      mse   =(["time", "zc", "rc"], ax_mse[np.newaxis,:,:],    {'units':'K'}),\
      tv    =(["time", "zc", "rc"], ax_tv[np.newaxis,:,:],     {'units':'K'}),\
      dtradsw =(["time", "zc", "rc"], ax_dtradsw[np.newaxis,:,:], {'units':'K s-1'}),\
      dtradlw =(["time", "zc", "rc"], ax_dtradlw[np.newaxis,:,:], {'units':'K s-1'}),\
      rain  =(["time", "rc"], ax_rain[np.newaxis,:],           {'units':'mm hr-1'}),\
      cwv   =(["time", "rc"], ax_cwv[np.newaxis,:],            {'units':'kg/m2'}),\
      lwp   =(["time", "rc"], ax_lwp[np.newaxis,:],            {'units':'kg/m2'}),\
      iwp   =(["time", "rc"], ax_iwp[np.newaxis,:],            {'units':'kg/m2'}),\
      sample   =(["time", "rc"], ax_sample[np.newaxis,:],      {'units':'count'}),\
    ),
    coords=dict(
      time=np.ones(1),
      zc=(['zc'], zc),
      rc=(['rc'], ax_xc),
    )
  )

fout = open(f'{outdir}/../axisym_{exp}.ctl','w')
ctl=f"""
DSET ^./{exp}/axisym-%tm6.nc
 DTYPE netcdf
 OPTIONS template
 TITLE C.Surface variables
 UNDEF 99999.
 CACHESIZE 10000000
 XDEF {ax_xc.size} LINEAR {ax_xc[0]} {ax_xc[1]-ax_xc[0]} 
 YDEF 1 LINEAR 0. .027027
 ZDEF 75 LEVELS 0 .037 .112 .194 .288 .395 .520 .667 .843 1.062 1.331 1.664 2.055 2.505 3.000 3.500 4.000 4.500 5.000 5.500 6.000 6.500 7.000 7.500 8.000 8.500 9.000 9.500 10.000 10.500 11.000 11.500 12.000 12.500 13.000 13.500 14.000 14.500 15.000 15.500 16.000 16.500 17.000 17.500 18.000 18.500 19.000 19.500 20.000 20.500 21.000 21.500 22.000 22.500 23.000 23.500 24.000 24.500 25.000 25.500 26.000 26.500 27.000 27.500 28.000 28.500 29.000 29.500 30.000 30.500 31.000 31.500 32.000 32.500 33.000
 TDEF {nt} LINEAR 01JAN1998 {config.getExpDeltaT(exp)}mn
 VARS 19
  u_radi=>radi 75 t,z,x "m s-1" 
  u_tang=>tang 75 t,z,x "m s-1" 
  w=>w         75 t,z,x "m s-1" 
  zeta=>zeta   75 t,z,x "s-1" 
  qv=>qv       75 t,z,x "kg kg-1" 
  qc=>qc       75 t,z,x "kg kg-1" 
  qi=>qi       75 t,z,x "kg kg-1" 
  qr=>qr       75 t,z,x "kg kg-1" 
  th=>th       75 t,z,x "K" 
  temp=>temp   75 t,z,x "K" 
  mse=>mse     75 t,z,x "K" 
  tv=>tv       75 t,z,x "K" 
  dtradsw=>dtradsw 75 t,z,x "K s-1" 
  dtradlw=>dtradlw 75 t,z,x "K s-1" 
  rain=>rain  1 t,x "mm hr-1" 
  cwv=>cwv    1 t,x "kg/m2" 
  lwp=>lwp    1 t,x "kg/m2" 
  iwp=>iwp    1 t,x "kg/m2" 
  sample=>sample 1 t,x "count" 
 ENDVARS"""
fout.write(ctl)
fout.close()
