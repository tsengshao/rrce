#!/usr/bin/bash
#SBATCH -J center     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 19       # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o center.%j.out  # output file


source ~/.bashrc
conda activate py311
ncpu=19
cpum=$(echo "${ncpu}-1"|bc)

for i in $(seq 0 18);do
  a=$(echo "mod(${i},${ncpu})"|bc -l ~/.bcrc)
  echo ${i}...${a}
  mpirun -np 1 python -u find_center.py ${i} &
  if [ "${a}" == "${cpum}" ]; then
    wait
  fi
done

wait

