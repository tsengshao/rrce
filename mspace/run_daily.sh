#!/usr/bin/bash
#SBATCH -J con     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 1       # Run a single task
#SBATCH -w mogamd  # nodelist
##SBATCH -w node01
#SBATCH -o daily.%j.out  # output file

source ~/.bashrc
conda activate py311

#for i in $(seq 0 4);do
for i in 6;do
  echo ${i}
  python -u mspace_daily_ptile.py ${i} 
done

wait


