PROGRAM sub
USE mpi
use netcdf
IMPLICIT NONE

INTEGER, PARAMETER :: nx=384, ny=384, nz=75
REAL, PARAMETER :: dx=3000., dy=3000., height=3.0
INTEGER :: nt
INTEGER :: err, ncid1, varid1
INTEGER :: i,j,k,m,n,o,t, iter
INTEGER :: idxt, irun, ihei
REAL    :: rerr
REAL, DIMENSION(nx,ny)  :: zeta
REAL, DIMENSION(nx,ny,2)   :: sf
REAL*4, DIMENSION(nx,ny)   :: sfr4
REAL, DIMENSION(nz+1) :: zz, zc, rho, rhoz, thbar, thvbar, pbar, pibar&
                       , q1, q2, fnz, fnu
CHARACTER(300) :: path, filename, run, vvmpath, datapath
INTEGER :: ierr, cpu, nproc
INTEGER :: ts, te, idum1, idum2

INTEGER, PARAMETER :: nexp=5
CHARACTER(100) :: runlist(nexp)
INTEGER        :: ntlist(nexp)
runlist = (/'RCE_300K_3km_f0', 'RCE_300K_3km_f05', 'RRCE_3km_f00', 'RRCE_3km_f10', 'RRCE_3km_f15'/)
ntlist  = (/2137, 2030, 3654, 2286, 2161/)

call MPI_INIT(ierr)
call MPI_COMM_SIZE(MPI_COMM_WORLD, nproc, ierr)
call MPI_COMM_RANK(MPI_COMM_WORLD, cpu, ierr)

call GETARG(1,run)
read(run, '(I)') irun
run = runlist(irun)
nt  = ntlist(irun)
datapath="/data/C.shaoyu/rrce/data/horisf/"//run//"/"
vvmpath="/data/C.shaoyu/rrce/vvm/"//run//'/'

!WRITE(*,*) 'vvmpath=',trim(vvmpath)
!WRITE(*,*) 'datapath=',trim(datapath)
!call MPI_ABORT(MPI_COMM_WORLD, -1, ierr)

WRITE(filename,'(A)') trim(vvmpath)//"/fort.98"

! read mean profiles
OPEN(10,FILE=trim(filename), ACTION='read')
DO i=1,188
  READ(10,*)
ENDDO
DO i=1,nz+1
  READ(10,*) j, zz(i), zc(i), fnz(i), fnu(i)
ENDDO
DO i=1,3
  READ(10,*)
ENDDO
DO i=1,nz+1
  READ(10,*) j, rho(i), thbar(i), pbar(i), pibar(i)
ENDDO
DO i=1,3
  READ(10,*)
ENDDO
DO i=1,nz+1
  READ(10,*) j, rhoz(i), rhoz(i), q1(i), q2(i)
ENDDO
DO i=1,3
  READ(10,*)
ENDDO
DO i=2,nz+1
  READ(10,*) j, rhoz(i)
ENDDO
CLOSE(10)

ihei = MINLOC(ABS(zz-height*1e3), 1)
if(cpu==nproc-1) print*, ihei, zz(ihei)
sf(:,:,:) = 0.
idxt=1

idum2=nt/nproc
ts=idum2*cpu ! start from 0
te=idum2*(cpu+1)
if(cpu+1==nproc) te=te+mod(nt,nproc)-1
print*, 'cpu=',cpu,'ts=',ts,'te=',te

INQUIRE(IOLENGTH=idum2) sfr4
WRITE(filename,'(A,F0.2,A)') trim(datapath)//"_", zz(ihei)*1e-3, "km.dat"
OPEN(10,FILE=trim(filename),ACCESS="direct",RECL=idum2)

!DO t=0,1200
DO t=te,ts,-1
if(cpu==nproc-1) print*, '======','cpuid=',cpu,'t=',t,'======'

! read 3-D data field
WRITE(filename,114) trim(vvmpath)//"/archive/"//trim(run)//".L.Dynamic-",t,".nc"
114 FORMAT(A,I6.6,A)

err = nf90_open(trim(filename),NF90_NOWRITE,ncid1)
IF (err/=nf90_noerr) WRITE(*,*) "open fail"
err = nf90_inq_varid(ncid1,"zeta",varid1)
IF (err/=nf90_noerr) WRITE(*,*) "var_inq fail"
err = nf90_get_var(ncid1,varid1,zeta,start=(/ 1,1,ihei,1 /),count=(/ nx,ny,1,1 /))
IF (err/=nf90_noerr) WRITE(*,*) "read fail"
o=0
IF (err/=nf90_noerr) STOP '!! STOP !! READ ERROR'
err = nf90_close(ncid1)

if (t==0) then
  sf(:,:,idxt)=0.
  sfr4 = sf(:,:,idxt)
  goto 5555
endif

call elliptic(nx,ny,dx,dy,zeta(:,:),sf(:,:,3-idxt),sf(:,:,idxt), iter, rerr)
sfr4=sf(:,:,idxt)
if(cpu==nproc-1) print '(A,I5,A,2F10.2,F10.6,A)',&
   '...... iter=',iter,',min,max,rerr=', MINVAL(sfr4), MAXVAL(sfr4),rerr,'======'

5555 continue
WRITE(10,REC=t+1) sfr4
idxt = 3-idxt

ENDDO
CLOSE(10)

call MPI_FINALIZE(ierr)

END PROGRAM sub



!===========================================================================================

subroutine elliptic(nx,ny,dx,dy,zeta, psi_ini, psi, iter, dum1)
implicit none
integer, intent(in) :: nx, ny
REAL, intent(in) :: dx, dy
integer :: i,j,k, im,ip, jm, jp
real :: dum1,dum2,dum3,dum4, dn, en, pre_dum1, errmean
real, dimension(nx,ny), intent(in)    :: psi_ini
real, dimension(nx,ny), intent(in) :: zeta
real, dimension(nx,ny), intent(out)   :: psi
real, dimension(nx,ny)   :: pre_field
INTEGER, intent(out) :: iter

dn=-1./(dx**2)
en=-(dn+dn)
psi=psi_ini


pre_field = psi_ini
dum1=1000
k=0
!do while(dum1>1e-9)
do while(dum1>1e-5 .and. k<100000)
k=k+1
iter=k

dum1=-1
dum4=0.9

do j=1, ny
do i=1, nx
ip = i+1
im = i-1
jp = j+1
jm = j-1
if(i==1)  im = nx
if(i==nx) ip = 1
if(j==1)  jm = ny
if(j==ny) jp = 1


!dum3 = psi(i,j)
!!psi(i,j)  = 0.25 * (psi(ip,j)+psi(im,j)+psi(i,jp)+psi(i,jm)-dx**2*zeta(i,j))
!psi(i,j)  = (1-dum2)*psi(i,j) + dum2 * (&
!             psi(ip,j) + psi(im,j) + psi(i,jp) + psi(i,jm) &
!             + dx**2*zeta(i,j) - 4.*psi(i,j) ) / 4.
!dum1 = max(dum1, abs((psi(i,j)-dum3)/dum3))

dum2 = zeta(i,j) - (dn*psi(ip,j) + dn*psi(im,j) + dn*psi(i,jm) + dn*psi(i,jp))
dum3 = psi(i,j)
psi(i,j) = (1-dum4)*psi(i,j) + dum4/(en+en)*dum2
!dum1 = max(dum1, abs((dum3-psi(i,j))/psi(i,j)))
!dum1 = max(dum1, abs((dum3-psi(i,j))/psi(i,j)) )
dum1 = max(dum1, abs(dum3-psi(i,j)) )

enddo
enddo

print*, 'counter=',k,', ',dum1
enddo

end subroutine elliptic




