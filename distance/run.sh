#!/usr/bin/bash
#SBATCH -J dis     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 30      # Run a single task
#SBATCH -w node01  # nodelist
#SBATCH -o dis.%j.out  # output file


source ~/.bashrc
conda activate py311

for i in $(seq 0 18);do
  mpirun -np 30 python -u cal_distance.py ${i}
  mpirun -np 30 python -u axisymmertic.py ${i}
  mpirun -np 30 python -u reconstruct_axismap.py ${i}
  mpirun -np 30 python -u cal_axisymmetricity.py ${i}
done
