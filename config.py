
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
            'RRCE_3km_f00_26', \
            'RRCE_3km_f00_27', \
            'RRCE_3km_f00_28', \
            'RRCE_3km_f00_29', \
            'RRCE_3km_f00_30', \
            'RRCE_3km_f00_30p27', \
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
            217,  \
            217,  \
            217,  \
            217,  \
            1441, \
            217,  \
           ]
expdict  = {
            'RRCE_3km_f00':'D00_close',    \
            'RRCE_3km_f10':'D00_open',    \
            'RRCE_3km_f00_10':'D10_open', \
            'RRCE_3km_f00_15':'D15_open', \
            'RRCE_3km_f00_16':'D16_open', \
            'RRCE_3km_f00_17':'D17_open', \
            'RRCE_3km_f00_18':'D18_open', \
            'RRCE_3km_f00_19':'D19_open', \
            'RRCE_3km_f00_20':'D20_open', \
            'RRCE_3km_f00_21':'D21_open', \
            'RRCE_3km_f00_22':'D22_open', \
            'RRCE_3km_f00_23':'D23_open', \
            'RRCE_3km_f00_24':'D24_open', \
            'RRCE_3km_f00_25':'D25_open', \
            'RRCE_3km_f00_26':'D26_open', \
            'RRCE_3km_f00_27':'D27_open', \
            'RRCE_3km_f00_28':'D28_open', \
            'RRCE_3km_f00_29':'D29_open', \
            'RRCE_3km_f00_30':'D30_open', \
            'RRCE_3km_f00_30p27':'D30p27_open', \
           }

def getExpDeltaT(exp):
  expheader=exp.split('_')[0]
  if expheader == 'RCE':
    return 60 #mins
  elif expheader == 'RRCE':
    return 20 #mins
