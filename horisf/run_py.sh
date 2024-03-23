#!/usr/bin/bash
#SBATCH -J sfpy     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 40       # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o sfpy.%j.out  # output file

source ~/.bashrc
conda activate py311

#for i in $(seq 5 -1 0);do
for i in 7 8 9; do
  mpirun -np 5 python -u cal_sf_fft.py ${i}
done
