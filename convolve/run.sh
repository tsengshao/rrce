#!/usr/bin/bash
#SBATCH -J con     # Job name
#SBATCH -p ct448     # job partition
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 217       # Run a single task
#SBATCH -o out.%j.out  # output file
#SBATCH -A MST114418

source ~/.bashrc
conda activate py311

#for i in $(seq 7 9);do
#for i in 0 1 2 3 4;do
#for i in $(seq 0 14);do
for i in $(seq 1 16);do
#for c in 150 100 50 25;do
for c in 150;do
echo ${i}
mpirun -np 217 python -u cal_convolve.py ${i} ${c}
done
done
