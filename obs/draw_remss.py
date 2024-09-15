import numpy as np
from netCDF4 import Dataset, num2date
from scipy.interpolate import RegularGridInterpolator
import matplotlib.pyplot as plt
import matplotlib as mpl
from datetime import datetime, timedelta
import sys, os
sys.path.insert(1,'../')

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter

from util_ascat.ascat_daily import ASCATDaily
from util_ascat.bytemaps import get_uv

def set_black_background():
  plt.rcParams.update({
                       'axes.edgecolor': 'white',
                       'axes.facecolor': 'black',
                       'figure.edgecolor': 'black',
                       'figure.facecolor': 'black',
                       'text.color': 'white',
                       'xtick.color': 'white',
                       'ytick.color': 'white',
                      })

# ASCAT metop-B
inpath='/data/C.shaoyu/data/'

iasc = 1 # local morning (descending) passes, local evening (ascending) passes
fname_ascat='ascatb_20240716_v02.1.gz'
fname_mtpw2 = 'comp20240716.120000.nc'
fname_h8    = '202407161240.tir.02.fld.dat'

iasc = 0
fname_ascat = 'ascatb_20240718_v02.1.gz'
fname_mtpw2 = 'comp20240718.010000.nc'
fname_h8    = '202407180050.tir.02.fld.dat'

## iasc = 1
## fname_ascat = 'ascatb_20240718_v02.1.gz'
## fname_mtpw2 = 'comp20240718.120000.nc'
## fname_h8    = '202407181200.tir.02.fld.dat'
## 
## iasc = 1
## fname_ascat = 'ascatb_20240719_v02.1.gz'
## fname_mtpw2 = 'comp20240719.120000.nc'
## fname_h8    = '202407191140.tir.02.fld.dat'
## 
iasc = 0
fname_ascat = 'ascatb_20240719_v02.1.gz'
fname_mtpw2 = 'comp20240719.000000.nc'
fname_h8    = '202407190030.tir.02.fld.dat'

lonb = [115, 145]
latb = [-5,  25]

figdate = datetime.strptime(fname_h8.split('.')[0],'%Y%m%d%H%M')
str_title_date = figdate.strftime('%Y%m%d_%H:%MZ')
str_file = figdate.strftime('%Y%m%d')+f'_{iasc}'


# ---------------------
# -- ascat, remss -----
ds = ASCATDaily(f"{inpath}/ascat/remss/{fname_ascat}", missing=-999.)

# get lon/lat:
lon = ds.variables['longitude']
lat = ds.variables['latitude']
# get region to plot:
ilon1 = np.argmin(np.abs(lonb[0]-lon))
ilon2 = np.argmin(np.abs(lonb[1]-lon))
ilat1 = np.argmin(np.abs(latb[0]-lat))
ilat2 = np.argmin(np.abs(latb[1]-lat))
slicex = slice(ilon1,ilon2+1)
slicey = slice(ilat1,ilat2+1)

ws   = ds.variables['windspd'][iasc,slicey,slicex]     #m/s
wd   = ds.variables['winddir'][iasc,slicey,slicex]     #ocean degree
whr  = ds.variables['mingmt'][iasc,slicey,slicex]/60  #hour
land = ds.variables['land'][iasc,:,:]
rainflag = ds.variables['scatflag'][iasc,slicey,slicex]
nodata = ds.variables['nodata'][iasc,slicey,slicex]
ws[nodata] = np.nan
wd[nodata] = np.nan
whr[nodata] = np.nan
rainflag[nodata] = np.nan
lon_u = lon[slicex]
lat_u = lat[slicey]
# get u and v from wspd and wdir:
u,v = get_uv(ws,wd)
bad = np.where((ws<0)+(rainflag>0.5))
u[bad] = np.nan
v[bad] = np.nan


# ---------------------
# mtpw2
nc = Dataset(f'{inpath}/mtpw2/{fname_mtpw2}', 'r')
lon_tpw  = nc.variables['lonArr'][:]
lat_tpw  = nc.variables['latArr'][:-1]
tpw      = nc.variables['tpwGrid'][:-1,:]


# ---------------------
# himawari-8 / band14 / 11.2 mum
# xdef 6000 linear 85.01  0.02
# ydef 6000 linear -59.99 0.02
lon_h8 = np.arange(6000)*0.02 + 85.01
lat_h8 = np.arange(6000)*0.02 - 59.99
lon0   = np.argmin(np.abs(lon_h8-lonb[0]))
lon1   = np.argmin(np.abs(lon_h8-lonb[1]))+1
lat0   = np.argmin(np.abs(lat_h8-latb[0]))
lat1   = np.argmin(np.abs(lat_h8-latb[1]))+1
h8     = np.fromfile(f'{inpath}/h8/{fname_h8}', \
                     np.float32).reshape(6000,6000)[::-1,:]
h8     = h8[lat0:lat1, lon0:lon1]
lon_h8 = lon_h8[lon0:lon1]
lat_h8 = lat_h8[lat0:lat1]


# ---------------------
# ---------------------
# -- plot --
plt.rcParams.update({'font.size':20,
                     'axes.linewidth':2,
                     'lines.linewidth':2})
fontcolor = 'white'
set_black_background()

fig = plt.figure(figsize=(12,10))
projc = ccrs.PlateCarree()
ax   = fig.add_axes([0.05,0.05,0.85,0.85], projection=projc)
cax1 = fig.add_axes([0.85,0.05,0.03,0.35])
cax2 = fig.add_axes([0.85,0.5, 0.03,0.35])

# coastlines and grid
box = [lonb[0]+5,lonb[1]-5,latb[0]+5,latb[1]-5]
xticks = np.arange(box[0],box[1]+1,5)
yticks = np.arange(box[2],box[3]+1,5)
ax.set_extent(box, crs=ccrs.PlateCarree())
ax.set_xticks(xticks, crs=ccrs.PlateCarree())
ax.set_xticklabels(xticks, color=fontcolor, weight='bold')
ax.set_yticks(yticks, crs=ccrs.PlateCarree())
ax.set_yticklabels(yticks, color=fontcolor, weight='bold')

lon_formatter = LongitudeFormatter()
lat_formatter = LatitudeFormatter()
ax.xaxis.set_major_formatter(lon_formatter)
ax.yaxis.set_major_formatter(lat_formatter)
ax.grid(linewidth=1, color=fontcolor, alpha=1, linestyle='--')
ax.coastlines(resolution='50m', color='#FFE000', linestyle='-', linewidth=3,zorder=101)
ax.add_feature(cfeature.LAND,zorder=100,color='0')

## # ----------
## # twp
## plt.sca(ax)
## bounds = [60, 70]
## C = plt.contour(lon_tpw, lat_tpw, tpw, \
##                 levels = bounds,\
##                 transform=projc,\
##                 linewidths=[2],\
##                 colors=['r'],\
##                 )

# ----------
# h8
plt.sca(ax)
bounds = np.arange(190,301,10)
clist  = plt.cm.binary(np.linspace(0, 1, 256))
cmap   = mpl.colors.ListedColormap(clist, name='h8')
norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=cmap.N, extend='max')

C = plt.contourf(lon_h8, lat_h8, h8, \
                 levels=bounds, cmap=cmap, extend='min',\
                 transform=projc,\
                 )
cb = plt.colorbar(C, extend='min', cax=cax1)
cb.ax.set_yticks(bounds[::2])
cb.ax.set_title('[K]',loc='left')


# ----------
## # -- rain flag --
## plt.sca(ax)
## bounds = [-0.5,0.5,1.5]
## norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=256)
## P  = plt.pcolormesh(lon_u, lat_u, rainflag, norm=norm)
## cb = plt.colorbar(P, cax=cax2)
## cb.ax.set_yticks([0,1])
## cb.ax.set_yticklabels(['no-rain', 'rain'])

# -- wind --
plt.sca(ax)
bounds = np.arange(0,11,2) 
norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=256, extend='max')
Q = plt.quiver(lon_u,lat_u,u,v,ws, \
               angles='uv',\
               scale=20, scale_units='xy', \
               norm=norm, cmap=plt.cm.Reds, \
               transform=projc,\
               )
cb = plt.colorbar(Q, cax=cax2)
cb.ax.set_title('[m/s]', loc='left')

#plt.title(f'{datestr}\nWind[m/s], Brightness Temp.[K]',loc='left',fontweight='bold')
plt.title(f'{str_title_date}\nASCAT Wind, H8 Band14 Brightness Temp.',loc='left',fontweight='bold')
plt.savefig(str_file+'.png', dpi=300, transparent=True)
plt.close('all')
#plt.show(block=False)
