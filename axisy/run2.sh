#!/usr/bin/bash
#SBATCH -J axisy     # Job name
#SBATCH -p compute     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 10       # Run a single task
##SBATCH -w node01  # nodelist
##SBATCH -w mogamd  # nodelist
#SBATCH -o out2.%j.out  # output file
#SBATCH --dependency=afterok:42

source ~/.bashrc
conda activate py311

py='cal_axisymmetricity.py'
#py='cal_axisymmetricity_ano.py'
#py='cal_process_axisymmetricity.py'

#for i in $(seq 19 -1 1);do
for i in $(seq 36 -1 19);do
  echo ${i}
  mpirun -np 10 python -u ${py} ${i}
done
# mpirun -np 20 python -u ${py} 0
#mpirun -np 20 python -u ${py} 20
