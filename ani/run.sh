#!/usr/bin/bash
#SBATCH -J draw     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 5       # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o draw.%j.out  # output file


source ~/.bashrc

grads -blcx "run draw.gs 1" &
grads -blcx "run draw.gs 2" &
grads -blcx "run draw.gs 3" &
grads -blcx "run draw.gs 4" &
grads -blcx "run draw.gs 5" &

wait
