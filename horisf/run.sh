#!/usr/bin/bash
#SBATCH -J sf     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 64       # Run a single task
#SBATCH -w mogamd  # nodelist
#SBATCH -o sf.%j.out  # output file

module purge

module load Intel-oneAPI-2022.1
module load compiler mpi mkl
module load petsc/3.14.0 pnetcdf/1.12.2

export I_MPI_FABRICS=shm
ulimit -s unlimited

./compile.sh
#mpirun -np 1 ./sf.out ${1}
for i in $(seq 1 5);do
  echo ${i}
  mpirun -np 64 ./sf.out ${i}
done
