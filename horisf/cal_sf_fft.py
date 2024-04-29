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

def calculate_stream_function(vorticity, dx, dy):
    """
    Calculate the stream function from a given vorticity field
    using Fast Fourier Transform (FFT), considering the spatial resolution.
    
    Parameters:
    - vorticity: 2D numpy array representing the vorticity field.
    - dx: Spatial resolution in the x direction.
    - dy: Spatial resolution in the y direction.
    
    Returns:
    - stream_function: 2D numpy array representing the stream function.
    """
    # Grid dimensions
    ny, nx = vorticity.shape
    
    # Generate wave numbers for x and y directions, considering spatial resolution
    kx = np.fft.fftfreq(nx, d=dx) * 2 * np.pi  # Multiply by 2*pi to convert to radians
    ky = np.fft.fftfreq(ny, d=dy) * 2 * np.pi  # Same for y direction
    kx, ky = np.meshgrid(kx, ky)
    
    # Square of the wavenumber magnitude for each point in Fourier space
    # Avoid division by zero at k=0 by setting it to one (will be corrected later)
    k_squared = kx**2 + ky**2
    k_squared[0, 0] = 1  # Prevent division by zero
    
    # Compute Fourier transform of the vorticity
    vorticity_hat = np.fft.fft2(vorticity)
    
    # Solve for stream function in Fourier space
    stream_function_hat = vorticity_hat / k_squared
    
    # Set the mean of the stream function to zero (correcting the division by zero earlier)
    stream_function_hat[0, 0] = 0
    
    # Compute inverse Fourier transform to get the stream function in physical space
    stream_function = np.fft.ifft2(stream_function_hat).real
    
    return stream_function

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])
height=3000 #m

exp = config.expList[iexp]
nt = config.totalT[iexp]
dtime = config.getExpDeltaT(exp)
print(exp, nt)

vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
thData = vvmLoader.loadDynamic(0)
nz, ny, nx = thData['zeta'][0].shape
xc, yc, zc = thData['xc'][:].data, thData['yc'][:].data, thData['zc'][:].data
dx, dy = np.diff(xc)[0], np.diff(yc)[0]
rho = vvmLoader.loadRHO()[:-1]
rhoz = vvmLoader.loadRHOZ()[:-1]
zz = vvmLoader.loadZZ()[:-1]

iuhei=np.argmin(np.abs(zz-15000))+1
zz = zz[:iuhei]
zc = zc[:iuhei]
rho = rho[:iuhei]
rhoz = rhoz[:iuhei]
nz = zc.size

idxTS, idxTE = tools.get_mpi_time_span(0, nt, cpuid, nproc)
print(cpuid, idxTS, idxTE, idxTE-idxTS)

outdir=config.dataPath+"/horimsf/"+exp+'/'
os.system('mkdir -p '+outdir)
dataWriter = DataWriter(outdir)

for it in range(idxTS, idxTE):
  print(exp, it)
  dyData = vvmLoader.loadDynamic(it)
  zeta = dyData['zeta'][0,:iuhei,:,:]*rhoz[:,np.newaxis,np.newaxis]
  sf3d = np.zeros((nz,ny,nx))
  tt0 = datetime.now()
  for iz in range(nz):
    sf3d[iz] =  calculate_stream_function(zeta[iz], dx, dy)
  print(f'done to calculate sf3d @{it} ... {(datetime.now()-tt0).total_seconds()}')
  
  varenc = {'_FillValue': -999.0,
            'complevel': 1,
            'zlib': True}
  dim4d=['time', 'zz', 'yc', 'xc']
  encoding={'sf':{'chunksizes':(1, 1, ny, nx)} }
  dataWriter.toNC(f"horimsf-{it:06d}.nc", \
    data=dict(
      sf    =(dim4d, sf3d[np.newaxis,:,:,:], {'units':'kg m**-1s**-1'}),\
    ),
    coords=dict(
      time=(['time'], [it*dtime], {'axis':'T'}),
      zz=(['zz'], zz, {'axis':'Z'}),
      yc=(['yc'], yc, {'axis':'Y'}),
      xc=(['xc'], xc, {'axis':'X'}),
    ),  \
    encoding=encoding, \
  )

