#!/usr/bin/bash
#SBATCH -J center     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 5       # Run a single task
#SBATCH -w node01  # nodelist
#SBATCH -o center.%j.out  # output file


source ~/.bashrc
conda activate py311
py="find_center_czeta_max.py"
ncpu=5
cpum=$(echo "${ncpu}-1"|bc)

for i in $(seq 0 18);do
  a=$(echo "mod(${i},${ncpu})"|bc -l ~/.bcrc)
  echo ${i}...${a}
  mpirun -np 1 python -u ${py} ${i} &
  if [ "${a}" == "${cpum}" ]; then
    wait
  fi
done

wait

