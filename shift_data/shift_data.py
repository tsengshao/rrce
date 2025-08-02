import numpy as np
import xarray as xr
import sys, os
sys.path.insert(1,'../')
import config
from datetime import datetime, timedelta
import glob, itertools
import multiprocessing

# ------------------------------------------------------------------
# A)  ───────────── helper: keep only wanted attrs ────────────────
def keep_attrs(da, allowed=("long_name", "units", "axis")):
    da.attrs = {k: v for k, v in da.attrs.items() if k in allowed}
    return da

# ------------------------------------------------------------------
# B)  ───────────── helper: sanitise the encoding dict ─────────────
ALLOWED_ENC = {
    "chunksizes", "dtype", "zlib", "shuffle", "complevel"
}  # drop _FillValue, szip, …

def build_encoding(ds):
    enc = {}
    for v in ds.data_vars:
        base = ds[v].encoding
        enc[v] = {k: base[k] for k in ALLOWED_ENC if k in base}

        # compression + chunking
        enc[v].update(dict(zlib=True, shuffle=True, complevel=4))
        suggested = {"time": 1, "zh": 1, "yh": 384, "xh": 384,
                                 "zf": 1, "yf": 384, "xf": 384}
        enc[v]["chunksizes"] = tuple(
            suggested[d] for d in ds[v].dims if d in suggested
        )
    return enc

nexp = len(config.expList)
#iexp = int(sys.argv[1])
#iexp = 0
iexp = 18
#iexp = 8

#nt = config.totalT[iexp] if iexp!=0 else 2161
nt = 217 if iexp!=0 else 2161
exp = config.expList[iexp]
dtime = config.getExpDeltaT(exp)    #minutes
outdir=config.dataPath+f"/shift/try_{exp}/"
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


    # ---------------------------------------------------------------
    # 1.  rename coordinates / dimensions to the Cartesian names
    # ---------------------------------------------------------------
    rename_map = {
        "lon": "xh", "lat": "yh",       # cell centres
        "xc":  "xf", "yc":  "yf",       # staggered u-/v-grid
        "lev": "zh", "zc":  "zf",
    }
    ds_shift = ds_shift.rename({k: v for k, v in rename_map.items() if k in ds_shift})
    
    # ---------------------------------------------------------------
    # 2.  convert metres → kilometres where needed + add axis tag
    # ---------------------------------------------------------------
    for c, ax in [("xh", "X"), ("xf", "X"),
                  ("yh", "Y"), ("yf", "Y"),
                  ("zh", "Z"), ("zf", "Z")]:
        if c in ds_shift.coords:
            if ds_shift[c].attrs.get("units", "").lower() in {"m", "metre", "meters"}:
                ds_shift[c] = ds_shift[c] / 1_000.0
            ds_shift[c].attrs.update(dict(
                long_name=f"{ax.lower()}-coordinate in Cartesian system",
                units="km",
                axis=ax,
            ))
            keep_attrs(ds_shift[c])            # strip other attrs
    
    # ---------------------------------------------------------------
    # 3.  keep ONLY long_name / units / axis on *all* variables
    # ---------------------------------------------------------------
    for v in ds_shift.variables:
        keep_attrs(ds_shift[v])
    
    # ---------------------------------------------------------------
    # 4.  build clean encoding & write file
    # ---------------------------------------------------------------
    encoding = build_encoding(ds_shift)

    fname=ncpath.split('/')[-1]
    outfile=f"{outdir}/{fname}"
    ds_shift.to_netcdf(outfile, encoding=encoding, engine="netcdf4")

# for it, prefix in itertools.product(it_list, prefix_list):
#     print(it, prefix)
#     process_main(it, prefix)

# Use multiprocessing to fetch variable data in parallel
prefix_list = ['L.Thermodynamic', 'L.Dynamic', 'C.Surface']
#prefix_list = ['wp']
it_list     = np.arange(72*0, nt, 3*6)
#it_list     = [2160]
it_list = [216]

cores = 10
with multiprocessing.Pool(processes=cores) as pool:
    results = pool.starmap(process_main, itertools.product(it_list, prefix_list) )
