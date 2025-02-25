import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import sys, os
sys.path.insert(1,'../')
import config
import util.tools as tools
from datetime import datetime, timedelta
from netCDF4 import Dataset
def set_black_background():
  plt.rcParams.update({
                       'axes.edgecolor': 'white',
                       'axes.facecolor': 'black',
                       'figure.edgecolor': 'black',
                       'figure.facecolor': 'black',
                       'text.color': 'white',
                       'xtick.color': 'white',
                       'ytick.color': 'white',
                       'axes.labelcolor': 'white',
                      })

plt.rcParams.update({'font.size':20,
                     'axes.linewidth':2,
                     'lines.linewidth':5})

nexp = len(config.expList)

str_kernel  = '0km'
center_flag = f'conzeta{str_kernel}_max'
method      = 'mean' #max;mean

str_kernel  = '0km'
center_flag = f'czeta{str_kernel}_domainmean'
method      = 'max'


bounds=np.array('10 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30'.split()).astype(int)
newcolors = np.vstack((
                       plt.cm.Greens(np.linspace(0.2,0.9,1)),
                       plt.cm.Oranges(np.linspace(0.2,0.9,5)),
                       plt.cm.Blues(np.linspace(0.2,0.9,5)),
                       plt.cm.Purples(np.linspace(0.2,0.9,5))
                     ))
cmap = mpl.colors.ListedColormap(newcolors, name='OrangeBlue')
cmap.set_under((0.7,0.7,0.7))
cmap.set_over(plt.cm.Purples(0.95))
norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

set_black_background()
fig = plt.figure(figsize=(12,8))
ax  = fig.add_axes([0.1, 0.1, 0.8, 0.8])
cax = fig.add_axes([0.12, 0.86, 0.35, 0.03])

plt.sca(ax)
for iexp in range(nexp):
  nt = config.totalT[iexp]
  exp = config.expList[iexp]
  if exp!='RRCE_3km_f00': nt=217
  dtime = config.getExpDeltaT(exp)    #minutes
  
  restart_day = exp[13:]
  if len(restart_day)<=0:
    restart_day = 0
  else:
    restart_day = int(restart_day)
  color = cmap(norm(restart_day))

  if exp == 'RRCE_3km_f00':
    color = (1,1,1,1)
    #restart_day = 0

  print(restart_day, exp, color)
  
  #fname=config.dataPath+f'/find_center/{center_flag}_{exp}.txt'
  fname=config.dataPath+f'/find_center/{center_flag}/{exp}.txt'
  f=open(fname,'r')
  line = f.read().split('\n')[2]
  zhei = float(line.split()[2])
  if method == 'max':
    x0, value = np.loadtxt(fname, skiprows=7, usecols=[0,2], unpack=True, max_rows=nt)
  elif method=='mean':
    x0, value = np.loadtxt(fname, skiprows=7, usecols=[0,1], unpack=True, max_rows=nt) #
  elif method=='positive_mean':
    x0, value = np.loadtxt(fname, skiprows=7, usecols=[0,8], unpack=True, max_rows=nt) #
  x = restart_day + x0*dtime/60/24 #days

  plt.plot(x, value*1e5, c=color)

CB=fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
       cax=cax, orientation='horizontal', extend='both', label='restart_day')
CB.ax.set_xticks([15,20,25,30])
#plt.ylabel(f'center SF [1e5]')
plt.ylabel(f'zeta [1e5]')
plt.ylim(100,3000)
plt.xlim(0,35)
plt.grid(True)
#plt.title(f'center SF@{zhei}m [mean]', loc='left', fontweight='bold')
plt.title(f'con{str_kernel}-zeta@{zhei}m [{method}]', loc='left', fontweight='bold')

os.system('mkdir -p ./fig')
plt.savefig(f'./fig/{center_flag}_series_{method}.png', dpi=300, transparent=True)
#plt.show()
