#!/usr/bin/bash
#SBATCH -J axisy     # Job name
#SBATCH -p cf112     # job partition
#SBATCH -A MST114418
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 45       # Run a single task
#SBATCH -o out2.%j.out  # output file
#SBATCH --dependency=afterok:928437

source ~/.bashrc
conda activate py311
##  
##  #py='cal_axisymmetricity_ano.py'
##  #py='cal_process_axisymmetricity.py'
##  
##  py='cal_axisymmetricity.py'
##  #for i in $(seq 19 -1 1);do
##  #for i in $(seq 36 -1 19);do
##  for i in $(seq 0 14);do
##    echo ${i}
##    mpirun -np 72 python -u ${py} ${i}
##  done
##  # mpirun -np 20 python -u ${py} 0
##  #mpirun -np 20 python -u ${py} 20
##  
##  

## py='cal_process_axisymmetricity.py'
## for i in $(seq 0 14);do
##   echo ${i}
##   mpirun -np 217 python -u ${py} ${i}
## done

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

py='cal_axisymmetricity_daily.py'

for i in $(seq 0 14); do
  echo "start ${i}"
  srun --mpi=pmi2 --exclusive -n 3 -c 1 python -u ${py} ${i} > log.${i} 2>&1 &
done

wait
