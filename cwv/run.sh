#!/usr/bin/bash
#SBATCH -J cwv     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 5       # Run a single task
#SBATCH -w node01  # nodelist
#SBATCH -o cwv.%j.out  # output file


source ~/.bashrc
conda activate py311

python -u cwv.py 0 &
python -u cwv.py 1 &
python -u cwv.py 2 &
python -u cwv.py 3 &
python -u cwv.py 4 &
wait

