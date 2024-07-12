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
import matplotlib.pyplot as plt

def create_nc_copy_dims(fname, src, iztop):
  # src is the netCDF.Dataset
  # fname is the string
  dst = Dataset(fname,'w')
  # copy global attributes all at once via dictionary
  dst.setncatts(src.__dict__)
  # copy dimensions
  for name, dimension in src.dimensions.items():
    size=len(dimension)
    if name=='zc': size=iztop
    dst.createDimension(
      name, (size if not dimension.isunlimited() else None))
  # copy all file data except for the excluded
  for name in src.dimensions.keys():
    variable = src.variables[name]
    data  = variable[:]
    if name=='zc': data = data[:iztop]
    x = dst.createVariable(name, variable.datatype, variable.dimensions)
    # copy variable attributes all at once via dictionary
    dst[name].setncatts(src[name].__dict__)
    dst[name][:] = data
  return dst
 

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

# read anomaly / mean field
nc = Dataset(f"{outdir}/axisym_anom-{10:06d}.nc",'r')
nz, ny, nx = nc.variables['qv'][0].shape
zc = nc.variables['zc'][:]
yc = nc.variables['yc'][:]
xc = nc.variables['xc'][:]

# read Axisymmertic 
nc = Dataset(f'{outdir}/axisym-{10:06d}.nc', 'r')
ax_xc = nc.variables['rc'][:].data
ax_bin = ax_xc[1] - ax_xc[0]
ax_xb = ( ax_xc[0] - ax_bin/2 ) + np.arange(ax_xc.size+1) * ax_bin
zc_axsy  = nc.variables['zc'][:]
iztop = np.argmin(np.abs(zc_axsy - zc.max()))+1

var_except = ['zeta', 'sample', 'time', 'zc', 'rc']
var2d_list = []
var2d_unit = []
var3d_list = []
var3d_unit = []
for varn in nc.variables.keys():
  var = nc.variables[varn]
  if varn in var_except: continue
  if len(var.shape)==3:
    var3d_list.append(varn)
    var3d_unit.append(varn)
  elif len(var.shape)==2:
    var2d_list.append(varn)
    var2d_unit.append(varn)

# mpi for time
idxTS, idxTE = tools.get_mpi_time_span(0, nt, cpuid, nproc)
print(cpuid, idxTS, idxTE, idxTE-idxTS)

dataWriter = DataWriter(outdir)
for it in range(idxTS, idxTE):
  # ---- read the data ------------
  nc_axsy = Dataset(f'{outdir}/axisym-{it:06d}.nc', 'r')
  nc_anom = Dataset(f'{outdir}/axisym_anom-{it:06d}.nc', 'r')
  dis_idx = nc_anom.variables['idx_dis'][0].data

  # ---- create nc
  fname = f'{outdir}/axisym_gamma-{it:06d}.nc'
  nc_out  = create_nc_copy_dims(fname, nc_axsy, iztop)

  for ivar in range(len(var2d_list)):
    varn = var2d_list[ivar]
    unit = var2d_unit[ivar]
    var_anom = nc_anom.variables[varn][0,:,:].data
    var_axsy = nc_axsy.variables[varn][0,:].data
    var_prim = ax_average2d(var_anom**2, dis_idx, ax_xc.size)
    gamma    = ( var_axsy**2 ) / ( var_axsy**2 + var_prim )
    
    # write variables
    x = nc_out.createVariable(varn, gamma.dtype, ('time', 'rc'))
    nc_out[varn].setncatts({'_FillValue': np.nan, 'units':unit})
    nc_out[varn][:] = gamma[np.newaxis,:]

  for ivar in range(len(var3d_list)):
    varn = var3d_list[ivar]
    unit = var3d_unit[ivar]
    var_anom = nc_anom.variables[varn][0,:,:,:].data
    var_axsy = nc_axsy.variables[varn][0,:iztop,:].data
    var_prim = ax_average3d(var_anom**2, dis_idx, ax_xc.size)
    gamma    = ( var_axsy**2 ) / ( var_axsy**2 + var_prim )
    
    # write variables
    x = nc_out.createVariable(varn, gamma.dtype, ('time', 'zc', 'rc'))
    nc_out[varn].setncatts({'_FillValue': np.nan, 'units':unit})
    nc_out[varn][:] = gamma[np.newaxis,:,:]
  nc_out.close()

fout = open(f'{outdir}/../axisym_gamma_{exp}.ctl','w')
ctl=f"""
DSET ^./{exp}/axisym_gamma-%tm6.nc
 DTYPE netcdf
 OPTIONS template
 TITLE C.Surface variables
 UNDEF 99999.
 CACHESIZE 10000000
 XDEF {ax_xc.size} LINEAR {ax_xc[0]} {ax_xc[1]-ax_xc[0]}
 YDEF 1 LINEAR 0 1
 ZDEF {nz} LEVELS {' '.join(['%.1f'%i for i in zc])}
 TDEF {nt} LINEAR 01JAN1998 {config.getExpDeltaT(exp)}mn
 VARS 17
  u_radi=>radi {nz} t,z,x "m s-1" 
  u_tang=>tang {nz} t,z,x "m s-1" 
  w=>w         {nz} t,z,x "m s-1" 
  qv=>qv       {nz} t,z,x "kg kg-1" 
  qc=>qc       {nz} t,z,x "kg kg-1" 
  qi=>qi       {nz} t,z,x "kg kg-1" 
  qr=>qr       {nz} t,z,x "kg kg-1" 
  th=>th       {nz} t,z,x "K" 
  temp=>temp   {nz} t,z,x "K" 
  mse=>mse     {nz} t,z,x "K" 
  tv=>tv       {nz} t,z,x "K" 
  dtradsw=>dtradsw {nz} t,z,x "K s-1" 
  dtradlw=>dtradlw {nz} t,z,x "K s-1" 
  rain=>rain  0 t,x "mm hr-1" 
  cwv=>cwv    0 t,x "kg/m2" 
  lwp=>lwp    0 t,x "kg/m2" 
  iwp=>iwp    0 t,x "kg/m2" 
 ENDVARS"""
fout.write(ctl)
fout.close()
