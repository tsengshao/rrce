#!/usr/bin/bash
#SBATCH -J series     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 20       # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o series.%j.out  # output file


source ~/.bashrc
conda activate py311

#for i in $(seq 0 5);do
for i in 7;do
mpirun -np 20 python -u series_msf.py ${i}
done

wait
