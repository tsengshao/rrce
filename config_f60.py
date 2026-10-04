
vvmPath  = '/work1/umbrella0c/VVM/DATA/'
dataPath = '/work1/umbrella0c/rrce2/data/'

expList  = [  
            # 0
#            'cluster_f60_d10',
            # 1
            'cluster_f60_d15',
            'cluster_f60_d16',
            'cluster_f60_d17',
            'cluster_f60_d18',
            'cluster_f60_d19',

            # 6
            'cluster_f60_d20',
            'cluster_f60_d21',
            'cluster_f60_d22',
            'cluster_f60_d23',
            'cluster_f60_d24',
            # 11
            'cluster_f60_d25',
            'cluster_f60_d26',
            'cluster_f60_d27',
            'cluster_f60_d28',
            'cluster_f60_d29',
            # 16
            'cluster_f60_d30',
           ]
totalT   = [ 217 ] * len(expList)
expdict  = {
            'cluster_f60_d10':'D10_f60',

            'cluster_f60_d15':'D15_f60',
            'cluster_f60_d16':'D16_f60',
            'cluster_f60_d17':'D17_f60',
            'cluster_f60_d18':'D18_f60',
            'cluster_f60_d19':'D19_f60',

            'cluster_f60_d20':'D20_f60',
            'cluster_f60_d21':'D21_f60',
            'cluster_f60_d22':'D22_f60',
            'cluster_f60_d23':'D23_f60',
            'cluster_f60_d24':'D24_f60',

            'cluster_f60_d25':'D25_f60',
            'cluster_f60_d26':'D26_f60',
            'cluster_f60_d27':'D27_f60',
            'cluster_f60_d28':'D28_f60',
            'cluster_f60_d29':'D29_f60',

            'cluster_f60_d30':'D30_f60',
           }

def getExpDeltaT(exp):
  expheader=exp.split('_')[0]
  if expheader == 'RCE':
    return 60 #mins
  elif expheader == 'RRCE':
    return 20 #mins
  elif expheader == 'cluster':
    return 20 #mins
