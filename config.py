
vvmPath  = '/data/C.shaoyu/rrce/vvm/'
dataPath = '/data/C.shaoyu/rrce/data/'

expList  = [  
            # 0
            'RRCE_3km_f00',    
            'RRCE_3km_f10',    
            'RRCE_3km_f00_10', 
            'RRCE_3km_f00_15', 
            'RRCE_3km_f00_16', 
            # 5
            'RRCE_3km_f00_17',
            'RRCE_3km_f00_18',
            'RRCE_3km_f00_19',
            'RRCE_3km_f00_20',
            'RRCE_3km_f00_21',
            # 10
            'RRCE_3km_f00_22',
            'RRCE_3km_f00_23',
            'RRCE_3km_f00_24',
            'RRCE_3km_f00_25',
            'RRCE_3km_f00_26',
            #15
            'RRCE_3km_f00_27', 
            'RRCE_3km_f00_28', 
            'RRCE_3km_f00_29',
            'RRCE_3km_f00_30',
            'RRCE_3km_f00_30p27',
            #20
            'RRCE_3km_f00_14p972',
            'RRCE_3km_f00_14p986',
            'RRCE_3km_f00_15p014',
            'RRCE_3km_f00_15p028',
            'RRCE_3km_f00_19p972',
            #25
            'RRCE_3km_f00_19p986',
            'RRCE_3km_f00_20p014',
            'RRCE_3km_f00_20p028',
            'RRCE_3km_f00_24p972',
            'RRCE_3km_f00_24p986',
            #30
            'RRCE_3km_f00_25p014',
            'RRCE_3km_f00_25p028',
            'RRCE_3km_f00_29p972',
            'RRCE_3km_f00_29p986',
            'RRCE_3km_f00_30p014',
            #35
            'RRCE_3km_f00_30p028',
            'RRCE_3km_f00_halfwind_30',
#            'RRCE_3km_f00_25p07', 
           ]
totalT   = [
            # 0
            2881,
            2161,
            1441,
            1081,
            217, 
            # 5
            217, 
            217, 
            325, 
            2880,
            361, 
            # 10
            361, 
            361, 
            361, 
            1441,
            217, 
            # 15
            217, 
            217, 
            217, 
            1441,
            217, 

            # 20
            217,
            217,
            217,
            217,
            217,
            # 25
            217,
            217,
            217,
            217,
            217,
            # 30
            217,
            217,
            217,
            217,
            217,

            # 35
            217,  \
            217,  \
#            217,  \

           ]
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
            'RRCE_3km_f00_25p07':'D25p07_on', \
           }

def getExpDeltaT(exp):
  expheader=exp.split('_')[0]
  if expheader == 'RCE':
    return 60 #mins
  elif expheader == 'RRCE':
    return 20 #mins
