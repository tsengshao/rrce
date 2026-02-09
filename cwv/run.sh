#!/usr/bin/bash
#SBATCH -J wp     # Job name
##SBATCH -p all     # job partition
#SBATCH -p compute    # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 15       # Run a single task
##SBATCH -w mogamd  # nodelist
#SBATCH -o wp.%j.out  # output file


source ~/.bashrc
conda activate py311
echo $(which mpirun)
echo $(which python)

#for i in $(seq 0 4);do
for i in $(seq 37 40);do
  mpirun -np 15 python -u wp.py ${i}
done

wait

#  python -u lwp.py 0 &
#  python -u lwp.py 1 &
#  python -u lwp.py 2 &
#  python -u lwp.py 3 &
#  python -u lwp.py 4 &
#  wait

