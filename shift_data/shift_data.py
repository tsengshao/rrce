import numpy as np
import xarray as xr
import sys, os
sys.path.insert(1,'../')
import config
from datetime import datetime, timedelta
import glob, itertools
import multiprocessing

nexp = len(config.expList)
#iexp = int(sys.argv[1])
#iexp = 0
iexp = 18
#iexp = 8

#nt = config.totalT[iexp] if iexp!=0 else 2161
nt = 217 if iexp!=0 else 2161
exp = config.expList[iexp]
dtime = config.getExpDeltaT(exp)    #minutes
outdir=config.dataPath+f"/shift/{exp}/"
os.system(f'mkdir -p {outdir}')

## read center data
txtpath=f"{config.dataPath}/find_center/czeta0km_positivemean/{exp}.txt"
cx, cy = np.loadtxt(txtpath, skiprows=7, usecols=[4,5], unpack=True)


#it   = 72*30
#prefix='L.Thermodynamic'

def process_main(it, prefix):
    print(f'{it} ... {prefix}')
    if prefix=='wp':
        ncpath=f"{config.dataPath}/wp/{exp}/wp-{it:06d}.nc"
        xname='xc'
        yname='yc'
    else:
        path=f"{config.vvmPath}/{exp}/archive"
        ncpath=f"{path}/{exp}.{prefix}-{it:06d}.nc"
        xname='lon'
        yname='lat'
    ds = xr.open_dataset(ncpath, decode_cf=True)
    if 'lev' in ds.coords:
        ds = ds.sel({'lev':slice(None,20)})
        ds['lev'].attrs.update({
            "units": "km",
            "long_name": "vertical level (kilometres)",
        })
    
    shift_x = int(ds[xname].size/2 - cx[it])
    shift_y = int(ds[yname].size/2 - cy[it])
    ds_shift = ds.roll({yname:shift_y,xname:shift_x}, roll_coords=False)
    #ds_shift = ds.roll(lat=shift_y, lon=shift_x, roll_coords=False)
    
    # create attributes
    enc = {}
    for v in ds.data_vars:
        enc[v] = ds[v].encoding.copy()

        enc[v].update({
            "zlib": True,
            "complevel": 1,                # 1–9, higher = smaller but slower
            "shuffle": False,               # improves compression of floating‑point data
        })
        suggested_chunks = {
            "time": 1,
            'lev': 1,           # or ds.dims[args.z_name] if ≤10
            'lat': 384,
            'lon': 384,
            'xc': 384,
            'yc': 384,
        }
        for pop_key in ['szip', 'zstd', 'bzip2', 'blosc', 'contiguous', 'original_shape']:
        #for pop_key in ['original_shape']:
            if pop_key in enc[v]:
                enc[v].pop(pop_key)
        var_dims = ds[v].dims
        enc[v]["chunksizes"] = tuple(
            suggested_chunks[d] for d in var_dims if d in suggested_chunks
        )
    outdir=config.dataPath+f"/shift/{exp}/"
    fname=ncpath.split('/')[-1]
    outfile=f"{outdir}/{fname}"
    ds_shift.to_netcdf(outfile, encoding=enc, engine="netcdf4")

# for it, prefix in itertools.product(it_list, prefix_list):
#     print(it, prefix)
#     process_main(it, prefix)

# Use multiprocessing to fetch variable data in parallel
prefix_list = ['L.Thermodynamic', 'L.Dynamic', 'C.Surface']
#prefix_list = ['wp']
it_list     = np.arange(72*0, nt, 3*6)
#it_list     = [2160]

cores = 10
with multiprocessing.Pool(processes=cores) as pool:
    results = pool.starmap(process_main, itertools.product(it_list, prefix_list) )
