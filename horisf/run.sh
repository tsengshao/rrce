#!/usr/bin/bash
#SBATCH -J sf     # Job name
#SBATCH -p all     # job partition
#SBATCH -N 1       # Run all processes on a single node 
#SBATCH -c 1        # cores per MPI rank
#SBATCH -n 10       # Run a single task
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
#for i in $(seq 2 5);do
# for i in 5 4 3 2 1;do
#   echo ${i}
#   mpirun -np 64 ./sf ${i}
# done

mpirun -np 2 ./sf 5 &
mpirun -np 2 ./sf 4 &
mpirun -np 2 ./sf 3 &
mpirun -np 2 ./sf 2 &
mpirun -np 2 ./sf 1 &
wait



