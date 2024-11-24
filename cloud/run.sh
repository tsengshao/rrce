#!/usr/bin/bash
#SBATCH -J axis     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 65       # Run a single task
#SBATCH -w node01  # nodelist
#SBATCH -o out.%j.out  # output file

source ~/.bashrc
conda activate py311

py='find_cloud.py'

#for i in $(seq 18 -1 1);do
#for i in 2 8 13 18; do
for i in 2 8 13; do
  echo ${i}
  python -u ${py} ${i} &
  #mpirun -np 73 python -u ${py} ${i}
done

wait
#mpirun -np 73 python -u ${py} 0
