#!/usr/bin/bash
#SBATCH -J axis     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 73       # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o out.%j.out  # output file

source ~/.bashrc
conda activate py311

py='cal_axisy.py'

mpiexec -n 73 python -u ${py} 0
exit

for i in $(seq 18 -1 1);do
  echo ${i}
  mpirun -np 73 python -u ${py} ${i}
done
mpirun -np 73 python -u ${py} 0
