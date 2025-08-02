import numpy as np
import xarray as xr
import sys, os
sys.path.insert(1,'../')
import config
from datetime import datetime, timedelta
import glob, itertools
import multiprocessing

def keep_attrs(da, allowed=("long_name", "units", "axis")):
    da.attrs = {k: v for k, v in da.attrs.items() if k in allowed}
    return da

nexp = len(config.expList)
#iexp = int(sys.argv[1])
iexp = 0
#iexp = 18
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
    else:
        path=f"{config.vvmPath}/{exp}/archive"
        ncpath=f"{path}/{exp}.{prefix}-{it:06d}.nc"
    ds = xr.open_dataset(ncpath, decode_cf=True)

    # modify time
    if "time" in ds.coords:
        day_offset = 693_595                                        # 常數差
        t = ds['time'].values
        t_minutes = (t.astype('datetime64[m]') - np.datetime64('1900-01-01')).astype('int64')
        ds["time"] = (t_minutes / 1440)             
    
        ds["time"].attrs.update({
            "units": "days since 0001-01-01",
            "calendar": "proleptic_gregorian",
            "axis": "T",
            "long_name": ds["time"].attrs.get("long_name", "time")
        })
    
        ds["time"].encoding.update({
            "units": "days since 0001-01-01",
            "calendar": "proleptic_gregorian"
        })

    # change coordinate
    rename_dims={'lon':'xc', 'lat':'yc', 'lev':'zc'}
    axis_list={'xc':'X', 'yc':'Y', 'zc':'Z'}
    for dsdim in ds.coords:
        #for rdim, cdim in rename_dims.items():
        if dsdim in rename_dims.keys():
            rdim, cdim = dsdim, rename_dims[dsdim]
            ds = ds.swap_dims({rdim:cdim})
            ds = ds.drop_vars(rdim)
            ds = ds.set_coords([cdim])

    if 'zc' in ds.coords:
        ds['zc'] = ds['zc']/1000.
        ds = ds.sel({'zc':slice(None,20)})
    ds['xc'] = ds['xc']/1000.
    ds['yc'] = ds['yc']/1000.
    
    shift_x = int(ds['xc'].size/2 - cx[it])
    shift_y = int(ds['yc'].size/2 - cy[it])
    ds_shift = ds.roll({'yc':shift_y,'xc':shift_x}, roll_coords=False)
    #ds_shift = ds.roll(lat=shift_y, lon=shift_x, roll_coords=False)

    for c in ds_shift.coords:
        if c in axis_list.keys():
            ds_shift[c].attrs.update(dict(
                units="km",
                axis=axis_list[c],
            ))
        keep_attrs(ds_shift[c])            # strip other attrs
    
    # create attributes
    enc = {}
    for v in ds.data_vars:
        enc[v] = ds[v].encoding.copy()

        enc[v].update({
            "zlib": True,
            "complevel": 3,                # 1–9, higher = smaller but slower
            "shuffle": False,               # improves compression of floating‑point data
        })
        suggested_chunks = {
            "time": 1,
            'zc': 1,           # or ds.dims[args.z_name] if ≤10
            'xc': 384,
            'yc': 384,
        }
        if v in ['cwv', 'iwp', 'lwp']:
            ds_shift[v].attrs.update(units='kg/m2')
            
        keep_attrs(ds_shift[v])            # strip other attrs
        var_dims = ds[v].dims
        enc[v]["chunksizes"] = tuple(
            suggested_chunks[d] for d in var_dims if d in suggested_chunks
        )
        for pop_key in ['szip', 'zstd', 'bzip2', 'blosc', 'contiguous', 'original_shape']:
        #for pop_key in ['original_shape']:
            if pop_key in enc[v]:
                enc[v].pop(pop_key)

    outdir=config.dataPath+f"/shift/{exp}/"
    fname=ncpath.split('/')[-1]
    outfile=f"{outdir}/{fname}"
    ds_shift.to_netcdf(outfile, encoding=enc, engine="netcdf4")


# Use multiprocessing to fetch variable data in parallel
prefix_list = ['L.Thermodynamic', 'L.Dynamic', 'C.Surface', 'wp']
#prefix_list = ['wp']
it_list     = np.arange(72*0, nt, 3)
#it_list     = [2160]

# for it, prefix in itertools.product(it_list, prefix_list):
#     print(it, prefix)
#     process_main(it, prefix)

cores = 10
with multiprocessing.Pool(processes=cores) as pool:
    results = pool.starmap(process_main, itertools.product(it_list, prefix_list) )
