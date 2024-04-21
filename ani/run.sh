#!/usr/bin/bash
#SBATCH -J draw     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 7      # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o draw.%j.out  # output file


source ~/.bashrc

#for i in $(seq 1 6);do
for i in 1 2 3 4 ;do
args="${i} -mode SAVEFIG"
grads -blcx "run draw.gs ${args} -ts 1    -te 200" &
grads -blcx "run draw.gs ${args} -ts 201  -te 400" &
grads -blcx "run draw.gs ${args} -ts 401  -te 600" &
grads -blcx "run draw.gs ${args} -ts 601  -te 800" &
grads -blcx "run draw.gs ${args} -ts 1001 -te 1200" &
grads -blcx "run draw.gs ${args} -ts 1201 -te 1400" &
grads -blcx "run draw.gs ${args} -ts 1401 -te 1600" &
wait
done
