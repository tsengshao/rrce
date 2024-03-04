
vvmPath  = '/data/C.shaoyu/rrce/vvm/'
dataPath = '/data/C.shaoyu/rrce/data/'

expList  = ['RCE_300K_3km_f0', 'RCE_300K_3km_f05', 'RRCE_3km_f00', 'RRCE_3km_f10', 'RRCE_3km_f15', 'RRCE_3km_f20']
totalT   = [2137, 2030, 3654, 2286, 2161, 2138]

def getExpDeltaT(exp):
  expheader=exp.split('_')[0]
  if expheader == 'RRCE':
    return 60 #mins
  elif expheader == 'RCE':
    return 20 #mins
