import numpy as np
import sys, os
sys.path.insert(1,'../')
import config
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.calculator as calc
import util.tools as tools
from util.dataWriter import DataWriter
from netCDF4 import Dataset
from mpi4py import MPI
from datetime import datetime, timedelta
import numba

def conditional_CWV3d(cwvbins, cwv2d, data, data2d):
  nv, nz, ny, nx = data.shape #4d, [vars, z, y, x]
  nv2, ny2, nx2  = data2d.shape #3d, [vars, y, x]
  nb = cwvbins.size-1

  output    = np.empty((nv,nz,nb), dtype=data.dtype)
  output2d    = np.empty((nv2,nb), dtype=data.dtype)
  output[:] = np.nan
  output2d[:] = np.nan

  idxmap, nsample = conditional_CWV_idx(cwvbins, cwv2d)
  for ib in range(nb):
    idx = np.nonzero(idxmap==ib)
    if len(idx[0])==0:
      continue
    output[:,:,ib] = np.mean(data[:,:,idx[0],idx[1]], axis=2)
    output2d[:,ib] = np.mean(data2d[:,idx[0],idx[1]], axis=1)
  return output, output2d, nsample


@numba.njit()
def conditional_CWV_idx(cwvbins, cwv2d):
  nb = cwvbins.size-1
  ny, nx = cwv2d.shape
  nsample   = np.zeros((nb), dtype=np.int64)
  idxmap = np.zeros((ny,nx), dtype=np.int64)
  for iy in range(ny):
    for ix in range(nx):
      for ib in range(nb):
        if ( (cwvbins[ib] <= cwv2d[iy,ix]) and \
             (cwvbins[ib+1] > cwv2d[iy,ix]) ):
          nsample[ib] += 1
          idxmap[iy,ix] = ib
          break
  return idxmap, nsample

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])

nt = config.totalT[iexp]
exp = config.expList[iexp]
dtime = config.getExpDeltaT(exp)    #minutes

outdir=config.dataPath+f"/mspace/{exp}/"
print(outdir)

vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
thData = vvmLoader.loadThermoDynamic(0)
nz, ny, nx = thData['qv'][0].shape
xc, yc, zc = thData['xc'][:].data, thData['yc'][:].data, thData['zc'][:].data
rho = vvmLoader.loadRHO()[:-1]
pibar = vvmLoader.loadPIBAR()[:-1]
zz  = vvmLoader.loadZZ()[:-1]

cwvbins = np.arange(0,101,1)

idxTS, idxTE = tools.get_mpi_time_span(0, nt, cpuid, nproc)
print(cpuid, idxTS, idxTE, idxTE-idxTS)

dataWriter = DataWriter(outdir)
for it in range(idxTS, idxTE):
  print(exp, it)
  time = it*dtime #minutes
  dyData = vvmLoader.loadDynamic(it)
  u = dyData['u'][0,:].data
  v = dyData['v'][0,:].data
  w = dyData['w'][0,:].data
  massflux = w*rho.reshape((nz,1,1))
  ws = np.sqrt((u**2+v**2))

  thData = vvmLoader.loadThermoDynamic(it)
  qv = thData['qv'][0,:].data
  th = thData['th'][0,:].data
  qc = thData['qc'][0,:].data
  qi = thData['qi'][0,:].data
  qr = thData['qr'][0,:].data

  temp  = th * pibar.reshape((nz,1,1))
  mse = 1004*temp + 9.8*zc.reshape((nz,1,1)) + 2.5e6*qv
  mse /= 1004 #[K]

  sfData = vvmLoader.loadSurface(it)
  rain = sfData['sprec'][0,:].data*3600 #[mm/hr]

  nc  = Dataset(f'{config.dataPath}/wp/{exp}/wp-{it:06d}.nc', 'r')
  cwv = nc.variables['cwv'][0,:,:].data

  dum = datetime.now()
  varlist = ['w', 'massflux', 'mse', 'th', 'qv', 'qc', 'qi', 'qr', 'u', 'v', 'ws']
  unitslist = ['m/s', 'kg*kg*m/s', 'K', 'K', 'kg/kg', 'kg/kg', 'kg/kg', 'kg/kg', 'm/s', 'm/s', 'm/s']
  datalist = [w, massflux, mse, th, qv, qc, qi, qr, u, v, ws]

  var2dlist = ['rain']
  units2dlist = ['mm/hr']
  data2dlist = [rain]

  allmdata, allmdata2d, nsample = \
          conditional_CWV3d(cwvbins, cwv, \
          np.array(datalist), np.array(data2dlist))
  if cpuid==0:
    print('conditional_CWV ... %.2f sec'%((datetime.now()-dum).total_seconds()))

  varenc = {'_FillValue': -999.0,
            'complevel': 1,
            'zlib': True}
  dim3d=['time', 'zc', 'inum']
  dim1d=['time', 'inum']
  vardict={}
  encoding={}
  for iv in range(len(varlist)):
    vardict[varlist[iv]] = (dim3d, allmdata[np.newaxis,iv,:,:], {'units':unitslist[iv]})
    encoding[varlist[iv]] = varenc | {'chunksizes':(1, nz, cwvbins.size-1)}

  for iv in range(len(var2dlist)):
    vardict[var2dlist[iv]] = (dim1d, allmdata2d[np.newaxis,iv,:], {'units':units2dlist[iv]})
    encoding[var2dlist[iv]] = varenc | {'chunksizes':(1, cwvbins.size-1)}

  vardict['nsample'] = (['inum'], nsample)

  dataWriter.toNC(f"mspace-{it:06d}.nc", \
    data=vardict,
    coords=dict(
      time=[it],
      zc=(['zc'], zc),
      inum=(['inum'], np.arange(cwvbins.size-1)),
      cwvbins=(['cwvbins'], cwvbins),
    ),
    encoding=encoding,
  )

