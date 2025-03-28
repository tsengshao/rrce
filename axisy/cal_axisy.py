import numpy as np
import sys, os
sys.path.insert(1,'../')
import config
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.tools as tools
from mpi4py import MPI
from datetime import datetime, timedelta
import util_axisymmetric as axisy


comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
iexp = int(sys.argv[1])

nt = config.totalT[iexp]
exp = config.expList[iexp]
if exp!='RRCE_3km_f00':
  nt=217
else:
  nt=2521
if (cpuid==0): print(exp, nt)

center_flag='czeta0km_positivemean'
outdir=config.dataPath+f"/axisy/{center_flag}/{exp}/"
os.system(f'mkdir -p {outdir}')

# read VVM coordinate
vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
thData = vvmLoader.loadThermoDynamic(0)
nz, ny, nx = thData['qv'][0].shape
xc, yc, zc = thData['xc'][:], thData['yc'][:], thData['zc'][:]
dx, dy = np.diff(xc)[0], np.diff(yc)[0]
dtime  = 20  #minutes
rho = vvmLoader.loadRHO()[:-1]
pibar = vvmLoader.loadPIBAR()[:-1]
pbar = vvmLoader.loadPBAR()[:-1]
idxTOP = np.argmin(np.abs(zc-18000))
zc = zc[:idxTOP]
nz = zc.size


# create r/theta coordinate
radius_1d = np.arange(0, (nx*dx)//2, dx) + dx/2
theta_1d  = np.arange(0,360,0.5) + 0.25
theta_1d  = theta_1d*np.pi/180.
radius, theta = np.meshgrid(radius_1d, theta_1d)

# read center file
fname = f'{config.dataPath}/find_center/{center_flag}/{exp}.txt'
center_info, center_loc = axisy.read_center_file(fname, \
                            colname=['center_locx','center_locy'])
speed_x = np.gradient(center_loc['center_locx'])*dx/(dtime*60) # m/s
speed_y = np.gradient(center_loc['center_locy'])*dy/(dtime*60) # m/s


it_start, it_end =  tools.get_mpi_time_span(0, nt, cpuid, nproc)
#it_start, it_end =  tools.get_mpi_time_span(212, 217, cpuid, nproc)
print(cpuid, it_start, it_end, it_end-it_start)
comm.Barrier()

for it in np.arange(it_start, it_end):
#for it in [216]:
    # calculate corespond x/y from r/theta
    cx = center_loc['center_locx'].iloc[it]*dx
    cy = center_loc['center_locy'].iloc[it]*dy
    x_polar, y_polar  =  axisy.convert_rth2xy(\
                          radius, theta, \
                          cx, cy, \
                          nx*dx, ny*dy, \
                         )
    sdis, stheta = axisy.compute_shortest_distances_vectorized(xc, yc, cx, cy)
    
    fname  = f'{outdir}/axisy-{it:06d}.nc'
    os.system(f'rm -rf {fname}')
    axisyWriter = axisy.ncWriter(fname)
    axisyWriter.create_coordinate(t_min = it*dtime,\
                                z_zc_m = zc,\
                                y_theta_rad = theta_1d, \
                                x_radius_m  = radius_1d, \
                                center_x_grid = cx/dx, \
                                center_y_grid = cy/dy, \
                               )
    
    # read data
    dataCollector = axisy.data_collector(exp, it, idztop=idxTOP+1)
    print(speed_x[it], speed_y[it])
    radial_dict, tangential_dict = \
        dataCollector.get_radial_and_tangential_wind(\
#            stheta, speed_x[it], speed_y[it]\
            stheta, 0,0,\
        )
    
    # regrid 2d datasets
    for varname in dataCollector.var2dlist:
    #for varname in []:
      data_dict = dataCollector.get_variable(varname)
      rawdata   = data_dict.pop('data')
      positive  = data_dict.pop('positive')
      data_dict['ens'] = 9
      data_polar = axisy.regrid_data_c2p(xc_1d = xc,\
                                 yc_1d = yc,\
                                 rawdata = rawdata,\
                                 x_polar = x_polar,\
                                 y_polar = y_polar,\
                                 always_positive = positive, \
                                 ens     = data_dict['ens'], \
                                )
      axisyWriter.put_variables(varname, data_polar, data_dict)
    
    # regrid 3d datasets
    for varname in dataCollector.var3dlist + ['radi_wind', 'tang_wind']:
    #for varname in ['radi_wind', 'tang_wind']:
      data_polar = np.zeros((nz, theta_1d.size, radius_1d.size))
    
      if varname=='radi_wind':
        data_dict = radial_dict
      elif varname=='tang_wind':
        data_dict = tangential_dict
      else:
        data_dict = dataCollector.get_variable(varname)
      rawdata = data_dict.pop('data')
      positive  = data_dict.pop('positive')
      data_dict['ens'] = 9

      for iz in range(nz):
        data_polar[iz] = axisy.regrid_data_c2p(xc_1d = xc,\
                                   yc_1d = yc,\
                                   rawdata = rawdata[iz],\
                                   x_polar = x_polar,\
                                   y_polar = y_polar,\
                                   always_positive = positive, \
                                   ens     = data_dict['ens'], \
                                  )
   
      if varname in []:
        iz = 8
        axisy.axisy_quick_view(x_polar, y_polar, radius, theta, data_polar[iz],\
                               xc, yc, rawdata[iz], cx, cy, varname,\
                               savefig=False, \
                               savedir='./fig_example/', \
                               saveheader=f'en{data_dict["ens"]}_{varname}_{zc[iz]:.0f}_{it:06d}',\
                              )
      axisyWriter.put_variables(varname, data_polar, data_dict)
    axisyWriter.close_ncfile()

    if cpuid==0 and it==it_start:
        print(f'cpuid={cpuid}, write ctl file ... ')
        axisyWriter.write_ctl(fname = f'{outdir}/../axisy_{exp}.ctl',\
                                exp = exp,\
                                  x = radius_1d*1e-3,\
                                  y = theta_1d,\
                                  z = zc,\
                                  nt = nt,\
                                  dt = dtime\
                             )

