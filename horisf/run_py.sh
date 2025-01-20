#!/usr/bin/bash
#SBATCH -J sfpy     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 30       # Run a single task
##SBATCH -w mogamd  # nodelist
#SBATCH -w node01  # nodelist
#SBATCH -o sfpy.%j.out  # output file

source ~/.bashrc
conda activate py311

# #for i in 7 ;do
# for i in $(seq 18 -1 0);do
#   mpirun -np 30 python -u cal_sf_fft.py ${i}
# done
mpirun -np 30 python -u cal_sf_fft.py 0
