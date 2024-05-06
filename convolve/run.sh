#!/usr/bin/bash
#SBATCH -J con     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 64       # Run a single task
##SBATCH -w node01  # nodelist
#SBATCH -w mogamd  # nodelist
#SBATCH -o out.%j.out  # output file

source ~/.bashrc
conda activate py311

#for i in $(seq 7 9);do
#for i in 0 1 2 3 4;do
for i in 7;do
for c in 100 50 25;do
echo ${i}
mpirun -np 64 python -u cal_convolve.py ${i} ${c}
done
done
