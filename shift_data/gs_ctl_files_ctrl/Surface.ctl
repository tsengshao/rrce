DSET ^../archive/RRCE_3km_f00.C.Surface-%tm6.nc
 DTYPE netcdf
 OPTIONS template
 TITLE C.Surface variables
 UNDEF 99999.
 CACHESIZE 10000000
 XDEF 384 LINEAR 0 .027027
 YDEF 384 LINEAR 0 .027027
 ZDEF 1 LEVELS 1000
 TDEF 3654 LINEAR 01JAN1998 20mn
 VARS 7 
uw=>uw 0 t,y,x sfc_flux_u_momentum
wv=>wv 0 t,y,x sfc_flux_v_momentum
wth=>wth 0 t,y,x sfc_flux_theta
wqv=>wqv 0 t,y,x sfc_flux_water_vapor
sprec=>sprec 0 t,y,x sfc_precip_rate
tg=>tg 0 t,y,x Skin_temp
olr=>olr 0 t,y,x outgoing_longwave_radiation
 ENDVARS
