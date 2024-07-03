import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(1,'../')
import config
from netCDF4 import Dataset
import matplotlib as mpl
from mpi4py import MPI

comm = MPI.COMM_WORLD
nproc = comm.Get_size()
cpuid = comm.Get_rank()

nexp = len(config.expList)
#iexp = int(sys.argv[1])
iexp = cpuid

nt = config.totalT[iexp]
exp = config.expList[iexp]
dtime = config.getExpDeltaT(exp)    #minutes
tspdy = int(60*24/dtime*5)  # number of timestep per day
nday  = int((nt-1)/tspdy)+1
print(exp, nday, nt)

datpath=config.dataPath+f"/mspace_penta/{exp}/"
figpath=f'./fig/{exp}/'
os.system(f'mkdir -p {figpath}')
nc = Dataset(datpath+f'mspace-{1:03d}penta.nc', 'r')
zc = nc.variables['zc'][:] / 1000 #km
ptile = nc.variables['ptile'][:]
xnum = nc.variables['inum'][:] + 0.5
izTop=np.argmin(np.abs(zc-13.2))
zc  = zc[:izTop]
nx, nz = xnum.size, zc.size

for iday in range(nday):
  print(iday)
  nc = Dataset(datpath+f'mspace-{iday:03d}penta.nc', 'r')
  mse = nc.variables['mse'][0,:izTop,:]
  mf  = nc.variables['massflux'][0,:izTop,:]
  sf  = np.cumsum(mf, axis=1)
  qv  = nc.variables['qv'][0,:izTop,:]
  qc  = nc.variables['qc'][0,:izTop,:]
  qi  = nc.variables['qr'][0,:izTop,:]
  w   = nc.variables['w'][0,:izTop,:]
  rain = nc.variables['rain'][0,:]
  nsample = nc.variables['nsample'][:]
  ws  = nc.variables['ws'][0,:izTop,:]
  cwvbins = nc.variables['cwvbins'][:]

  nc = Dataset(datpath+f'mspace_cloud-{iday:03d}penta.nc', 'r')
  ## freqc = nc.variables['qc'][0,:izTop,:,:].sum(axis=1)/384/384/72
  ## freqi = nc.variables['qi'][0,:izTop,:,:].sum(axis=1)/384/384/72

  th=100
  freqc = nc.variables['qc'][0,:izTop,:,:].sum(axis=1)
  dum = np.sum(freqc, axis=0, keepdims=True)
  dum[dum<th] = np.nan
  freqc /= dum 
  freqc[np.isnan(freqc)] = 0

  freqi = nc.variables['qi'][0,:izTop,:,:].sum(axis=1)
  dum = np.sum(freqi, axis=0, keepdims=True)
  dum[dum<th] = np.nan
  freqi /= dum 
  freqi[np.isnan(freqi)] = 0
  
  xleft  = (5-cwvbins[0])/2 + ptile[0]
  xright = (80-cwvbins[-1])/2 + ptile[-1]
  xlim = [xleft, xright]
  
  plt.rcParams.update({'font.size':20,
                       'axes.linewidth':2,
                       'lines.linewidth':2})
  fontcolor = 'white'
  plt.rcParams.update({
                       'axes.edgecolor': 'white',
                       'axes.facecolor': 'black',
                       'figure.edgecolor': 'black',
                       'figure.facecolor': 'black',
                       'text.color': 'white',
                       'xtick.color': 'white',
                       'ytick.color': 'white',
                      })
  fig = plt.figure(figsize=(10,12))
  ax  = plt.axes([0.1, 0.3, 0.75, 0.6])
  ax2 = plt.axes([0.1, 0.1, 0.75, 0.19])
  cax = plt.axes([0.87, 0.4, 0.02, 0.4])
  cax2 = plt.axes([0.87, 0.12, 0.02, 0.15])
  
  ###  draw upper figure / streamfunction&MSE
  # colormap
  colors = ['lightseagreen','lightgreen', 'yellowgreen', 'gold', 'orange', 'orangered']
  nodes = np.linspace(0,1,len(colors))
  cmap = mpl.colors.LinearSegmentedColormap.from_list("mycmap", list(zip(nodes, colors)))
  cmap.set_over('red')
  cmap.set_under('dodgerblue')
  
  bounds = np.arange(310, 340, 2)
  norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=256, extend='both')
  
  # draw upper figure
  plt.sca(ax)
  PC =  plt.pcolormesh(xnum, zc, mse, cmap=cmap, norm=norm)
  CB = plt.colorbar(PC, cax=cax, extend='both')

  ## CO2 = plt.contour(xnum, zc, np.log10(freqi), \
  ##                   colors=['0.9'], levels=[-5], \
  ##                   linewidths=[5], linestyles=['-'])
  ## plt.clabel(CO2, fmt='%.0f')
  ## CO2 = plt.contour(xnum, zc, np.log10(freqc),\
  ##                   colors=['w'], levels=[-5,-4,-3,-2,-1,0], \
  ##                   linewidths=[4], linestyles=['-'])
  ## plt.clabel(CO2, fmt='%.0f', levels=[-5,-3,-1])


  CO2 = plt.contourf(xnum, zc, freqi,\
                    colors=['0.9'], levels=[0.01, 1.1], \
                    alpha=0.3,)
  CO2 = plt.contourf(xnum, zc, freqi,\
                    colors=['0.9'], levels=[0.1,1.1], \
                    alpha=0.3)
  CO2 = plt.contour(xnum, zc, freqi, \
                    colors=['0.9'], levels=[0.01], \
                    linewidths=[6], linestyles=['-'],)
  #plt.clabel(CO2, fmt='%.f')

  CO2 = plt.contourf(xnum, zc, freqc,\
                    colors=['1'], levels=[0.01,1.1], \
                    alpha=0.3)
  CO2 = plt.contourf(xnum, zc, freqc,\
                    colors=['1'], levels=[0.1,1.1], \
                    alpha=0.5)
  CO2 = plt.contour(xnum, zc, freqc,\
                    colors=['1'], levels=[0.01], \
                    linewidths=[6], linestyles=['-'])
  #plt.clabel(CO2, fmt='%.f')


  CO = plt.contour(xnum, zc, sf, colors=['k'], \
                   levels=np.arange(-1,1.1,0.05).round(3), \
                   linewidths=[4])
  plt.clabel(CO, levels=[0])

  # these are matplotlib.patch.Patch properties
  props = dict(boxstyle='square,pad=0.2', facecolor=plt.gca().get_fc(), alpha=1)
  #plt.text(xnum[-1]-0.5, zc.max(), \
  plt.text(xnum[1]-0.5, zc.max()+0.1, \
           'Stream Function'+r'[kg m$^{-2}$s$^{-1}$]'+ \
           '\nfrequency of qc / qi > 0.01g/kg [0.01, 0.1]',\
           va='top', ha='left', \
           fontweight='bold', fontsize=10,\
           color=fontcolor,\
           #bbox=props,\
           zorder=10)
  
  plt.ylabel('Height [km]',color=fontcolor)
  plt.xlim(xlim)
  plt.xticks(np.linspace(0,100,11), ['' for i in range(11)])
  
  # lower figure / WindSpeed&qv
  plt.sca(ax2)
  bounds = np.arange(0,21,2)
  PC = plt.contourf(xnum, zc, qv*1e3, cmap=plt.cm.Blues, levels=bounds,extend='max')
  CB = plt.colorbar(PC, cax=cax2)
  CB.ax.set_yticks(bounds[::2])
  CO = plt.contour(xnum, zc, ws, levels=np.arange(0,30.1,1),colors=['0.3'])
  plt.clabel(CO, levels=[0, 1, 3, 5,])

  plt.ylabel('Height [km]',color=fontcolor)
  plt.yticks([0,1,2])
  plt.ylim(0,2.5)
  plt.text(xnum[0], 2.45, 'WS[m/s], qv[g/kg]', \
           va='top', ha='left', \
           fontweight='bold',\
           color='k',)
  """
  bounds = np.arange(0,5.1,0.5)
  norm = mpl.colors.BoundaryNorm(boundaries=bounds, ncolors=256, extend='both')
  
  plt.sca(ax2)
  PC = plt.pcolormesh(xnum, zc, ws, cmap=plt.cm.Blues, norm=norm)
  CB = plt.colorbar(PC, cax=cax2, extend='max')
  CB.ax.set_yticks(bounds[::2])
  CO = plt.contour(xnum, zc, qv*1e3, levels=np.arange(0,50,2),colors=['k'])
  plt.clabel(CO)
  plt.ylabel('Height [km]',color=fontcolor)
  plt.yticks([0,1,2])
  plt.ylim(0,2.5)
  plt.text(xnum[0], 2.45, 'WS[m/s], qv[g/kg]', \
           va='top', ha='left', \
           fontweight='bold',\
           color='k',)
  """
  
  plt.sca(ax2)
  plt.xlim(xlim)
  plt.xticks(np.linspace(0,100,11), \
             ['%.1f'%i for i in cwvbins[::10]], \
             fontsize=15)
  plt.xlabel('CWV [mm]',color='w')
  
  # draw title
  ax.set_title(f'{exp}\nMSE[K] / StreamFunc.'+' / cloud freq.', \
           fontsize=22, fontweight='bold', loc='left')
  ax.set_title(f'{iday*5+1:d} to {(iday+1)*5:d} days\n' if iday!=0 else f'initial({dtime:d}mins)\n', \
           fontsize=25, fontweight='bold', loc='right')
  plt.savefig(f'{figpath}/mspace_{iday:03d}penta.png', dpi=300)
  plt.close('all')


