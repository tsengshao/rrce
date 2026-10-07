
vvmPath  = '/work1/umbrella0c/VVM/DATA/'
dataPath = '/work1/umbrella0c/rrce2/data/'

expList  = [  
            # 0
            'cluster_f10_d10_FixRad',

            # 1
            'cluster_f10_d11_FixRad',
            'cluster_f10_d12_FixRad',
            'cluster_f10_d13_FixRad',
            'cluster_f10_d14_FixRad',
            'cluster_f10_d15_FixRad',

            # 6
            'cluster_f10_d16_FixRad',
            'cluster_f10_d17_FixRad',
            'cluster_f10_d18_FixRad',
            'cluster_f10_d19_FixRad',
            'cluster_f10_d20_FixRad',

            # 11
            'cluster_f10_d21_FixRad',
            'cluster_f10_d22_FixRad',
            'cluster_f10_d23_FixRad',
            'cluster_f10_d24_FixRad',
            'cluster_f10_d25_FixRad',

            # 16
            'cluster_f10_d26_FixRad',
            'cluster_f10_d27_FixRad',
            'cluster_f10_d28_FixRad',
            'cluster_f10_d29_FixRad',
            'cluster_f10_d30_FixRad',
           ]
totalT   = [ 217 ] * len(expList)
expdict  = {
            'RRCE_3km_f00':'CTRL',    \
            'RRCE_3km_f10':'D00_on',    \
            'RRCE_3km_f00_halfwind_30':'D30half_on',\

            'cluster_f10_d10_FixRad':'D10_f10_FixRad',
            'cluster_f10_d11_FixRad':'D11_f10_FixRad',
            'cluster_f10_d12_FixRad':'D12_f10_FixRad',
            'cluster_f10_d13_FixRad':'D13_f10_FixRad',
            'cluster_f10_d14_FixRad':'D14_f10_FixRad',

            'cluster_f10_d15_FixRad':'D15_f10_FixRad',
            'cluster_f10_d16_FixRad':'D16_f10_FixRad',
            'cluster_f10_d17_FixRad':'D17_f10_FixRad',
            'cluster_f10_d18_FixRad':'D18_f10_FixRad',
            'cluster_f10_d19_FixRad':'D19_f10_FixRad',

            'cluster_f10_d20_FixRad':'D20_f10_FixRad',
            'cluster_f10_d21_FixRad':'D21_f10_FixRad',
            'cluster_f10_d22_FixRad':'D22_f10_FixRad',
            'cluster_f10_d23_FixRad':'D23_f10_FixRad',
            'cluster_f10_d24_FixRad':'D24_f10_FixRad',

            'cluster_f10_d25_FixRad':'D25_f10_FixRad',
            'cluster_f10_d26_FixRad':'D26_f10_FixRad',
            'cluster_f10_d27_FixRad':'D27_f10_FixRad',
            'cluster_f10_d28_FixRad':'D28_f10_FixRad',
            'cluster_f10_d29_FixRad':'D29_f10_FixRad',

            'cluster_f10_d30_FixRad':'D30_f10_FixRad',

           }

def getExpDeltaT(exp):
  expheader=exp.split('_')[0]
  if expheader == 'RCE':
    return 60 #mins
  elif expheader == 'RRCE':
    return 20 #mins
  elif expheader == 'cluster':
    return 20 #mins
