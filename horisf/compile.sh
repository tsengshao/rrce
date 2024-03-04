#!/bin/bash

#mpiifort -free -O3 $(nc-config --fflags --flibs) cal_sf.F -o sf.out



export I_MPI_FABRICS=shm
ulimit -s unlimited

DEBUG="-g -traceback"
FCFLAGS="-O3 -r8 -free -mcmodel=large -heap-arrays 10 -shared-intel ${DEBUG}"
FINCLUDE="-I/opt/libs-intel-oneapi/netcdf-4.7.4/include"
LDLIBS="-L/opt/libs-intel-oneapi/netcdf-4.7.4/lib -lnetcdff -lnetcdf"
mpiifort ${FCFLAGS} ${FINCLUDE} ${LDLIBS} -o sf cal_sf.F
#mpiifort ${FCFLAGS} ${FINCLUDE} ${LDLIBS} test.f90
