#!/usr/bin/bash
#SBATCH -J series     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 30       # Run a single task
#SBATCH -w node01  # nodelist
#SBATCH -o series.%j.out  # output file


source ~/.bashrc
conda activate py311

#for i in $(seq 0 5);do
for i in 0 1 2 3 4;do
for c in 100km 50km 25km;do
mpirun -np 10 python -u series_conv.py ${i} ${c} &
done

wait
done

wait
