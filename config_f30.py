
vvmPath  = '/work1/umbrella0c/VVM/DATA/'
dataPath = '/work1/umbrella0c/rrce2/data/'

expList  = [  
            # 0
            'cluster_f30_d10',

            # 1
            'cluster_f30_d11',
            'cluster_f30_d12',
            'cluster_f30_d13',
            'cluster_f30_d14',
            'cluster_f30_d15',

            # 6
            'cluster_f30_d16',
            'cluster_f30_d17',
            'cluster_f30_d18',
            'cluster_f30_d19',
            'cluster_f30_d20',

            # 11
            'cluster_f30_d21',
            'cluster_f30_d22',
            'cluster_f30_d23',
            'cluster_f30_d24',
            'cluster_f30_d25',

            # 16
            'cluster_f30_d26',
            'cluster_f30_d27',
            'cluster_f30_d28',
            'cluster_f30_d29',
            'cluster_f30_d30',
           ]
totalT   = [ 217 ] * len(expList)
expdict  = {
            'RRCE_3km_f00':'CTRL',    \
            'RRCE_3km_f30':'D00_on',    \
            'RRCE_3km_f00_halfwind_30':'D30half_on',\

            'cluster_f30_d10':'D10_f30',
            'cluster_f30_d11':'D11_f30',
            'cluster_f30_d12':'D12_f30',
            'cluster_f30_d13':'D13_f30',
            'cluster_f30_d14':'D14_f30',

            'cluster_f30_d15':'D15_f30',
            'cluster_f30_d16':'D16_f30',
            'cluster_f30_d17':'D17_f30',
            'cluster_f30_d18':'D18_f30',
            'cluster_f30_d19':'D19_f30',

            'cluster_f30_d20':'D20_f30',
            'cluster_f30_d21':'D21_f30',
            'cluster_f30_d22':'D22_f30',
            'cluster_f30_d23':'D23_f30',
            'cluster_f30_d24':'D24_f30',

            'cluster_f30_d25':'D25_f30',
            'cluster_f30_d26':'D26_f30',
            'cluster_f30_d27':'D27_f30',
            'cluster_f30_d28':'D28_f30',
            'cluster_f30_d29':'D29_f30',

            'cluster_f30_d30':'D30_f30',

           }

def getExpDeltaT(exp):
  expheader=exp.split('_')[0]
  if expheader == 'RCE':
    return 60 #mins
  elif expheader == 'RRCE':
    return 20 #mins
  elif expheader == 'cluster':
    return 20 #mins
