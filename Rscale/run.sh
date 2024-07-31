#!/usr/bin/bash
#SBATCH -J draw     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 20      # Run a single task
#SBATCH -w node01  # nodelist
#SBATCH -o z.%j.out  # output file

source ~/.bashrc
conda activate py311

for iexp in $(seq 0 18);do
  python -u draw.py ${iexp} &
done
wait

#bash make.sh
