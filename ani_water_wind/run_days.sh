#!/usr/bin/bash
#SBATCH -J draw     # Job name
#SBATCH -p ct112     # job partition
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 15      # Run a single task
#SBATCH -A MST114418
#SBATCH -o draw.%j.out  # output file

source ~/.bashrc
mode="SAVEFIG"
gs="draw_wind.gs"
export PERL5LIB=/pkg/compiler/intel/2024/2024.0/opt/oclfpga/host/linux64/bin/perl/lib/5.30.3:/usr/lib64/perl5

for iexp in $(seq 1 3);do
  #ts=145
  #te=217
  ts=1
  te=217
  ~/.local/bin/opengrads -blcx "run ${gs} ${iexp} -mode ${mode} -ts ${ts} -te ${te}" &
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

