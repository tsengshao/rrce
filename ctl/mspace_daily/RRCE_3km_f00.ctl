DSET ^./RRCE_3km_f00/mspace-%tm3days.nc
 DTYPE netcdf
 OPTIONS template
 TITLE C.Surface variables
 CACHESIZE 60000
 UNDEF -999.
 XDEF 100 LINEAR 0.5 1
 YDEF 1   LINEAR 0. .027027
 ZDEF 75 LEVELS 0 .037 .112 .194 .288 .395 .520 .667 .843 1.062 1.331 1.664 2.055 2.505 3.000 3.500 4.000 4.500 5.000 5.500 6.000 6.500 7.000 7.500 8.000 8.500 9.000 9.500 10.000 10.500 11.000 11.500 12.000 12.500 13.000 13.500 14.000 14.500 15.000 15.500 16.000 16.500 17.000 17.500 18.000 18.500 19.000 19.500 20.000 20.500 21.000 21.500 22.000 22.500 23.000 23.500 24.000 24.500 25.000 25.500 26.000 26.500 27.000 27.500 28.000 28.500 29.000 29.500 30.000 30.500 31.000 31.500 32.000 32.500 33.000
 TDEF 2881 LINEAR 01JAN1998 20mn
 VARS 13
 w=>w 75 t,z,x w
 massflux=>mf 75 t,z,x mf
 mse=>mse 75 t,z,x mse
 th=>th 75 t,z,x th
 qv=>qv 75 t,z,x qv
 qc=>qc 75 t,z,x qc
 qi=>qi 75 t,z,x qi
 qr=>qr 75 t,z,x qr
 u=>u   75 t,z,x u
 v=>v   75 t,z,x v
 ws=>ws   75 t,z,x ws
 rain=>rain 0 t,x rain
 nsample=>nsample 0 x rain
 ENDVARS
