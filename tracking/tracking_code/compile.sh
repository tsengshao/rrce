#!/bin/bash
set -ex

# netcdf configure flag
# ifort -o ooo.x ooo.f $(nc-config --fflags --flibs)

COMPILE_COMMAND="ifort -no-wrap-margin -mcmodel=large -check bounds -debug all -traceback -g -shared-intel -free -heap-arrays 10 $(nc-config --fflags --flibs)"
#COMPILE_COMMAND='ifort -no-wrap-margin -mcmodel=large -C -debug all -traceback -shared-intel -free -heap-arrays 10'
#COMPILE_COMMAND='ifort -no-wrap-margin -mcmodel=large -debug all -traceback -shared-intel -free -heap-arrays 10'
#COMPILE_COMMAND='gfortran -g -C -O0 -mcmodel=large'

# clean:
set +e
rm irt_parameters.mod
rm irt_objects_release.x
rm irt_advection_field_release.x
rm irt_tracks_release.x
rm irt_trackmask_release.x
rm irt_tracklinks_release.x
set -ex

# compile:
${COMPILE_COMMAND} -o irt_objects_release.x irt_parameters.f90 irt_tools.f90 irt_objects_release.f90 
${COMPILE_COMMAND} -o irt_advection_field_release.x irt_advection_field_release.f90 irt_parameters.f90
${COMPILE_COMMAND} -o irt_tracks_release.x irt_tracks_release.f90 irt_parameters.f90
${COMPILE_COMMAND} -o irt_trackmask_release.x irt_trackmask_release.f90 irt_parameters.f90
#${COMPILE_COMMAND} -o irt_agemask_release.x irt_agemask_release.f90 irt_parameters.f90
#${COMPILE_COMMAND} -o irt_tracklinks_release.x irt_tracklinks_release.f90 irt_parameters.f90
${COMPILE_COMMAND} -o irt_tracklinks_release.x irt_parameters.f90 irt_tracklinks_release_shao.f90

exit
