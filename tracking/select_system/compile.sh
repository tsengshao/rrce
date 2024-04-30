#!/bin/bash

COMPILE_COMMAND='ifort -no-wrap-margin -mcmodel=large -check bounds -debug all -traceback -g -shared-intel -free -heap-arrays 10'

# compile:
${COMPILE_COMMAND} -o select_system.x irt_parameters.f90 select_system.f90
