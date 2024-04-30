#!/bin/bash
#SBATCH --job-name=0529          # Specify job name
#SBATCH --partition=shared     # Specify partition name
#SBATCH --ntasks=1             # Specify max. number of tasks to be invoked
#SBATCH --cpus-per-task=3      # Specify number of CPUs per task
#SBATCH --time=08:00:00        # Set a limit on the total run time
#SBATCH --account=bm0982       # Charge resources on this project account
#SBATCH --output=track0529.o%j    # File name for standard output
#SBATCH --error=track0529.o%j     # File name for standard error output

set -ex


DATENPFAD=${PWD}/../tracking_data
#DATENFILE=data.nc

PFAD=`pwd`

cd $PFAD
cp irt_parameters.f90 $DATENPFAD/
./compile.sh

cd $DATENPFAD

  ### Iterate Object Files ###
   ${PFAD}/irt_objects_release.x 1

   #${PFAD}/irt_advection_field_release.x
   #cp irt_advection_field.srv irt_advection_field_it1.srv
   ##  for ITERATION in 2; do
   ##       echo iteration $ITERATION
   ##       ${PFAD}/irt_objects_release.x 2
   ##       ${PFAD}/irt_advection_field_release.x
   ##       cp irt_advection_field.srv irt_advection_field_it${ITERATION}.srv
   ##  done
   #rm -rf irt_advection_field.srv
   #cp irt_objects_output.txt irt_objects_output_it3.txt

   ### Build Tracks ###
   ${PFAD}/irt_tracks_release.x

   ### Generate Field of Track IDs ###
   sort -n -k2 irt_tracks_nohead_output.txt > irt_tracks_sorted.txt
   ${PFAD}/irt_trackmask_release.x

   ### add links to preceding and successing tracks to track headers
   ${PFAD}/irt_tracklinks_release.x

exit

