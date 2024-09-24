#!/usr/bin/bash
#SBATCH -J axisy     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 12       # Run a single task
#SBATCH -w node01  # nodelist
#SBATCH -o out2.%j.out  # output file
#SBATCH --dependency=afterok:5464

source ~/.bashrc
conda activate py311

py='cal_axisymmetricity.py'

for i in $(seq 18 -1 1);do
  echo ${i}
  mpirun -np 12 python -u ${py} ${i}
done
mpirun -np 12 python -u ${py} 0
