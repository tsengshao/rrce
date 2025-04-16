#!/usr/bin/bash
#SBATCH -J draw     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 20      # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o draw.%j.out  # output file

source ~/.bashrc
mode="SAVEFIG"
gs="draw_wind.gs"

for iexp in $(seq 2 19);do
  for ts in 1 217;do
    grads -blcx "run ${gs} ${iexp} -mode ${mode} -ts ${ts} -te ${ts}" &
  done
done
wait

for ts in $(seq 1 72 2161);do
#for ts in $(seq 1 3 2521);do
    te=$(echo "{ts}+1"|bc)
    grads -blcx "run ${gs} 1 -mode ${mode} -ts ${ts} -te ${ts}" &
done
wait
