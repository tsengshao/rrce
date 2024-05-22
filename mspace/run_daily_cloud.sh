#!/usr/bin/bash
#SBATCH -J mspace_dcloud     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 1      # Run a single task
##SBATCH -w mogamd  # nodelist
#SBATCH -w node01
#SBATCH -o dcloud.%j.out  # output file

source ~/.bashrc
conda activate py311

# for i in $(seq 0 4);do
#   echo ${i}
#   mpirun -np 5 python -u mspace_daily_ptile.py ${i}
# done
#python -u mspace_cloud_daily_ptile.py 7
python -u mspace_cloud_penta_ptile.py 0

wait


