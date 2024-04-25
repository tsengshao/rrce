#!/usr/bin/bash
#SBATCH -J con     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 6       # Run a single task
##SBATCH -w node01  # nodelist
#SBATCH -w mogamd  # nodelist
#SBATCH -o out.%j.out  # output file

source ~/.bashrc
conda activate py311

## for i in $(seq 0 4);do
## echo ${i}
## mpirun -np 25 python -u mspace.py ${i}
## done

python -u mspace.py 0 &
python -u mspace.py 1 &
python -u mspace.py 2 &
wait
python -u mspace.py 3 &
python -u mspace.py 4 &
wait


