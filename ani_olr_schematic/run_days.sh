#!/usr/bin/bash
#SBATCH -J draw     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 4      # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o draw.%j.out  # output file

source ~/.bashrc
mode="SAVEFIG"
gs="draw_olr_prec.gs"

for iexp in $(seq 2 19);do
  echo ${iexp}
  #ts=145
  #te=217
  ts=217
  te=217
  grads -blcx "run ${gs} ${iexp} -mode ${mode} -ts ${ts} -te ${te}"
done

for iexp in 1;do
  echo ${iexp}
  #ts=145
  #te=217
  ts=1
  grads -blcx "run ${gs} ${iexp} -mode ${mode} -ts ${ts}"
done
