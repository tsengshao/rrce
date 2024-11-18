import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import sys, os
sys.path.insert(1,'../')
import config
import util.tools as tools
from mpi4py import MPI
from datetime import datetime, timedelta
from netCDF4 import Dataset
import util_axisymmetric as axisy

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])

nt = config.totalT[iexp]
exp = config.expList[iexp]
if exp=='RRCE_3km_f00':
  nt=2521
else:
  nt=217


exp = 'rcemip_mg_square_diag2'
nt  = 217
if (cpuid==0): print(exp, nt)

center_flag='czeta0km_positivemean'
outdir=config.dataPath+f"/axisy/{center_flag}/{exp}/"

nc        = Dataset(f'{outdir}/axisy-000000.nc', 'r')
radius_1d = nc.variables['radius'][:]
theta_1d  = nc.variables['theta'][:]
zc        = nc.variables['zc'][:]
dtheta    = theta_1d[1]-theta_1d[0]

vtype     = np.array([0,1])  #0: mean, 1:gamma
def remove_theta_add_vtype_dims(in_ncvar):
  vardims = list(in_ncvar.dimensions)
  _       = vardims.pop(axis_theta)
  _       = vardims.insert(1, 'vtype')
  chunks  = in_ncvar.chunking()
  _       = chunks.pop(axis_theta)
  _       = chunks.insert(1, 1)
  return vardims, chunks


it = 216 
it_start, it_end =  tools.get_mpi_time_span(0, nt, cpuid, nproc)
print(cpuid, it_start, it_end, it_end-it_start)
comm.Barrier()

if cpuid==0:
  _ = axisy.create_axmean_ctl_from_axisy_ctl(outdir, exp)


for it in range(it_start, it_end):
  nc_axsy   = Dataset(f'{outdir}/axisy-{it:06d}.nc', 'r')
  fname_out = f'{outdir}/axmean-{it:06d}.nc'
  nc_out  = axisy.create_nc_copy_dims(fname=fname_out, src=nc_axsy, kick_out_members=['theta'])
  _       = axisy.add_dims_into_nc(nc_out, 'vtype', vtype, ('vtype'), {'num0':'mean', 'num1':'axisymmetricity'})
  
  for varname in nc_axsy.variables.keys():
    if varname in nc_axsy.dimensions.keys(): continue
    in_ncvar   = nc_axsy.variables[varname]
    dimtype    = in_ncvar.dim_type
    axis_theta = 2 if dimtype=='3d' else 1  #2d:1, 3d:2
    data = in_ncvar[:]
    data_mean = np.mean(data, axis=axis_theta, keepdims=True)
    data_prim = data - data_mean
    mean_square = np.squeeze(data_mean**2, axis=axis_theta)
    prim_square_integrate = np.trapz(data_prim**2, dx=dtheta, axis=axis_theta)/(np.pi*2)
    gamma     = mean_square / ( mean_square + prim_square_integrate )
    data_mean = np.squeeze(data_mean, axis=axis_theta)
    # get output variables data
    output_data = np.expand_dims( np.vstack((data_mean, gamma)), axis=0)
    
    # write variables in to ncfiles
    vardims, chunks = remove_theta_add_vtype_dims(in_ncvar)
    var_nc  = nc_out.createVariable(varname, 'f4', vardims,\
                                     compression='zlib', complevel=4,\
                                     fill_value=-999000000,\
                                     chunksizes=chunks,\
                                    )
    var_nc.setncatts(in_ncvar.__dict__)
    var_nc[:]  = output_data
  nc_out.close()




sys.exit()

############ quick view
# draw
x = radius_1d/1000.
y = zc/1000.
bounds = np.linspace(-20, 20, 21)

cmap   = plt.cm.jet
cmap = plt.cm.RdYlBu
norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=256, extend='both')

if dimtype=='3d':
  plt.figure()
  plt.pcolormesh(x, y, data_mean[0], cmap=cmap, norm=norm)
  plt.colorbar()
  C=plt.contour(x, y, gamma[0], levels=[0.1,0.3,0.5,0.7,0.9], colors='k')
  plt.clabel(C)
elif dimtype=='2d':
  plt.figure()
  plt.plot(x, data_mean[0], label='mean',lw=5)
  plt.ylabel(varname)
  ax2=plt.gca().twinx()
  plt.plot(x, gamma[0], label='gamma',lw=5,c='C2')
  plt.ylabel('gamma')
  plt.ylim(0,1)
  plt.legend()
plt.show()

