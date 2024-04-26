DSET ^./RRCE_3km_f05/axisym-%tm6.nc
 DTYPE netcdf
 OPTIONS template
 TITLE C.Surface variables
 UNDEF 99999.
 CACHESIZE 10000000
 XDEF 160 LINEAR 0.025 0.05
 YDEF 1 LINEAR 0. .027027
 ZDEF 75 LEVELS 0 .037 .112 .194 .288 .395 .520 .667 .843 1.062 1.331 1.664 2.055 2.505 3.000 3.500 4.000 4.500 5.000 5.500 6.000 6.500 7.000 7.500 8.000 8.500 9.000 9.500 10.000 10.500 11.000 11.500 12.000 12.500 13.000 13.500 14.000 14.500 15.000 15.500 16.000 16.500 17.000 17.500 18.000 18.500 19.000 19.500 20.000 20.500 21.000 21.500 22.000 22.500 23.000 23.500 24.000 24.500 25.000 25.500 26.000 26.500 27.000 27.500 28.000 28.500 29.000 29.500 30.000 30.500 31.000 31.500 32.000 32.500 33.000
 TDEF 2765 LINEAR 01JAN1998 20mn
 VARS 18
  u_radi=>radi 75 t,z,x "m s-1" 
  u_tang=>tang 75 t,z,x "m s-1" 
  w=>w         75 t,z,x "m s-1" 
  zeta=>zeta   75 t,z,x "s-1" 
  qv=>qv       75 t,z,x "kg kg-1" 
  qc=>qc       75 t,z,x "kg kg-1" 
  qi=>qi       75 t,z,x "kg kg-1" 
  qr=>qr       75 t,z,x "kg kg-1" 
  th=>th       75 t,z,x "K" 
  temp=>temp   75 t,z,x "K" 
  tv=>tv       75 t,z,x "K" 
  dtradsw=>dtradsw 75 t,z,x "K s-1" 
  dtradlw=>dtradlw 75 t,z,x "K s-1" 
  rain=>rain  1 t,x "mm hr-1" 
  cwv=>cwv    1 t,x "kg/m2" 
  lwp=>lwp    1 t,x "kg/m2" 
  iwp=>iwp    1 t,x "kg/m2" 
  sample=>sample 1 t,x "count" 
 ENDVARS
