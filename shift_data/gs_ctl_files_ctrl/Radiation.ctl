DSET ^../archive/RRCE_3km_f00.L.Radiation-%tm6.nc
 DTYPE netcdf
 OPTIONS template
 TITLE L.Radiation variables
 UNDEF 99999.
 CACHESIZE 10000000
 XDEF 384 LINEAR 0 .027027
 YDEF 384 LINEAR 0 .027027
 ZDEF 75 LEVELS 0 .037 .112 .194 .288 .395 .520 .667 .843 1.062 1.331 1.664 2.055 2.505 3.000 3.500 4.000 4.500 5.000 5.500 6.000 6.500 7.000 7.500 8.000 8.500 9.000 9.500 10.000 10.500 11.000 11.500 12.000 12.500 13.000 13.500 14.000 14.500 15.000 15.500 16.000 16.500 17.000 17.500 18.000 18.500 19.000 19.500 20.000 20.500 21.000 21.500 22.000 22.500 23.000 23.500 24.000 24.500 25.000 25.500 26.000 26.500 27.000 27.500 28.000 28.500 29.000 29.500 30.000 30.500 31.000 31.500 32.000 32.500 33.000
 TDEF 3654 LINEAR 01JAN1998 20mn
 VARS 10 
fusw=>fusw 75 t,z,y,x upward_flux_shortwave_radiation
fdsw=>fdsw 75 t,z,y,x downward_flux_shortwave_radiation
fulw=>fulw 75 t,z,y,x upward_flux_longwave_radiation
fdlw=>fdlw 75 t,z,y,x downward_flux_longwave_radiation
dtradsw=>dtradsw 75 t,z,y,x shortwave_heating_rate
dtradlw=>dtradlw 75 t,z,y,x longwave_heating_rate
cldfrc=>cldfrc 75 t,z,y,x cloud_fraction
fuswtoa=>fuswtoa 75 t,y,x upward_flux_shortwave_radiation_toa
fdswtoa=>fdswtoa 75 t,y,x downward_flux_shortwave_radiation_toa
fulwtoa=>fulwtoa 75 t,y,x upward_flux_longwave_radiation_toa
 ENDVARS
