#!/usr/bin/bash
#SBATCH -J con     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 2       # Run a single task
#SBATCH -w node01  # nodelist
##SBATCH -w mogamd  # nodelist
#SBATCH -o out.%j.out  # output file

source ~/.bashrc
conda activate py311

## for i in $(seq 0 4);do
## echo ${i}
## mpirun -np 25 python -u mspace.py ${i}
## done

mpirun -np 2 python -u mspace.py 1 


