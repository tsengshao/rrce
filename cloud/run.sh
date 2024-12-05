#!/usr/bin/bash
#SBATCH -J axis2     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 15       # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o out.%j.out  # output file

source ~/.bashrc
conda activate py311

py='find_cloud.py'

# for i in $(seq 18 -1 1);do
#   echo ${i}
#   #python -u ${py} ${i} &
#   mpiexec -n 6 python -u ${py} ${i}
# done
# 
# wait
mpirun -np 1 python -u ${py} 0
