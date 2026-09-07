
vvmPath  = '/work1/umbrella0c/VVM/DATA/'
dataPath = '/work1/umbrella0c/rrce2/data/'

expList  = [  
            # 0
            'cluster_f20_d10',
            'cluster_f20_d16',
            'cluster_f20_d17',
            'cluster_f20_d18',
            'cluster_f20_d19',

            # 5
            'cluster_f10_d20',
            'cluster_f10_d25',
            'cluster_f10_d30',
            'cluster_f20_d15',
            'cluster_f20_d20',
            'cluster_f20_d21',
            'cluster_f20_d22',
            'cluster_f20_d23',
            'cluster_f20_d24',
            'cluster_f20_d25',
            'cluster_f20_d26',
            'cluster_f20_d27',
            'cluster_f20_d28',
            'cluster_f20_d29',
            'cluster_f20_d30',
           ]
totalT   = [ 217 ] * len(expList)
expdict  = {
            'RRCE_3km_f00':'CTRL',    \
            'RRCE_3km_f10':'D00_on',    \
            'RRCE_3km_f00_10':'D10_on', \
            'RRCE_3km_f00_15':'D15_on', \
            'RRCE_3km_f00_16':'D16_on', \
            'RRCE_3km_f00_17':'D17_on', \
            'RRCE_3km_f00_18':'D18_on', \
            'RRCE_3km_f00_19':'D19_on', \
            'RRCE_3km_f00_20':'D20_on', \
            'RRCE_3km_f00_21':'D21_on', \
            'RRCE_3km_f00_22':'D22_on', \
            'RRCE_3km_f00_23':'D23_on', \
            'RRCE_3km_f00_24':'D24_on', \
            'RRCE_3km_f00_25':'D25_on', \
            'RRCE_3km_f00_26':'D26_on', \
            'RRCE_3km_f00_27':'D27_on', \
            'RRCE_3km_f00_28':'D28_on', \
            'RRCE_3km_f00_29':'D29_on', \
            'RRCE_3km_f00_30':'D30_on', \
            'RRCE_3km_f00_30p27':'D30p27_on', \

            'RRCE_3km_f00_14p972':'D14p972_on',\
            'RRCE_3km_f00_14p986':'D14p986_on',\
            'RRCE_3km_f00_15p014':'D15p014_on',\
            'RRCE_3km_f00_15p028':'D15p028_on',\
            'RRCE_3km_f00_19p972':'D19p972_on',\
            'RRCE_3km_f00_19p986':'D19p986_on',\
            'RRCE_3km_f00_20p014':'D20p014_on',\
            'RRCE_3km_f00_20p028':'D20p028_on',\
            'RRCE_3km_f00_24p972':'D24p972_on',\
            'RRCE_3km_f00_24p986':'D24p986_on',\
            'RRCE_3km_f00_25p014':'D25p014_on',\
            'RRCE_3km_f00_25p028':'D25p028_on',\
            'RRCE_3km_f00_29p972':'D29p972_on',\
            'RRCE_3km_f00_29p986':'D29p986_on',\
            'RRCE_3km_f00_30p014':'D30p014_on',\
            'RRCE_3km_f00_30p028':'D30p028_on',\

            'RRCE_3km_f00_halfwind_30':'D30half_on',\

            'RRCE_3km_f00_11':'D11_on', 
            'RRCE_3km_f00_12':'D12_on', 
            'RRCE_3km_f00_13':'D13_on', 
            'RRCE_3km_f00_14':'D14_on', 

            'RRCE_3km_f00_25p07':'D25p07_on', 

            'cluster_f10_d20':'D10_f10',
            'cluster_f10_d25':'D10_f10',
            'cluster_f10_d30':'D10_f10',
            'cluster_f20_d15':'D15_f20',
            'cluster_f20_d20':'D20_f20',
            'cluster_f20_d21':'D21_f20',
            'cluster_f20_d22':'D22_f20',
            'cluster_f20_d23':'D23_f20',
            'cluster_f20_d24':'D24_f20',
            'cluster_f20_d25':'D25_f20',
            'cluster_f20_d26':'D26_f20',
            'cluster_f20_d27':'D27_f20',
            'cluster_f20_d28':'D28_f20',
            'cluster_f20_d29':'D29_f20',
            'cluster_f20_d30':'D30_f20',

            'cluster_f20_d10':'D10_f20',
            'cluster_f20_d15':'D15_f20',
            'cluster_f20_d16':'D16_f20',
            'cluster_f20_d17':'D17_f20',
            'cluster_f20_d18':'D18_f20',
            'cluster_f20_d19':'D19_f20',
           }

def getExpDeltaT(exp):
  expheader=exp.split('_')[0]
  if expheader == 'RCE':
    return 60 #mins
  elif expheader == 'RRCE':
    return 20 #mins
  elif expheader == 'cluster':
    return 20 #mins
