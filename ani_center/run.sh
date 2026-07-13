#!/usr/bin/bash
#SBATCH -J draw     # Job name
#SBATCH -p ct448     # job partition
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 217      # Run a single task
#SBATCH -o draw.%j.out  # output file
#SBATCH -A MST114418

source ~/.bashrc
export PERL5LIB=/pkg/compiler/intel/2024/2024.0/opt/oclfpga/host/linux64/bin/perl/lib/5.30.3:/usr/lib64/perl5
mode="SAVEFIG"
gs="draw_conzeta.gs"
gs="draw_zeta.gs"

for iexp in $(seq 1 14);do
#for iexp in 2;do
  for ts in $(seq 1 217);do
    te=${ts}
    ~/.local/bin/opengrads -blcx "run ${gs} ${iexp} -mode ${mode} -ts ${ts} -te ${te}" &
    #grads -blcx "run ${gs} ${iexp} -mode ${mode} -ts ${ts} -te ${ts}" &
  done
  wait
done
wait

# for ts in $(seq 1 72 2161);do
#     te=$(echo "{ts}+1"|bc)
#     grads -blcx "run ${gs} 1 -mode ${mode} -ts ${ts} -te ${ts}" &
# done
# wait
