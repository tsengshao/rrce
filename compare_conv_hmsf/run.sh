#!/usr/bin/bash
#SBATCH -J draw     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 29      # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o draw.%j.out  # output file

source ~/.bashrc

mode="SAVEFIG"
gs="draw.gs"
dt=100

#for iexp in 3;do
#for iexp in 3 1 4 5 6;do
for iexp in 5;do
  for i in {0..28};do
    ts=$(echo "${i}*${dt}+1"|bc)
    te=$(echo "(${i}+1)*${dt}"|bc)
    echo ${i} ${ts} ${te}
    grads -blcx "run ${gs} ${iexp} -mode ${mode} -ts ${ts} -te ${te}" &
  done
  wait
done

#bash make.sh
