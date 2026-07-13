#!/usr/bin/bash
#SBATCH -J axis2     # Job name
#SBATCH -p ct112     # job partition
#SBATCH -A MST114418
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 112       # Run a single task
#SBATCH -o out.%j.out  # output file

source ~/.bashrc
conda activate py311

py='find_cloud.py'

for i in $(seq 0 14);do
  echo ${i}
  #python -u ${py} ${i} &
  mpirun -np 7 python -u ${py} ${i}
done
# 
# wait
#mpirun -np 1 python -u ${py} 1
