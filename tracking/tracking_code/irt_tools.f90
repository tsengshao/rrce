MODULE irt_tools
use netcdf
USE irt_parameters, ONLY: domainsize_x, domainsize_y,time_steps
IMPLICIT NONE

CONTAINS

SUBROUTINE read_single_nc(fname,varname,itime,outdata)
CHARACTER(len=90), INTENT(in)  :: fname
CHARACTER(*), INTENT(in)  :: varname
INTEGER          , INTENT(in)  :: itime
REAL             , INTENT(out) :: outdata(domainsize_x,domainsize_y)
INTEGER                        :: lrec
INTEGER                        :: err, ncid, varid

err = nf90_open(trim(fname),NF90_NOWRITE,ncid)
IF (err/=nf90_noerr) WRITE(*,*) "nc open fail"

err = nf90_inq_varid(ncid,trim(varname),varid)
IF (err/=nf90_noerr) WRITE(*,*) "var_inq fail"

err = nf90_get_var(ncid,varid,outdata,start=(/ 1,1,itime /),count=(/ domainsize_x,domainsize_y,1 /))
IF (err/=nf90_noerr) WRITE(*,*) "var_read fail"

err = nf90_close(ncid)
IF (err/=nf90_noerr) WRITE(*,*) "nc close fail"

END SUBROUTINE read_single_nc


SUBROUTINE read_single_dat(fname,itime,outdata)
CHARACTER(len=90), INTENT(in)  :: fname
INTEGER          , INTENT(in)  :: itime
REAL             , INTENT(out) :: outdata(domainsize_x,domainsize_y)
INTEGER                        :: lrec

INQUIRE(IOLENGTH=lrec) outdata
OPEN(10, FILE=fname, FORM='unformatted', ACCESS='direct',RECL=lrec)
READ(10,rec=itime) outdata
CLOSE(10)
END SUBROUTINE read_single_dat




SUBROUTINE write_dat(file_id,itime,field)
REAL, INTENT(IN)      :: field(domainsize_x,domainsize_y)
INTEGER, INTENT(IN)   :: file_id, itime
LOGICAL               :: itsopen

!inquire(unit=file_id, opened=itsopen) 
!print*, itsopen
WRITE (file_id,rec=itime) field
END SUBROUTINE write_dat



END MODULE irt_tools
