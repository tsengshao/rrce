import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

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

def get_restart_date_from_expname(expname):
  if expname=='RRCE_3km_f10':
    return 0
  elif expname=='RRCE_3km_f00':
    return -1
  else:
    strtmp = int(expname.split('_')[-1])
    return float(strtmp)
  
df = pd.read_csv('seed_time.csv')
df['restart_day'] = df['exp_name'].apply(get_restart_date_from_expname)

plt.rcParams.update({'font.size':20,
                     'axes.linewidth':2,
                     'lines.linewidth':2})
fontcolor = 'white'
set_black_background()

ylim=[0,72]
xlim=[df['restart_day'].min()-3, df['restart_day'].max()+3]
xlim = [15-3 , df['restart_day'].max()+3]

colist = [fontcolor, '#55A4FF', '#FF8E55', '#E555FF']

fig, ax = plt.subplots(figsize=(12,10))
for idef in range(df.columns.size-2):
  plt.plot(df['restart_day']+0.1*(idef-(df.columns.size-2)/2), df.iloc[:,idef+1], '.',
           c=colist[idef], ms=30, label=df.columns[idef+1])
plt.legend()
##   plt.text(reday[i],yyy+1,f'{est_time[i]}',\
##            fontweight='bold', ha='center', va='bottom', \
##            color=fontcolor)
plt.yticks(np.arange(0,max(ylim)+1,12))
plt.xticks(np.arange(0, 31, 5))
plt.ylim(ylim)
plt.xlim(xlim)
plt.grid(True)
plt.ylabel('[hr]', color=fontcolor)
plt.xlabel('the restart day', color=fontcolor)
plt.title('TCseed development time',loc='left',fontweight='bold', y=1.05)
plt.title('TCseed critia:\ncon100km-Zeta '+r'$1x10^{-4}s^{-1}$', loc='right', \
          y=1.0, fontsize=15)
plt.savefig('development_time.png', dpi=250)
plt.show()




