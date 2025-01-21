
vvmPath  = '/data/C.shaoyu/rankine/vvm/'
dataPath = '/data/C.shaoyu/rankine/data/'

expList  = [
            'rankine_mg_dterm_large', \
            'rankine_mg_dterm_large_slab', \
            'rankine_mg_dterm_large_slab_10m', \
            'rankine_mg_dterm_large_slab_10m_3k', \
           ]
totalT   = [
            721,  \
            721,  \
            721,  \
            295,  \
           ]
expdict  = {
            'rankine_mg_dterm_large':'CTRL', \
            'rankine_mg_dterm_large_slab':'slab', \
            'rankine_mg_dterm_large_slab_10m':'slab_10m', \
            'rankine_mg_dterm_large_slab_10m_3k':'slab_10m_3k', \
           }

def getExpDeltaT(exp):
  return 10  #mins
