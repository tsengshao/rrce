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
gs="draw_wind.gs"

for iexp in 3 9 19;do
  #ts=145
  #te=217
  ts=1
  te=144
  grads -blcx "run ${gs} ${iexp} -mode ${mode} -ts ${ts} -te ${te}" &
done
wait

exit
n2day=72
for iday in 0 9 19 29;do
    ts=$((iday * n2day + 1))
    te=$(((iday+1) * n2day + 1))
    echo ${iday} ${ts} ${te}
    grads -blcx "run ${gs} 1 -mode ${mode} -ts ${ts} -te ${te}" &
done
wait 

