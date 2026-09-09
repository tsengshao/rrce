
vvmPath  = '/work1/umbrella0c/VVM/DATA/'
dataPath = '/work1/umbrella0c/rrce2/data/'

expList  = [  
            # 0
            'cluster_f10_d10_HomogRadCTRL',

            # 1
            'cluster_f10_d11_HomogRadCTRL',
            'cluster_f10_d12_HomogRadCTRL',
            'cluster_f10_d13_HomogRadCTRL',
            'cluster_f10_d14_HomogRadCTRL',
            'cluster_f10_d15_HomogRadCTRL',

            # 6
            'cluster_f10_d16_HomogRadCTRL',
            'cluster_f10_d17_HomogRadCTRL',
            'cluster_f10_d18_HomogRadCTRL',
            'cluster_f10_d19_HomogRadCTRL',
            'cluster_f10_d20_HomogRadCTRL',

            # 11
            'cluster_f10_d21_HomogRadCTRL',
            'cluster_f10_d22_HomogRadCTRL',
            'cluster_f10_d23_HomogRadCTRL',
            'cluster_f10_d24_HomogRadCTRL',
            'cluster_f10_d25_HomogRadCTRL',

            # 16
            'cluster_f10_d26_HomogRadCTRL',
            'cluster_f10_d27_HomogRadCTRL',
            'cluster_f10_d28_HomogRadCTRL',
            'cluster_f10_d29_HomogRadCTRL',
            'cluster_f10_d30_HomogRadCTRL',
           ]
totalT   = [ 217 ] * len(expList)
expdict  = {
            'RRCE_3km_f00':'CTRL',    \
            'RRCE_3km_f10':'D00_on',    \
            'RRCE_3km_f00_halfwind_30':'D30half_on',\

            'cluster_f10_d10_HomogRadCTRL':'D10_f10_HRadCTL',
            'cluster_f10_d11_HomogRadCTRL':'D11_f10_HRadCTL',
            'cluster_f10_d12_HomogRadCTRL':'D12_f10_HRadCTL',
            'cluster_f10_d13_HomogRadCTRL':'D13_f10_HRadCTL',
            'cluster_f10_d14_HomogRadCTRL':'D14_f10_HRadCTL',

            'cluster_f10_d15_HomogRadCTRL':'D15_f10_HRadCTL',
            'cluster_f10_d16_HomogRadCTRL':'D16_f10_HRadCTL',
            'cluster_f10_d17_HomogRadCTRL':'D17_f10_HRadCTL',
            'cluster_f10_d18_HomogRadCTRL':'D18_f10_HRadCTL',
            'cluster_f10_d19_HomogRadCTRL':'D19_f10_HRadCTL',

            'cluster_f10_d20_HomogRadCTRL':'D20_f10_HRadCTL',
            'cluster_f10_d21_HomogRadCTRL':'D21_f10_HRadCTL',
            'cluster_f10_d22_HomogRadCTRL':'D22_f10_HRadCTL',
            'cluster_f10_d23_HomogRadCTRL':'D23_f10_HRadCTL',
            'cluster_f10_d24_HomogRadCTRL':'D24_f10_HRadCTL',

            'cluster_f10_d25_HomogRadCTRL':'D25_f10_HRadCTL',
            'cluster_f10_d26_HomogRadCTRL':'D26_f10_HRadCTL',
            'cluster_f10_d27_HomogRadCTRL':'D27_f10_HRadCTL',
            'cluster_f10_d28_HomogRadCTRL':'D28_f10_HRadCTL',
            'cluster_f10_d29_HomogRadCTRL':'D29_f10_HRadCTL',

            'cluster_f10_d30_HomogRadCTRL':'D30_f10_HRadCTL',

           }

def getExpDeltaT(exp):
  expheader=exp.split('_')[0]
  if expheader == 'RCE':
    return 60 #mins
  elif expheader == 'RRCE':
    return 20 #mins
  elif expheader == 'cluster':
    return 20 #mins
