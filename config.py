
vvmPath  = '/data/C.shaoyu/rrce/vvm/'
dataPath = '/data/C.shaoyu/rrce/data/'

expList  = ['RRCE_3km_f00', 'RRCE_3km_f10', 'RRCE_3km_f15', 'RCE_300K_3km_f0', 'RCE_300K_3km_f05']
totalT   = [3654, 2286, 2161, 2137, 2030]

def getExpDeltaT(exp):
  expheader=exp.split('_')[0]
  if expheader == 'RRCE':
    return 60 #mins
  elif expheader == 'RCE':
    return 10 #mins
