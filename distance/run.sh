#!/usr/bin/bash
#SBATCH -J dis     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 40      # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o dis.%j.out  # output file


source ~/.bashrc
conda activate py311

for i in $(seq 0 18);do
  #mpirun -np 40 python -u cal_distance.py ${i}
  #mpirun -np 40 python -u axisymmertic.py ${i}
  mpirun -np 40 python -u reconstruct_axismap.py ${i}
done
