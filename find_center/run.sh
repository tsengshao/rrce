#!/usr/bin/bash
#SBATCH -J center     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 6       # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o center.%j.out  # output file


source ~/.bashrc
conda activate py311
#py="find_center_domain_mean.py"
py="find_center_domain_mean_sf.py"
ncpu=5
cpum=$(echo "${ncpu}-1"|bc)
str_kernel='0km'

python -u ${py} 0 ${str_kernel} &
echo $!

exit
for i in $(seq 1 19);do
  pids=()
  a=$(echo "mod(${i},${ncpu})"|bc -l ~/.bcrc)
  echo ${i}...${a}
  #mpirun -np 1 python -u ${py} ${i} ${str_kernel} &
  python -u ${py} ${i} ${str_kernel} &
  pids[${a}]=$!
  
  if [ "${a}" == "${cpum}" ]; then
    for pid in ${pids[*]};do
      wait $pid
    done
    pids=()
  fi
  echo $(jobs -p)
done

echo $(jobs -p)
wait

