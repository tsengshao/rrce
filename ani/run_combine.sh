#!/usr/bin/bash
#SBATCH -J draw     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 30      # Run a single task
#SBATCH -w node01
#SBATCH -o acom.%j.out  # output file

source ~/.bashrc
conda activate py311

#python -u combine.py 0 &
#python -u combine.py 1 &
python -u combine.py 2 &
python -u combine.py 3 &
python -u combine.py 4 &
wait
