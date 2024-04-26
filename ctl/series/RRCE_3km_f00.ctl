DSET ^./RRCE_3km_f00/series_%tm6.nc
 OPTIONS template
 DTYPE netcdf
 TITLE C.Surface variables
 UNDEF 99999.
 CACHESIZE 10000000
 XDEF 1 LINEAR 0. .027027
 YDEF 1 LINEAR 0. .027027
 ZDEF 1 LEVELS 1000
 TDEF 3654 LINEAR 01JAN1998 20mn
 VARS 10
 cwv_mean=>cwvm 0 t xxx 
 lwp_mean=>lwpm 0 t xxx
 iwp_mean=>iwpm 0 t xxx
 cwv_std=>cwvs  0 t xxx
 lwp_std=>lwps  0 t xxx
 iwp_std=>iwps  0 t xxx
 maxwind=>mws   0 t xxx
 dryfrac=>dryf  0 t xxx
 sf000_max=>msf0 0 t xxx
 sf275_max=>msf3 0 t xxx
 ENDVARS
