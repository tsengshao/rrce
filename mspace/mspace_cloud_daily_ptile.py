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
from scipy import ndimage

def conditional_CWV3d(cwvbins, cwv2d, data, data2d):
  nv, nz, ny, nx = data.shape #4d, [vars, z, y, x]
  nv2, ny2, nx2  = data2d.shape #3d, [vars, y, x]
  nb = cwvbins.size-1

  output    = np.empty((nv,nz,nb), dtype=data.dtype)
  output2d    = np.empty((nv2,nb), dtype=data.dtype)

  idxmap, nsample = conditional_CWV_idx(cwvbins, cwv2d)
  for ib in range(nb):
    idx = np.nonzero(idxmap==ib)
    if len(idx[0])==0:
      continue
    output[:,:,ib] = np.sum(data[:,:,idx[0],idx[1]], axis=2)
    output2d[:,ib] = np.sum(data2d[:,idx[0],idx[1]], axis=1)
  return output, output2d, nsample

def conditional_CWV3d_cb(cwvbins, cbrange, cwv2d, qc, zc):
  nz, ny, nx = qc.shape #3d, [z, y, x]
  nb = cwvbins.size-1
  ncb = cbrange.size-1
  a = qc>1e-5

  idxzc  = conditional_zc_idx(cbrange, zc) 
  idxcb  = find_cloud_base_3d(a, idxzc)
  idxmap, nsample = conditional_CWV_idx(cwvbins, cwv2d)
  output = np.zeros((nz,ncb,nb), dtype=qc.dtype)
  idx = np.nonzero(a)

  output = speedup(output, idx, idxcb, idxmap)
  return output

@numba.njit()
def speedup(output, idx, idxcb, idxmap):
  for i in range(len(idx[0])):
    iz, iy, ix = idx[0][i], idx[1][i], idx[2][i]
    icwv = idxmap[iy,ix]
    icb  = int(idxcb[iz,iy,ix])
    #print((iz,iy,ix), 'icwv=',icwv, 'icb=',icb)
    output[iz, icb, icwv] += 1
  return output
  

@numba.njit()
def conditional_zc_idx(cbrange, zc):
  ncb = cbrange.size-1
  idxzc = np.zeros(zc.size)
  for i in range(ncb):
    idx =( (cbrange[i] <= zc) * \
           (cbrange[i+1] > zc) )
    idxzc[idx] = i
  return idxzc

@numba.njit()
def conditional_CWV_idx(cwvbins, cwv2d):
  nb = cwvbins.size-1
  ny, nx = cwv2d.shape
  nsample   = np.zeros((nb), dtype=np.int32)
  idxmap = np.zeros((ny,nx), dtype=np.int32)
  for iy in range(ny):
    for ix in range(nx):
      for ib in range(nb):
        if ( (cwvbins[ib] <= cwv2d[iy,ix]) and \
             (cwvbins[ib+1] > cwv2d[iy,ix]) ):
          nsample[ib] += 1
          idxmap[iy,ix] = ib
          break
  return idxmap, nsample

def find_cloud_base_3d(a, zc=None):
  nz, ny, nx = a.shape
  if type(zc)==type(None):
    zc = np.arange(nz)
  zc3d = np.ones(a.shape)*zc[:,np.newaxis,np.newaxis]
  s = ndimage.generate_binary_structure(3,3)*False
  s[:,1,1] = True
  labeled_array, num = ndimage.label(a, structure=s)
  mincb = ndimage.minimum(zc3d, labels=labeled_array, index=np.arange(0, num+1))
  mincb[0] = np.nan 
  cb3d = mincb[labeled_array.astype(int)]
  return cb3d

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])

nt = config.totalT[iexp]
exp = config.expList[iexp]
dtime = config.getExpDeltaT(exp)    #minutes
tspdy = int(60*24/dtime)  # number of timestep per day
nday  = int((nt-1)/tspdy+1)
print(nday, nt, tspdy)

outdir=config.dataPath+f"/mspace_daily/{exp}/"
print(outdir)

vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
thData = vvmLoader.loadThermoDynamic(0)
nz, ny, nx = thData['qv'][0].shape
xc, yc, zc = thData['xc'][:].data, thData['yc'][:].data, thData['zc'][:].data
rho = vvmLoader.loadRHO()[:-1]
pibar = vvmLoader.loadPIBAR()[:-1]
zz  = vvmLoader.loadZZ()[:-1]
zc3d = zc[:,np.newaxis,np.newaxis]*np.ones((nz,ny,nx))

ptile   = np.arange(0,101,1)

idayTS, idayTE = tools.get_mpi_time_span(0, nday, cpuid, nproc)
print(cpuid, idayTS, idayTE, idayTE-idayTS)

dataWriter = DataWriter(outdir)
for iday in range(idayTS, idayTE):
  idxTS, idxTE = (iday-1)*tspdy+1, iday*tspdy+1
  if iday==0:
    idxTS, idxTE = 0, 1
  nidxt = idxTE-idxTS
  #print(iday, idxTS, idxTE, idxTE-idxTS)

  # find ptile (cwvbins)
  cwv = np.zeros((nidxt, ny, nx))
  for it in range(idxTS, idxTE):
    it0 = it-idxTS
    nc  = Dataset(f'{config.dataPath}/wp/{exp}/wp-{it:06d}.nc', 'r')
    cwv[it0,:,:] = nc.variables['cwv'][0,:,:].data
  cwvbins = np.percentile(cwv, ptile)
  cwvall = cwv.copy()
  
  # calculate daily mspace
  varlist = ['qc', 'qi']
  unitslist = ['#', '#']

  cbrange = np.arange(0, 16000, 1000)
  cbrange[-1] = 50000
  ncb = cbrange.size-1

  mspace = np.zeros((2, nz,ncb,cwvbins.size-1))
  #msample = np.zeros(nz,cwvbins.size-1)

  for it in range(idxTS, idxTE):
    it0 = it-idxTS
    print(exp, iday, it, it0)

    time = it*dtime #minutes
    ## dyData = vvmLoader.loadDynamic(it)
    ## w = dyData['w'][0,:].data
    ## massflux = w*rho.reshape((nz,1,1))

    thData = vvmLoader.loadThermoDynamic(it)
    qc = thData['qc'][0,:].data
    qi = thData['qi'][0,:].data
    
    dum_time = datetime.now()
    dum_qc = conditional_CWV3d_cb(cwvbins, cbrange, cwvall[it0], qc, zc)
    dum_qi = conditional_CWV3d_cb(cwvbins, cbrange, cwvall[it0], qi, zc)
    mspace[0,:]+=dum_qc
    mspace[1,:]+=dum_qi

    if cpuid==0:
      print('conditional_CWV ... %.2f sec'%((datetime.now()-dum_time).total_seconds()))

  varenc = {'_FillValue': -999.0,
            'complevel': 1,
            'zlib': True}
  dim4d=['time', 'zc', 'icb', 'inum']
  dim1d=['time', 'inum']
  vardict={}
  encoding={}
  for iv in range(len(varlist)):
    vardict[varlist[iv]] = (dim4d, mspace[np.newaxis,iv,:,:,:], {'units':unitslist[iv]})
    encoding[varlist[iv]] = varenc | {'chunksizes':(1, nz, 1, cwvbins.size-1)}

  dataWriter.toNC(f"mspace_cloud-{iday:03d}days.nc", \
    data=vardict,
    coords=dict(
      time=[it],
      zc=(['zc'], zc),
      inum=(['inum'], np.arange(cwvbins.size-1)),
      icb=(['icb'], np.arange(cbrange.size-1)),
      cwvbins=(['cwvbins'], cwvbins),
      cbbins=(['cbbins'], cbrange),
      ptile=(['ptile'], ptile),
    ),
    encoding=encoding,
  )

