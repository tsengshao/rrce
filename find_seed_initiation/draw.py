import numpy as np
import matplotlib.pyplot as plt

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
  

# explist, est_time = np.loadtxt('seed_time.txt', delimiter=' ', usecols=[0, 6])
## def rerange(arr):
##   return np.vstack((arr[-1], arr[:-1]))
## explist  = rerange(explist)
## est_time = rerange(est_time)


fname = 'seed_time.txt'
f = open(fname, 'r')
lines = f.read().split('\n')
explist  = []
est_time = []
reday    = []
for i in range(len(lines)):
  if (len(lines[i])<=0): continue
  exp=lines[i].split()[0]
  if (exp=='RRCE_3km_f00'): continue
  explist.append(exp)
  est_time.append(float(lines[i].split()[6]))
  if explist[-1]=='RRCE_3km_f10':
    reday.append(0)
  else:
    reday.append(int(explist[-1].split('_')[-1]))
    
explist = np.array(explist)
est_time = np.array(est_time)
reday   = np.array(reday)

plt.rcParams.update({'font.size':20,
                     'axes.linewidth':2,
                     'lines.linewidth':2})
fontcolor = 'white'
set_black_background()

ylim=[0,72]

fig, ax = plt.subplots(figsize=(12,10))
plt.plot(reday, est_time, '.', c=fontcolor, ms=30)
for i in range(reday.size):
  yyy=est_time[i] if est_time[i]<max(ylim) else max(ylim)-0.5
  plt.text(reday[i],yyy+1,f'{est_time[i]}',\
           fontweight='bold', ha='center', va='bottom', \
           color=fontcolor)
plt.xlim(reday.min()-3,reday.max()+3)
plt.yticks(np.arange(0,73,12))
plt.ylim(ylim)
plt.grid(True)
plt.ylabel('[hr]', color=fontcolor)
plt.xlabel('the restart day', color=fontcolor)
plt.title('TCseed development time',loc='left',fontweight='bold',y=1.05)
plt.title('TCseed critia:\ncon100km-Zeta '+r'$1x10^{-4}s^{-1}$', loc='right', \
          y=1.0, fontsize=15)
plt.savefig('development_time.png', dpi=250)




