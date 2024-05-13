
vvmPath  = '/data/C.shaoyu/rrce/vvm/'
dataPath = '/data/C.shaoyu/rrce/data/'

expList  = [
            'RRCE_3km_f00',    \
            'RRCE_3km_f10',    \
            'RRCE_3km_f00_10', \
            'RRCE_3km_f00_15', \
            'RRCE_3km_f00_16', \
            'RRCE_3km_f00_17', \
            'RRCE_3km_f00_18', \
            'RRCE_3km_f00_19', \
            'RRCE_3km_f00_20', \
            'RRCE_3km_f00_21', \
            'RRCE_3km_f00_22', \
            'RRCE_3km_f00_23', \
            'RRCE_3km_f00_24', \
            'RRCE_3km_f00_25', \
            'RRCE_3km_f00_30', \
           ]
totalT   = [
            2881, \
            2161, \
            1441, \
            1081, \
            217,  \
            217,  \
            217,  \
            325,  \
            2880, \
            361,  \
            361,  \
            361,  \
            361,  \
            1441, \
            1441, \
           ]

def getExpDeltaT(exp):
  expheader=exp.split('_')[0]
  if expheader == 'RCE':
    return 60 #mins
  elif expheader == 'RRCE':
    return 20 #mins
