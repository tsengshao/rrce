#!/usr/bin/bash
#SBATCH -J axis     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 120       # Run a single task
#SBATCH -w node01  # nodelist
#SBATCH -o out.%j.out  # output file

source ~/.bashrc
conda activate py311

py='cal_axisy.py'

for i in $(seq 0 1 3);do
  echo ${i}
  mpirun -np 120 python -u ${py} ${i}
done
