#!/usr/bin/bash
#SBATCH -J draw     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 10     # Run a single task
#SBATCH -w mogamd
#SBATCH -o acom.%j.out  # output file

source ~/.bashrc
conda activate py311

#for i in 0 1 2 3 4; do
for i in 4;do
python -u combine03.py ${i} 
python -u combine_zeta.py ${i} 
#python -u combine.py ${i} &
done
wait
