#!/usr/bin/bash
#SBATCH -J series     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 20       # Run a single task
#SBATCH -w node01  # nodelist
#SBATCH -o series.%j.out  # output file


source ~/.bashrc
conda activate py311

#for i in $(seq 0 5);do
#for i in 0 2;do
for i in 14 15 16 17;do
mpirun -np 20 python -u series.py ${i}
done

wait
