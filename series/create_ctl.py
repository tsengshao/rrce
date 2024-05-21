import sys, os
sys.path.insert(1,'../')
import config

def write_txt(fname, txt):
  f = open(fname,'w')
  f.write(txt)
  f.close()
  return
def create_msf_ctl(fname, exp, nt, sdate):
  txt = f"""
DSET ^./{exp}/series_hsf_%tm6.nc
 OPTIONS template
 DTYPE netcdf
 TITLE C.Surface variables
 UNDEF 99999.
 CACHESIZE 10000000
 XDEF 1 LINEAR 0. .027027
 YDEF 1 LINEAR 0. .027027
 ZDEF 1 LEVELS 1000
 ZDEF 38 LEVELS
    0 73.5 152 240 340.5 456.5 592.5 754 951.5 1195.5 1496.5
    1858.5 2279 2751.5 3250 3750 4250 4750 5250 5750 6250 6750
    7250 7750 8250 8750 9250 9750 10250 10750 11250 11750 12250
    12750 13250 13750 14250 14750 ;
 TDEF {nt} LINEAR {sdate+1:02d}JAN1998 20mn
 VARS 1
 maxsf=>maxsf 38 t,z max_sf
 ENDVARS
"""
  write_txt(fname, txt)
  return

def create_conv_ctl(fname, exp, nt, sdate):
  txt = f"""
DSET ^./{exp}/%e/series_conv_%tm6.nc
 OPTIONS template
 DTYPE netcdf
 TITLE C.Surface variables
 UNDEF 99999.
 CACHESIZE 10000000
 XDEF 1 LINEAR 0. .027027
 YDEF 1 LINEAR 0. .027027
 ZDEF 1 LEVELS 1000
 TDEF {nt} LINEAR {sdate+1:02d}JAN1998 20mn
 EDEF 3 names 100km 50km 25km
 VARS 3
 max_zeta=>mzeta   0 t max_zeta
 area_zeta1=>aseed 0 t area of seed
 area_zeta2=>atc   0 t area of tc
 ENDVARS
"""
  write_txt(fname, txt)
  return

def create_series_ctl(fname,exp,nt,sdate):
  txt =  f"""
DSET ^./{exp}/series_%tm6.nc
 OPTIONS template
 DTYPE netcdf
 TITLE C.Surface variables
 UNDEF 99999.
 CACHESIZE 10000000
 XDEF 1 LINEAR 0. .027027
 YDEF 1 LINEAR 0. .027027
 ZDEF 1 LEVELS 1000
 TDEF {nt} LINEAR {sdate+1:02d}JAN1998 20mn
 VARS 8
 cwv_mean=>cwvm 0 t xxx
 lwp_mean=>lwpm 0 t xxx
 iwp_mean=>iwpm 0 t xxx
 cwv_std=>cwvs  0 t xxx
 lwp_std=>lwps  0 t xxx
 iwp_std=>iwps  0 t xxx
 maxwind=>mws   0 t xxx
 dryfrac=>dryf  0 t xxx
 ENDVARS
"""
  write_txt(fname, txt)
  return

if __name__=='__main__':
  outdir=config.dataPath+f"/series/"
  nexp = len(config.expList)
  for i in range(nexp):
    exp = config.expList[i]
    dum = exp.split('_')
    sdate = int(dum[-1]) if len(dum)==4 else 0
    if exp == 'RRCE_3km_f00':
      nt = int(35*72+1)
    elif exp == 'RRCE_3km_f10':
      nt = int(30*72+1)
    else:
      nt = 271
    create_series_ctl(outdir+f'series_{exp}.ctl',\
                      exp, nt, sdate)
    create_conv_ctl(outdir+f'conv_{exp}.ctl',\
                      exp, nt, sdate)
    create_msf_ctl(outdir+f'msf_{exp}.ctl',\
                      exp, nt, sdate)

