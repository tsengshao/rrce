import numpy as np
from netCDF4 import Dataset, num2date
import matplotlib.pyplot as plt
import matplotlib as mpl
from datetime import datetime, timedelta
import sys, os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter

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
fname_ascat='ascat_20240716_123900_metopb_61372_eps_o_250_3301_ovw.l2.nc'
fname_mtpw2 = 'comp20240716.120000.nc'
fname_h8    = '202407161240.tir.02.fld.dat'


fname_ascat = 'ascat_20240718_115700_metopb_61400_eps_o_250_3301_ovw.l2.nc'
fname_mtpw2 = 'comp20240718.120000.nc'
fname_h8    = '202407181200.tir.02.fld.dat'
lonb = [115, 145]
latb = [-5,  25]

fname_ascat = 'ascat_20240718_125100_metopc_29558_eps_o_250_3301_ovw.l2.nc'
#fname_ascat = 'ascat_20240720_125700_metopb_61429_eps_o_250_3301_ovw.l2.nc'


fdate=datetime.strptime(fname_ascat.split('_')[1], '%Y%m%d')
nc = Dataset(f'{inpath}/ascat/{fname_ascat}', 'r')
ws = nc.variables['wind_speed'][:]
wd = nc.variables['wind_dir'][:]+180 #convert to meteorological instend of ocean
wd = wd%360
qc_flag_u_nc = nc.variables['wvc_quality_flag']
qc_flag_meaning = qc_flag_u_nc.flag_meanings.split()
qc_flag_masks   = np.log2(qc_flag_u_nc.flag_masks)
qc_flag_u       = np.log2(qc_flag_u_nc[:])
u = ws * np.cos((270-wd)*np.pi/180)
v = ws * np.sin((270-wd)*np.pi/180)
lon_u = nc.variables['lon'][:]
lat_u = nc.variables['lat'][:]
time_u = nc.variables['time']
time_u = num2date(time_u[:], time_u.units)
nc.close()

# mtpw2
nc = Dataset(f'{inpath}/mtpw2/{fname_mtpw2}', 'r')
lon_tpw = nc.variables['lonArr'][:]
lat_tpw = nc.variables['latArr'][:]
tpw     = nc.variables['tpwGrid'][:,:]

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


# --- plot --
plt.rcParams.update({'font.size':20,
                     'axes.linewidth':2,
                     'lines.linewidth':2})
fontcolor = 'white'
set_black_background()

fig = plt.figure(figsize=(12,10))
projc = ccrs.PlateCarree()
ax   = fig.add_axes([0.05,0.05,0.85,0.85], projection=projc)
cax1 = fig.add_axes([0.85,0.1,0.03,0.35])
cax2 = fig.add_axes([0.85,0.55,0.03,0.35])

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
ax.coastlines(resolution='50m', color='1', linestyle='-', linewidth=3)

# twp
plt.sca(ax)
bounds = np.arange(50,71,2) #50, 60, 70
#bottom = mpl.colors.LinearSegmentedColormap.from_list(\
#             "mycmap", ['#011E97','#0246A7','#036EB7','#257ADB'])
#top = mpl.colors.LinearSegmentedColormap.from_list(\
#             "mycmap", ['#0CEBF5','1'])
bottom = mpl.colors.LinearSegmentedColormap.from_list(\
             "mycmap", ['#A3A9DC','#011E97'])
cidx = np.linspace(0,1,128)
#clist = np.vstack((bottom(cidx), top(cidx)))
clist = np.vstack((bottom(cidx)))
cmap   = mpl.colors.ListedColormap(clist, name='twp')
norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=cmap.N, extend='both')

# C = plt.pcolormesh(lon_tpw, lat_tpw, tpw, \
#                  norm=norm, cmap=cmap, \
#                  transform=projc,\
#                  )
# cb = plt.colorbar(C, extend='both', cax=cax1)
# cb.ax.set_yticks(bounds)

# h8
plt.sca(ax)
bounds = np.arange(190,240,5)
clist  = plt.cm.binary(np.linspace(0, 0.6, 256))
cmap   = mpl.colors.ListedColormap(clist, name='h8')
norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=cmap.N, extend='min')

# C = plt.contourf(lon_h8, lat_h8, h8, \
#                  levels=bounds, cmap=cmap, extend='min',\
#                  transform=projc,\
#                  )
# cb = plt.colorbar(C, extend='min', cax=cax2)
# cb.ax.set_yticks(bounds)


# -- wind speed --
plt.sca(ax)
bounds = np.arange(0,11,1) 
norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=256, extend='max')
Q = plt.quiver(lon_u,lat_u,u,v,np.where(qc_flag_u<12,ws,np.nan), \
               angles='uv',\
               scale=15, scale_units='xy', \
               norm=norm, cmap=plt.cm.Reds, \
               transform=projc,\
               )
cb = plt.colorbar(Q, cax=cax1)

# # -- quility flag --
# plt.sca(ax)
# bounds = np.append(qc_flag_masks,[23])-0.5
# norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=256)
# C    = plt.scatter(x=lon_u, y=lat_u, \
#                    s=50, c=qc_flag_u, \
#                    norm=norm, cmap=plt.cm.jet,\
#                    transform=projc,\
#                    )
# cb   = plt.colorbar(C, cax=cax1)
# cb.ax.set_yticks(bounds[:-1]+0.5)
# cb.ax.set_yticklabels(qc_flag_meaning)


## # -- wind direction --
## plt.sca(ax)
## bounds = np.arange(0,361,30) 
## norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=256)
## Q    = plt.scatter(x=lon_u, y=lat_u, \
##                    s=50, c=wd, \
##                    norm=norm, cmap=plt.cm.jet,\
##                    transform=projc,\
##                    )
## cb = plt.colorbar(Q, cax=cax1)
## cb.ax.set_yticks(bounds[::3], bounds[::3])
## 
## # -- delta time [hr] --
## ## bounds = np.arange(-2,2.1, 0.5) 
## ## norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=256)
## ## c = np.zeros(time_u.shape)
## ## basetime = datetime(2024,7,18,12)
## ## for i in range(time_u.shape[1]):
## ##   for j in range(time_u.shape[0]):
## ##     c[j,i] = (time_u[j,i]-basetime).total_seconds()/3600
## ## Q = plt.pcolormesh(lon_u, lat_u, c, norm=norm, cmap=plt.cm.PiYG)
## ## cb = plt.colorbar(Q, cax=cax1)

plt.show(block=False)

