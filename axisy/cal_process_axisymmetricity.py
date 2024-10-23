import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import sys, os
sys.path.insert(1,'../')
import config
from mpi4py import MPI
from datetime import datetime, timedelta
from netCDF4 import Dataset
import util_axisymmetric as axisy
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.tools as tools

def write_amean_ctl(fname,exp,x,y,z,e,nt,dt):
    dset = f'^./{exp}/axmean_process-%tm6.nc'
    str_z = ' '.join(z.astype(str))
    dt = 20 #min
    x  = np.arange(x.size)*2
    #y  = np.linspace(0,1,y.size)*360
    y  = np.array([0])
    fctl=f"""
 DSET {dset} 
 DTYPE netcdf
 OPTIONS template
 TITLE C.Surface variables
 UNDEF 99999.
 CACHESIZE  1000000
 XDEF {x.size} LINEAR {x[0]} {x[1]-x[0]}
 YDEF {y.size} LINEAR {y[0]} {1}
 ZDEF {z.size} levels {str_z}
 EDEF {e.size} names {' '.join(e)}
 TDEF {nt} LINEAR 01JAN1998 {dt}mn
 VARS 3
   radi_wind_lower=>rwindlower   0  t,e,x radi_wind
   tang_wind_lower=>twindlower   0  t,e,x tang_wind
   conv_lower=>convlower         0  t,e,x convergence
 ENDVARS
"""
    fout = open(fname,'w')
    fout.write(fctl)
    fout.close()

    return 


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
if (cpuid==0): print(exp, nt)

center_flag='czeta0km_positivemean'
outdir=config.dataPath+f"/axisy/{center_flag}/{exp}/"

nc        = Dataset(f'{outdir}/axisy-000000.nc', 'r')
radius_1d = nc.variables['radius'][:]
theta_1d  = nc.variables['theta'][:]
zc        = nc.variables['zc'][:]
dtheta    = theta_1d[1]-theta_1d[0]

vvmload   = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
zz        = vvmload.loadZZ()[:zc.size]
rhoz      = vvmload.loadRHOZ()[:zc.size]
rho       = vvmload.loadRHO()[:zc.size]
izz500    = np.argmin(np.abs(zz-500))

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

varinfo = {'2d':{'vardims':['time', 'vtype', 'radius'],\
                 'chunks':(1, 1, radius_1d.size),\
                },\
           '3d':{'vardims':['time', 'vtype', 'zc', 'radius'],\
                 'chunks' :(1, 1, zc.size, radius_1d.size),\
                },\
          }
ax_theta_dict = {'2d':1,\
                 '3d':2,\
                }

if cpuid == 0:
    _ = write_amean_ctl(fname = f'{outdir}/../axmean_process_{exp}.ctl',\
                        exp   = exp,\
                        x     = radius_1d,\
                        y     = np.array([0]),\
                        z     = zc,\
                        e     = np.array(['mean', 'axisy']),\
                        nt    = nt,\
                        dt    = 20,\
                       )


for it in range(it_start, it_end):
#for it in [216]:
    nc_axsy   = Dataset(f'{outdir}/axisy-{it:06d}.nc', 'r')
    fname_out = f'{outdir}/axmean_process-{it:06d}.nc'
    os.system(f'rm -rf {fname_out}')
    nc_out  = axisy.create_nc_copy_dims(fname=fname_out, src=nc_axsy, kick_out_members=['theta'])
    _       = axisy.add_dims_into_nc(nc_out, 'vtype', vtype, ('vtype'), {'num0':'mean', 'num1':'axisymmetricity'})
    nc_out.history  = "Created " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for varname in ['radi_wind_lower', 'tang_wind_lower', 'conv_lower']:
        #if varname in nc_axsy.dimensions.keys(): continue
        #dimtype    = in_ncvar.dim_type
        #axis_theta = 2 if dimtype=='3d' else 1  #2d:1, 3d:2

        if varname == 'radi_wind_lower':
            in_ncvar     = nc_axsy.variables['radi_wind']
            rhoz4d       = rhoz[np.newaxis, :izz500+1, np.newaxis, np.newaxis]
            data         = np.trapz(in_ncvar[:,:izz500+1,:,:]*rhoz4d, 
                                    axis=1, \
                                    x=zz[:izz500+1],\
                                   ) / np.trapz(rhoz4d, axis=1, x=zz[:izz500+1])
            dimtype      = '2d'
            attrs = {'units'       : 'm/s',\
                     'lower_range' : '0 - 500m',\
                     'long_name'   : 'radial wind',\
                     'calculate_by_axisy': 'True',\
                    }

        if varname == 'tang_wind_lower':
            in_ncvar     = nc_axsy.variables['tang_wind']
            rhoz4d       = rhoz[np.newaxis, :izz500+1, np.newaxis, np.newaxis]
            data         = np.trapz(in_ncvar[:,:izz500+1,:,:]*rhoz4d, 
                                    axis=1, \
                                    x=zz[:izz500+1],\
                                   ) / np.trapz(rhoz4d, axis=1, x=zz[:izz500+1])
            dimtype      = '2d'
            attrs = {'units'       : 'm/s',\
                     'lower_range' : '0 - 500m',\
                     'long_name'   : 'tangential wind',\
                     'calculate_by_axisy': 'True',\
                    }

        if varname == 'conv_lower':
            data     = nc_out.variables['radi_wind_lower'][:, 0, :]
            data     = -1*np.gradient(data, radius_1d, axis=1)
            dimtype      = '2d'
            attrs = {'units'       : '1/s',\
                     'lower_range' : '0 - 500m',\
                     'note'        : 'this variables is processed using radi_wind_lower so it does not have axisymmetricity (set 0)',\
                     'long_name'   : 'convergence of radial wind [-div]',\
                     'calculate_by_axisy': 'False',\
                    }

        vardims  = varinfo[dimtype]['vardims']
        chunks   = varinfo[dimtype]['chunks']
        axis_theta = ax_theta_dict[dimtype]

        # calculate mean prim and gamma
        if attrs['calculate_by_axisy'].lower() == 'true':
            data_mean = np.mean(data, axis=axis_theta, keepdims=True)
            data_prim = data - data_mean
            mean_square = np.squeeze(data_mean**2, axis=axis_theta)
            prim_square_integrate = np.trapz(data_prim**2, dx=dtheta, axis=axis_theta)/(np.pi*2)
            gamma     = mean_square / ( mean_square + prim_square_integrate )
            data_mean = np.squeeze(data_mean, axis=axis_theta)
        else:
            data_mean = data.copy()
            gamma     = np.zeros(data_mean.shape)
  
        # get output variables data
        output_data = np.expand_dims( np.vstack((data_mean, gamma)), axis=0 )
  
        # write variables in to ncfiles
        var_nc  = nc_out.createVariable(varname, 'f4', vardims,\
                                        compression='zlib', complevel=4,\
                                        fill_value=-999000000,\
                                        chunksizes=chunks,\
                                       )
        for name, value in attrs.items():
            setattr(var_nc, name, value)
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

