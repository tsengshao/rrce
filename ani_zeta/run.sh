#!/usr/bin/bash
#SBATCH -J draw     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 11      # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o draw.%j.out  # output file

source ~/.bashrc
mode="SAVEFIG"
gs="draw.gs"
#dt=100
dt=36

for iexp in $(seq 1 6);do
  for zidx in 1 2 3; do
    for i in {0..10};do
      ts=$(echo "${i}*${dt}+1"|bc)
      te=$(echo "(${i}+1)*${dt}"|bc)
      echo ${i} ${ts} ${te}
      grads -blcx "run ${gs} ${iexp} -zidx ${zidx} -mode ${mode} -ts ${ts} -te ${te}" &
    done
    wait
  done
done

#bash make.sh
