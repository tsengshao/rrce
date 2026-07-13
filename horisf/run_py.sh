#!/usr/bin/bash
#SBATCH -J sfpy     # Job name
#SBATCH -p ct112     # job partition
#SBATCH -A MST114418
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 72       # Run a single task
#SBATCH -o sfpy.%j.out  # output file

source ~/.bashrc
conda activate py311

for i in 20 ;do
#for i in $(seq 0 14);do
  mpirun -np 72 python -u cal_sf_fft.py ${i}
done
