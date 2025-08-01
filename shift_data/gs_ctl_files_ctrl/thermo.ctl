!DSET ^../archive/RRCE_3km_f00.L.Thermodynamic-%tm6.nc
DSET /data/der0318/VVM/DATA/RCE_300K_d128r1km_e2/archive/RCE_300K_d128r1km_e2.L.Thermodynamic-%tm6.nc 
 DTYPE netcdf
 OPTIONS template
 TITLE L.Thermodynamic variables
 UNDEF 99999.
 CACHESIZE 10000000
 XDEF 128 LINEAR 0.0000 0.00898315 
 YDEF 128 LINEAR 0.0000 0.00899823 
 ZDEF 75 LEVELS 0 .037 .112 .194 .288 .395 .520 .667 .843 1.062 1.331 1.664 2.055 2.505 3.000 3.500 4.000 4.500 5.000 5.500 6.000 6.500 7.000 7.500 8.000 8.500 9.000 9.500 10.000 10.500 11.000 11.500 12.000 12.500 13.000 13.500 14.000 14.500 15.000 15.500 16.000 16.500 17.000 17.500 18.000 18.500 19.000 19.500 20.000 20.500 21.000 21.500 22.000 22.500 23.000 23.500 24.000 24.500 25.000 25.500 26.000 26.500 27.000 27.500 28.000 28.500 29.000 29.500 30.000 30.500 31.000 31.500 32.000 32.500 33.000
 TDEF 3654 LINEAR 01JAN1998 20mn
 VARS 10 
th=>th 75 t,z,y,x potential_temperature
qv=>qv 75 t,z,y,x vapor_mixing_ratio
qc=>qc 75 t,z,y,x cloud_water_mixing
qr=>qr 75 t,z,y,x rain_mixing_ratio
qi=>qi 75 t,z,y,x cloud_ice_mixing_ratio
nc=>nc 75 t,z,y,x cloud_water_number_mixing_ratio
nr=>nr 75 t,z,y,x rain_number_mixing_ratio
ni=>ni 75 t,z,y,x cloud_ice_number_mixing_ratio
qrim=>qrim 75 t,z,y,x riming_cloud_ice_mixing_ratio
brim=>brim 75 t,z,y,x riming_cloud_ice_volume_mixing_ratio
 ENDVARS
