#!/usr/bin/bash
#SBATCH -J drawze    # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 11      # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o drawz.%j.out  # output file

source ~/.bashrc
mode="SAVEFIG"
gs="draw.gs"
dt=22

for iexp in $(seq 1 18);do
  if [ ${iexp} -eq "1" ]; then 
    dt=231
  else
    dt=21
  fi

  for zidx in 6; do
    for i in {0..10};do
    #for i in {0..29};do
      ts=$(echo "${i}*${dt}+1"|bc)
      te=$(echo "(${i}+1)*${dt}"|bc)
      echo ${iexp} ${zidx} ${i} ${ts} ${te}
      grads -blcx "run ${gs} ${iexp} -zidx ${zidx} -mode ${mode} -ts ${ts} -te ${te}" &
    done
    wait
    echo "------"
  done
done

#bash make.sh
