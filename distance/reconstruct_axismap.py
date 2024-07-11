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

# ---- find the ax_x index ------------
def find_index_where(dis, ax_xb):
  dis_idx = np.zeros(dis.shape,int)
  for i in range(ax_xb.size-1):
    idx = (ax_xb[i]<=dis)*(ax_xb[i+1]>dis)
    dis_idx[idx]=int(i)
  return dis_idx

def construct_AaA_2d(var, axsy_var, dis_idx):
  # construct the Axisymmertic field and Anomaly (AaA) field for 2d dataarray
  # var : 2d variables in x-y
  # axsy_var : 1d axisymmertic field
  # dis_idx : 2d index of distance in x-y
  axsy_field = axsy_var[dis_idx]
  anom_field = var - axsy_field
  return axsy_field, anom_field

def construct_AaA_3d(var3d, axsy_var2d, dis_idx):
  nz, ny, nx = var3d.shape
  axsy_field = np.zeros(var3d.shape)
  anom_field = np.zeros(var3d.shape)
  for iz in range(nz):
    axsy_field[iz,:,:] = construct_AaA_2d(\
                           var3d[iz,:,:], \
                           axsy_var2d[iz,:], \
                           dis_idx\
                         )[0]
  anom_field = var3d - axsy_field
  return axsy_field, anom_field


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

# read Axisymmertic 
nc = Dataset(f'{outdir}/axisym-{10:06d}.nc', 'r')
ax_xc = nc.variables['rc'][:].data
ax_bin = ax_xc[1] - ax_xc[0]
ax_xb = ( ax_xc[0] - ax_bin/2 ) + np.arange(ax_xc.size+1) * ax_bin
iztop = np.argmin(np.abs(zc - 18000))+1
zc    = zc[:iztop]
rho = vvmLoader.loadRHO()[:-1][:iztop]
pibar = vvmLoader.loadPIBAR()[:-1][:iztop]
nz = zc.size

# mpi for time
idxTS, idxTE = tools.get_mpi_time_span(0, nt, cpuid, nproc)
print(cpuid, idxTS, idxTE, idxTE-idxTS)

dataWriter = DataWriter(outdir)
for it in range(idxTS, idxTE):
  # ---- read the data ------------
  nc = Dataset(f'{outdir}/dis-{it:06d}.nc','r')
  angle = nc.variables['angle'][0].data
  dis   = nc.variables['dis'][0].data

  # ---- find the ax_x index ------------
  dis_idx = find_index_where(dis, ax_xb)

  # ---- read axisymmertic field

  nc_ax = Dataset(f'{outdir}/axisym-{it:06d}.nc', 'r')
  axsy_cwv = nc_ax.variables['cwv'][0, :].data
  axsy_lwp = nc_ax.variables['lwp'][0, :].data
  axsy_iwp = nc_ax.variables['iwp'][0, :].data

  # ---- read origin field ----------
  nc = Dataset(f'{config.dataPath}/wp/{exp}/wp-{it:06d}.nc', 'r')
  cwv = nc.variables['cwv'][0].data #kg/m2
  lwp = nc.variables['lwp'][0].data #kg/m2
  iwp = nc.variables['iwp'][0].data #kg/m2

  cons_cwv = construct_AaA_2d(cwv, axsy_cwv, dis_idx)
  cons_lwp = construct_AaA_2d(cwv, axsy_lwp, dis_idx)
  cons_iwp = construct_AaA_2d(cwv, axsy_iwp, dis_idx)
  del axsy_cwv, axsy_lwp, axsy_iwp
  del cwv, lwp, iwp


  axsy_radi = nc_ax.variables['u_radi'][0, :iztop].data
  axsy_tang = nc_ax.variables['u_tang'][0, :iztop].data
  axsy_w = nc_ax.variables['w'][0, :iztop].data
  dyData = vvmLoader.loadDynamic(it)
  u = dyData['u'][0, :iztop].data #3d, m/s
  v = dyData['v'][0, :iztop].data #3d, m/s
  w = dyData['w'][0, :iztop].data #3d, m/s
  u_radial, u_tangential = convert_uv2rt(u,v,angle[np.newaxis,:,:])

  cons_radi = construct_AaA_3d(u_radial,     axsy_radi, dis_idx)
  cons_tang = construct_AaA_3d(u_tangential, axsy_tang, dis_idx)
  cons_w    = construct_AaA_3d(w,           axsy_w,    dis_idx)
  del axsy_radi, axsy_tang, axsy_w
  del u, v, w, u_radial, u_tangential

  axsy_qv   = nc_ax.variables['qv'][0, :iztop].data
  axsy_qc   = nc_ax.variables['qc'][0, :iztop].data
  axsy_qr   = nc_ax.variables['qr'][0, :iztop].data
  axsy_qi   = nc_ax.variables['qi'][0, :iztop].data
  axsy_th   = nc_ax.variables['th'][0, :iztop].data
  axsy_temp = nc_ax.variables['temp'][0, :iztop].data
  axsy_mse  = nc_ax.variables['mse'][0, :iztop].data
  axsy_tv   = nc_ax.variables['tv'][0, :iztop].data
  thData = vvmLoader.loadThermoDynamic(it)
  qv = thData['qv'][0, :iztop].data #3d, kg/kg
  qc = thData['qc'][0, :iztop].data #3d, kg/kg
  qr = thData['qr'][0, :iztop].data #3d, kg/kg
  qi = thData['qi'][0, :iztop].data #3d, kg/kg
  th = thData['th'][0, :iztop].data #3d, K
  temp = calc.getTemperature(th, piBar=pibar[:,np.newaxis,np.newaxis])
  tv  = temp*(1+0.61*qv-(qr+qc+qi))
  mse = ( 1004*temp + 9.8*zc[:,np.newaxis,np.newaxis] + 2.5e6*qv ) / 1004
  cons_qv   = construct_AaA_3d(qv, axsy_qv, dis_idx)
  cons_qc   = construct_AaA_3d(qc, axsy_qc, dis_idx)
  cons_qr   = construct_AaA_3d(qr, axsy_qr, dis_idx)
  cons_qi   = construct_AaA_3d(qi, axsy_qi, dis_idx)
  cons_th   = construct_AaA_3d(th, axsy_th, dis_idx)
  cons_temp = construct_AaA_3d(temp, axsy_temp, dis_idx)
  cons_mse  = construct_AaA_3d(mse,  axsy_mse, dis_idx)
  cons_tv   = construct_AaA_3d(tv,   axsy_tv, dis_idx)
  del axsy_qv, axsy_qc, axsy_qr, axsy_qi, axsy_th, axsy_temp, axsy_mse, axsy_tv 
  del qv, qc, qr, qi, th, temp, tv, mse
  
  axsy_dtradsw   = nc_ax.variables['dtradsw'][0, :iztop].data
  axsy_dtradlw   = nc_ax.variables['dtradlw'][0, :iztop].data
  radData = vvmLoader.loadRadiation(it)
  dtradsw = radData['dtradsw'][0, :iztop].data #shortwave_heating_rate, K/s
  dtradlw = radData['dtradlw'][0, :iztop].data #longwave_heating_rate, K/s
  cons_dtradsw   = construct_AaA_3d(dtradsw, axsy_dtradsw, dis_idx)
  cons_dtradlw   = construct_AaA_3d(dtradlw, axsy_dtradlw, dis_idx)
  del axsy_dtradsw, axsy_dtradlw
  del dtradsw, dtradlw

  axsy_rain   = nc_ax.variables['rain'][0, :].data
  sufData = vvmLoader.loadSurface(it)
  rain = sufData['sprec'][0].data*3600 #2d, mm/hr
  cons_rain   = construct_AaA_2d(rain, axsy_rain, dis_idx)

  idx=0
  dic = {0:'axisym_mean', 1:'axisym_anom'}
  for idx in dic.keys():
    dataWriter.toNC(f"{dic[idx]}-{it:06d}.nc", \
      data=dict(
        u_radi=(["time", "zc", "yc", "xc"],   cons_radi[idx][np.newaxis, :, :], {'units':'m s-1'}),\
        u_tang=(["time", "zc", "yc", "xc"],   cons_tang[idx][np.newaxis, :, :], {'units':'m s-1'}),\
        w     =(["time", "zc", "yc", "xc"],   cons_w[idx][np.newaxis,:,:],      {'units':'m s-1'}),\
        qv    =(["time", "zc", "yc", "xc"],   cons_qv[idx][np.newaxis,:,:],     {'units':'kg kg-1'}),\
        qc    =(["time", "zc", "yc", "xc"],   cons_qc[idx][np.newaxis,:,:],     {'units':'kg kg-1'}),\
        qi    =(["time", "zc", "yc", "xc"],   cons_qi[idx][np.newaxis,:,:],     {'units':'kg kg-1'}),\
        qr    =(["time", "zc", "yc", "xc"],   cons_qr[idx][np.newaxis,:,:],     {'units':'kg kg-1'}),\
        th    =(["time", "zc", "yc", "xc"],   cons_th[idx][np.newaxis,:,:],     {'units':'K'}),\
        temp  =(["time", "zc", "yc", "xc"],   cons_temp[idx][np.newaxis,:,:],   {'units':'K'}),\
        mse   =(["time", "zc", "yc", "xc"],   cons_mse[idx][np.newaxis,:,:],    {'units':'K'}),\
        tv    =(["time", "zc", "yc", "xc"],   cons_tv[idx][np.newaxis,:,:],     {'units':'K'}),\
        dtradsw =(["time", "zc", "yc", "xc"], cons_dtradsw[idx][np.newaxis,:,:], {'units':'K s-1'}),\
        dtradlw =(["time", "zc", "yc", "xc"], cons_dtradlw[idx][np.newaxis,:,:], {'units':'K s-1'}),\
        rain    =(["time", "yc", "xc"],       cons_rain[idx][np.newaxis,:],      {'units':'mm hr-1'}),\
        cwv     =(["time", "yc", "xc"],       cons_cwv[idx][np.newaxis,:],       {'units':'kg/m2'}),\
        lwp     =(["time", "yc", "xc"],       cons_lwp[idx][np.newaxis,:],       {'units':'kg/m2'}),\
        iwp     =(["time", "yc", "xc"],       cons_iwp[idx][np.newaxis,:],       {'units':'kg/m2'}),\
        idx_dis =(["time", "yc", "xc"],       dis_idx[np.newaxis,:],             {'units':'idx'}),\
        dis     =(["time", "yc", "xc"],       dis[np.newaxis,:],                 {'units':'m'}),\
        angle   =(["time", "yc", "xc"],       angle[np.newaxis,:],               {'units':'radian'}),\
      ),
      coords=dict(
        time=np.ones(1),
        zc=(['zc'], zc),
        yc=(['yc'], yc),
        xc=(['xc'], xc),
      )
    )

dic = {0:'axisym_mean', 1:'axisym_anom'}
for idx in dic.keys():
  fout = open(f'{outdir}/../{dic[idx]}_{exp}.ctl','w')
  ctl=f"""
  DSET ^./{exp}/{dic[idx]}-%tm6.nc
   DTYPE netcdf
   OPTIONS template
   TITLE C.Surface variables
   UNDEF 99999.
   CACHESIZE 10000000
   XDEF {xc.size} LINEAR {xc[0]} {xc[1]-xc[0]}
   YDEF {yc.size} LINEAR {yc[0]} {yc[1]-yc[0]}
   ZDEF {zc.size} LEVELS {' '.join(['%.1f'%i for i in zc])}
   TDEF {nt} LINEAR 01JAN1998 {config.getExpDeltaT(exp)}mn
   VARS 20
    u_radi=>radi 75 t,z,y,x "m s-1" 
    u_tang=>tang 75 t,z,y,x "m s-1" 
    w=>w         75 t,z,y,x "m s-1" 
    qv=>qv       75 t,z,y,x "kg kg-1" 
    qc=>qc       75 t,z,y,x "kg kg-1" 
    qi=>qi       75 t,z,y,x "kg kg-1" 
    qr=>qr       75 t,z,y,x "kg kg-1" 
    th=>th       75 t,z,y,x "K" 
    temp=>temp   75 t,z,y,x "K" 
    mse=>mse     75 t,z,y,x "K" 
    tv=>tv       75 t,z,y,x "K" 
    dtradsw=>dtradsw 75 t,z,y,x "K s-1" 
    dtradlw=>dtradlw 75 t,z,y,x "K s-1" 
    rain=>rain  1 t,y,x "mm hr-1" 
    cwv=>cwv    1 t,y,x "kg/m2" 
    lwp=>lwp    1 t,y,x "kg/m2" 
    iwp=>iwp    1 t,y,x "kg/m2" 
    idx_dis=>idx_dis 1 t,y,x "idx"
    dis=>dis         1 t,y,x "m"
    angle=>angle     1 t,y,x "radian"
   ENDVARS"""
  fout.write(ctl)
  fout.close()
