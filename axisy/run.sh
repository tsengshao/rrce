#!/usr/bin/bash
#SBATCH -J axis     # Job name
#SBATCH -p cf448     # job partition
#SBATCH -A MST114418
#SBATCH -c 1              # cores per MPI rank
#SBATCH -n 224    # Run a single task
#SBATCH -o out.%j.out  # output file

source ~/.bashrc
conda activate py311

py='cal_axisy.py'

#for i in $(seq 18 -1 1);do
for i in $(seq 0 5);do
  echo ${i}
  mpirun -np 217 python -u ${py} ${i}
done
# mpirun -np 73 python -u ${py} 0
# mpirun -np 73 python -u ${py} 20
