
vvmPath  = '/work1/umbrella0c/VVM/DATA/'
dataPath = '/work1/umbrella0c/rrce2/data/'

expList  = [  
            # 0
            'cluster_f10_d10_HomogRad',

            # 1
            'cluster_f10_d15_HomogRad',
            'cluster_f10_d16_HomogRad',
            'cluster_f10_d17_HomogRad',
            'cluster_f10_d18_HomogRad',
            'cluster_f10_d19_HomogRad',

            # 6
            'cluster_f10_d20_HomogRad',
            'cluster_f10_d21_HomogRad',
            'cluster_f10_d22_HomogRad',
            'cluster_f10_d23_HomogRad',
            'cluster_f10_d24_HomogRad',

            'cluster_f10_d25_HomogRad',
            'cluster_f10_d26_HomogRad',
            'cluster_f10_d27_HomogRad',
            'cluster_f10_d28_HomogRad',
            'cluster_f10_d29_HomogRad',

            'cluster_f10_d30_HomogRad',
           ]
totalT   = [ 217 ] * len(expList)
expdict  = {
            'RRCE_3km_f00':'CTRL',    \
            'RRCE_3km_f10':'D00_on',    \
            'RRCE_3km_f00_halfwind_30':'D30half_on',\

            'cluster_f10_d10_HomogRad':'D10_f10_HRad',

            'cluster_f10_d15_HomogRad':'D15_f10_HRad',
            'cluster_f10_d16_HomogRad':'D16_f10_HRad',
            'cluster_f10_d17_HomogRad':'D17_f10_HRad',
            'cluster_f10_d18_HomogRad':'D18_f10_HRad',
            'cluster_f10_d19_HomogRad':'D19_f10_HRad',

            'cluster_f10_d20_HomogRad':'D20_f10_HRad',
            'cluster_f10_d21_HomogRad':'D21_f10_HRad',
            'cluster_f10_d22_HomogRad':'D22_f10_HRad',
            'cluster_f10_d23_HomogRad':'D23_f10_HRad',
            'cluster_f10_d24_HomogRad':'D24_f10_HRad',

            'cluster_f10_d25_HomogRad':'D25_f10_HRad',
            'cluster_f10_d26_HomogRad':'D26_f10_HRad',
            'cluster_f10_d27_HomogRad':'D27_f10_HRad',
            'cluster_f10_d28_HomogRad':'D28_f10_HRad',
            'cluster_f10_d29_HomogRad':'D29_f10_HRad',

            'cluster_f10_d30_HomogRad':'D30_f10_HRad',

           }

def getExpDeltaT(exp):
  expheader=exp.split('_')[0]
  if expheader == 'RCE':
    return 60 #mins
  elif expheader == 'RRCE':
    return 20 #mins
  elif expheader == 'cluster':
    return 20 #mins
