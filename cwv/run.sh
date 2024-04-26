#!/usr/bin/bash
#SBATCH -J wp     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 10       # Run a single task
#SBATCH -w node01  # nodelist
##SBATCH -w mogamd  # nodelist
#SBATCH -o wp.%j.out  # output file


source ~/.bashrc
conda activate py311

#for i in $(seq 0 4);do
for i in 1 ;do
  mpirun -np 10 python -u wp.py ${i}
done

#  python -u lwp.py 0 &
#  python -u lwp.py 1 &
#  python -u lwp.py 2 &
#  python -u lwp.py 3 &
#  python -u lwp.py 4 &
#  wait

