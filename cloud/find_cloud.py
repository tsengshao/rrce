import numpy as np
import sys, os, time
sys.path.insert(1,'../')
import config
from util.vvmLoader import VVMLoader, VVMGeoLoader
import util.tools as tools
from util.dataWriter import DataWriter
from mpi4py import MPI
from datetime import datetime, timedelta
from netCDF4 import Dataset
from util_cloud_analyze import CloudRetriever
import util_axisymmetric as axisy
import matplotlib.pyplot as plt

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

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

vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
nc = vvmLoader.loadDynamic(4)
zz = vvmLoader.loadZZ()[:-1]
xc = nc.variables['xc'][:]; nx=xc.size
yc = nc.variables['yc'][:]; ny=yc.size
zc = nc.variables['zc'][:]; ny=yc.size
dx, dy = np.diff(xc)[0], np.diff(yc)[0]

outdir=config.dataPath+f"/cloud/"
os.system('mkdir -p '+outdir)

# for CloudRetriever
domain = {'x':xc/1000.,\
          'y':yc/1000.,\
          'z':zc/1000.,\
          'zz':np.concatenate(([0],zz/1000.))
         }


# find cloud and convective core cloud (w)
#for it in [2160, 1800, 1440, 720]:
for it in [216]:
    print(it)
    # --- prepare data / w in A-grid
    vvmLoader = VVMLoader(f"{config.vvmPath}/{exp}/", subName=exp)
    nc = vvmLoader.loadThermoDynamic(it)
    cld      = nc['qc'][0] + nc['qi'][0]
    cld[0,:] = 0.
    nc = vvmLoader.loadDynamic(it)
    w_raw = nc['w'][0]
    # create w in a-grid
    w = np.zeros(cld.shape)
    w[1:] = (w_raw[1:] + w_raw[:-1]) / 2
    w[0]  = w[1].copy()

    cloud = CloudRetriever(cld, threshold=1e-5, domain=domain, cc_condi={'base':2}, cores=20)
    cloud.cal_convective_core_clouds(w)

    if True:
        ### read cwv
        fname = f'../../data/wp/{exp}/wp-{it:06d}.nc'
        nc = Dataset(fname, 'r')
        cwv = nc.variables['cwv'][0,:]
        nc.close()

        ### read center and calculate distance
        # read center file
        center_flag='czeta0km_positivemean'
        fname = f'{config.dataPath}/find_center/{center_flag}/{exp}.txt'
        center_info, center_loc = axisy.read_center_file(fname, \
                                    colname=['center_x','center_y'])
        # calculate corespond x/y from r/theta
        cx = center_loc['center_x'].iloc[it]*dx
        cy = center_loc['center_y'].iloc[it]*dy
        sdis, stheta = axisy.compute_shortest_distances_vectorized(xc, yc, cx, cy)
        sdis /= 1000.

        plt.close()
        plt.figure(figsize=(10,8))
        plt.contourf(domain['x'], domain['y'], cwv, levels=np.arange(10,61,10), cmap=plt.cm.Greens)
        plt.colorbar()
        plt.contour(domain['x'], domain['y'], sdis, levels=np.arange(0,801, 100), colors=['k'])
        zyx = cloud.cld_feat['center_zyx']
        size = (cloud.cld_feat['size'][:,1])**(1/3)
        for i in range(cloud.cld_n):
            co = 'b' if cloud.cld_feat['cc_flag'][i] else 'k'
            si = size[i]
            plt.scatter(zyx[i,2], zyx[i,1], s=si, c=co)

        zyx_ccc = cloud.ccc_feat['center_zyx']
        size_ccc = cloud.ccc_feat['size'][:,1]**(1/3)
        for i in range(cloud.ccc_n):
          co  = 'r'
          si  = size_ccc[i]
          plt.scatter(zyx_ccc[i,2], zyx_ccc[i,1], s=si, c=co)
        plt.xlim(domain['x'].min(), domain['x'].max())
        plt.ylim(domain['y'].min(), domain['y'].max())
        plt.xlabel('[m]')
        plt.ylabel('[m]')
        plt.title('location of ccc[red] / cc[blue] / cld[black]')
        figdir = f'./fig_ccc/{exp}_{center_flag}/'
        os.system(f'mkdir -p {figdir}')
        plt.savefig(f'{figdir}/{it:06d}.png', dpi=200)







##  width=15
##  fout = open(f'{outdir}/{exp}.txt','w')
##  fout.write(\
##  f"""********** center info **********
##  variables: convolution zeta with {str_kernel} gaussion kernel
##  level    : {zz[iheit]} meter ( {iheit} / surface 0 )
##  threshold: domain mean
##  center index start from: 0
##  ********** center info **********
##  """)
##  fout.write(f"{'ts':>{width}s} {'mean':>{width}s} {'max':>{width}s} {'parea_ratio[%]':>{width}s} {'center_x':>{width}s} {'center_y':>{width}s} {'max_locx':>{width}s} {'max_locy':>{width}s} {'posi_mean':>{width}s}\n")
##  
