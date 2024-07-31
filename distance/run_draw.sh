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
gs="draw_axisym.gs"
dt=21

for iexp in $(seq 1 19);do
  if [ "${iexp}" == "1" ];then
    dt=230
  else
    dt=21
  fi

  for i in {0..10};do
    ts=$(echo "${i}*${dt}+1"|bc)
    te=$(echo "(${i}+1)*${dt}"|bc)
    echo ${i} ${ts} ${te}
    grads -blcx "run ${gs} ${iexp} -mode ${mode} -ts ${ts} -te ${te}" &
  done
  wait
done
wait

export ofram=9
bash make_video.sh
wait
