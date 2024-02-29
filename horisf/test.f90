PROGRAM sub
USE mpi
use netcdf
IMPLICIT NONE

INTEGER, PARAMETER :: nx=384, ny=384, nz=75
INTEGER :: err, ncid1, varid1
INTEGER :: ierr, cpu, nproc
INTEGER :: ts, te, idum2, nt

nt=200

call MPI_INIT(ierr)
call MPI_COMM_SIZE(MPI_COMM_WORLD, nproc, ierr)
call MPI_COMM_RANK(MPI_COMM_WORLD, cpu, ierr)

idum2=nt/nproc
ts=idum2*cpu ! start from 0
te=idum2*(cpu+1)
if(cpu+1==nproc) te=te+mod(nt,nproc)-1
print*, 'cpu=',cpu,'ts=',ts,'te=',te

call MPI_FINALIZE(ierr)

END PROGRAM sub

