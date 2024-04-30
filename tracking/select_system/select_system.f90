PROGRAM select
USE irt_parameters, ONLY: domainsize_x, domainsize_y, lperiodic_x, lperiodic_y, &
    miss, n_fields, lat_first, lat_inc, lon_inc, time_steps, max_length_of_track
IMPLICIT NONE

! data parameter
REAL, parameter    :: lon_first=0.0000000

!read tracklinks output
INTEGER            :: header(9)
CHARACTER(len=300) :: fname_tracklinks, fname_tracklinks_out
INTEGER            :: tracks_header(9), cinit_timestep, cduration
!INTEGER            :: ctrackid, ctimestep, cID1, cID2, cage1, cage2,&
!                      cx1, cx2, cy1, cy2,&
!                      clfid2, cslfid2, clbid2, cslbid2
!REAL               :: carea, cfield(3*(n_fields+1)), cxm, cym, cvx, cvy
INTEGER            :: ctrackid, ctimestep(max_length_of_track), cID1(max_length_of_track),&
                      cID2(max_length_of_track), cage1(max_length_of_track), cage2(max_length_of_track),&
                      cx1(max_length_of_track), cx2(max_length_of_track),&
                      cy1(max_length_of_track), cy2(max_length_of_track),&
                      clfid2(max_length_of_track), cslfid2(max_length_of_track),&
                      clbid2(max_length_of_track), cslbid2(max_length_of_track)
REAL               :: carea(max_length_of_track), cfield(max_length_of_track,3*(n_fields+1)),&
                      cxm(max_length_of_track), cym(max_length_of_track),&
                      cvx(max_length_of_track), cvy(max_length_of_track),&
                      cvxx(max_length_of_track), cvyy(max_length_of_track)
INTEGER            :: ii, ix, iy, iz
REAL               :: clonm(max_length_of_track), clatm(max_length_of_track), clsmm(max_length_of_track)
REAL               :: lon(domainsize_x), lat(domainsize_y)

! read trackmask map
CHARACTER(len=300) :: fname_trackmask, fname_trackmask_out
REAL               :: trackmask(domainsize_x,domainsize_y)
INTEGER            :: indx1, indx2, indy1, indy2
INTEGER            :: nxout, nyout
REAL, allocatable  :: trackmaskout(:,:)
REAL, parameter, DIMENSION(2) :: lonb=(/90.,235./), latb=(/-25.,25./)
REAL               :: dummyreal1, dummyreal2
INTEGER            :: reclraw, reclout
INTEGER            :: it

! target trackID
LOGICAL            :: istarget_trackID(5000000)
INTEGER            :: trackID2ftrackID(5000000)
INTEGER            :: nowftrackID
CHARACTER(len=100) :: outfmt

fname_tracklinks = 'irt_tracklinks_output.txt'
fname_tracklinks_out = 'irt_tracklinks_output_select.txt'
OPEN(10, FILE=trim(fname_tracklinks), FORM='formatted', ACTION='read')
OPEN(20, FILE=trim(fname_tracklinks_out), FORM='formatted', ACTION='write')
OPEN(30, FILE='select_tracks_output.csv', FORM='formatted', ACTION='write')

  ! 'newtrackID', 'trackID', 'duration', 'timestep series', 'Area series', 'field
  ! n_fields*3', 'lon series, 'lat series', 'velocity_x', 'velocity_y'
WRITE(outfmt,'(2(A,I1,A,I1,A,I1,A,","))') ('field',ii,'_mean, field',ii,'_min, field',ii,'_max', ii=0,n_fields)
WRITE(30,'(A,A,A)') 'newtrackID, trackID, duration, timestep, area[km2], ',trim(outfmt),' center_lon[deg], center_lat[deg], velocity_x[m/s], velocity_y[m/s]'

istarget_trackID(:) = .False.
trackID2ftrackID(:) = 0
nowftrackID = 0
DO
  read(10,*,end=999) ! newline
  read(10,*) tracks_header(:)
  ctrackid=tracks_header(1)
  cinit_timestep=tracks_header(2)
  cduration = tracks_header(3)
  DO ii=1, cduration
    read(10,*) ctrackid, ctimestep(ii), cID1(ii), cID2(ii), cage1(ii), cage2(ii),&
               carea(ii), cfield(ii,:),&
               cx1(ii), cx2(ii), cy1(ii), cy2(ii), cxm(ii), cym(ii),&
               cvx(ii), cvy(ii), clfid2(ii), cslfid2(ii), clbid2(ii), cslbid2(ii)
    clonm(ii) = lon_first+(cxm(ii)-1)*lon_inc
    clatm(ii) = lat_first+(cym(ii)-1)*lat_inc
    clsmm(ii) = cfield(ii,2)
    cvxx(ii)  = cvx(ii)*lon_inc*111000/30/60
    cvyy(ii)  = cvy(ii)*lat_inc*111000/30/60

    ! check
    !! LAND !!
    !IF(cduration>1 .and. ctimestep(ii)==cinit_timestep .and.&
    !   lonb(1)<=clonm(ii) .and. clonm(ii) <= lonb(2) .and.&
    !   latb(1)<= clatm(ii)  .and. clatm(ii) <= latb(2) .and.&
    !   clsmm(ii).eq.1) then
    !! SEA !!
    IF(cduration>1 .and. ctimestep(ii)==cinit_timestep .and.&
       lonb(1)<=clonm(ii) .and. clonm(ii) <= lonb(2) .and.&
       latb(1)<= clatm(ii)  .and. clatm(ii) <= latb(2) .and.&
       clsmm(ii).lt.1) then
      istarget_trackID(ctrackid) = .True.
      nowftrackID = nowftrackID+1
      trackID2ftrackID(ctrackid) = nowftrackID
    ENDIF

    IF(istarget_trackID(ctrackid))then
      IF(ctimestep(ii)==cinit_timestep)THEN
        WRITE(20,*) '*'
        WRITE(20,*) nowftrackID, tracks_header(:)
      ENDIF
      WRITE(20,*) ctrackid, ctimestep(ii), cID1(ii), cID2(ii), cage1(ii), cage2(ii),&
                  carea(ii), cfield(ii,:),&
                  cx1(ii), cx2(ii), cy1(ii), cy2(ii), cxm(ii), cym(ii),&
                  cvx(ii), cvy(ii), clfid2(ii), cslfid2(ii), clbid2(ii), cslbid2(ii)
    ENDIF ! istarget
  ENDDO !cduration

  ! WRITE CSV file
  IF(istarget_trackID(ctrackid))THEN
    WRITE(30,'(I,2(",",I),", ")',advance="no") nowftrackID, ctrackid, cduration
    WRITE(outfmt, '(I)') cduration-1
    WRITE(30, '(A,'//trim(outfmt)//'(I,","))', advance='no') '"[',(ctimestep(ix),ix=1,cduration-1)
    WRITE(30, '(I,A)', advance='no') ctimestep(cduration),']", '

    WRITE(30, '(A,'//trim(outfmt)//'(F,","))', advance='no') '"[',(carea(ix),ix=1,cduration-1)
    WRITE(30, '(F,A)', advance='no') carea(cduration),']", '
    DO iy=1,n_fields+1
      DO iz=1,3
        WRITE(30, '(A,'//trim(outfmt)//'(F,","))', advance='no') '"[',(cfield(ix,iy+(iz-1)*(n_fields+1)),ix=1,cduration-1)
        WRITE(30, '(F,A)', advance='no') cfield(cduration,iy+(iz-1)*(n_fields+1)),']", '
      ENDDO ! iz
    ENDDO ! iy
    WRITE(30, '(A,'//trim(outfmt)//'(F,","))', advance='no') '"[',(clonm(ix),ix=1,cduration-1)
    WRITE(30, '(F,A)', advance='no') clonm(cduration),']", '
    WRITE(30, '(A,'//trim(outfmt)//'(F,","))', advance='no') '"[',(clatm(ix),ix=1,cduration-1)
    WRITE(30, '(F,A)', advance='no') clatm(cduration),']", '
    WRITE(30, '(A,'//trim(outfmt)//'(F,","))', advance='no') '"[',(cvxx(ix),ix=1,cduration-1)
    WRITE(30, '(A)', advance='no') '-999999.99]", '
    WRITE(30, '(A,'//trim(outfmt)//'(F,","))', advance='no') '"[',(cvyy(ix),ix=1,cduration-1)
    WRITE(30, '(A)', advance='yes') '-999999.99]"'
  ENDIF

ENDDO
999 continue
close(10)
close(20)

! find the index to correspond the lonb / the latb
dummyreal1=99999999
dummyreal2=99999999
DO ix=1,domainsize_x
  lon(ix) = lon_first + lon_inc*(ix-1)
  IF ( abs(lonb(1)-10-lon(ix)) .lt. dummyreal1 )THEN
    dummyreal1 = abs(lonb(1)-10-lon(ix))
    indx1=ix
  ENDIF
  IF ( abs(lonb(2)+10-lon(ix)) .lt. dummyreal2 )THEN
    dummyreal2 = abs(lonb(2)+10-lon(ix))
    indx2=ix
  ENDIF
ENDDO
dummyreal1=99999999
dummyreal2=99999999
DO iy=1,domainsize_y
  lat(iy) = lat_first + lat_inc*(iy-1)
  IF ( abs(latb(1)-10-lat(iy)) .lt. dummyreal1 )THEN
    dummyreal1 = abs(latb(1)-10-lat(iy))
    indy1=iy
  ENDIF
  IF ( abs(latb(2)+10-lat(iy)) .lt. dummyreal2 )THEN
    dummyreal2 = abs(latb(2)+10-lat(iy))
    indy2=iy
  ENDIF
ENDDO

open(50,FILE='select_tracks_info.txt',form='formatted',action='write')
write(50,*) 'original data...'
write(50,*) 'raw_nx=',domainsize_x, ', raw_ny=',domainsize_y
write(50,*) 'raw_lon=',lon(1),' to',lon(domainsize_x)
write(50,*) 'raw_lat=',lat(1),' to',lat(domainsize_y)
write(50,*) 'lon_inc=',lon_inc, ', lat_inc=',lat_inc
write(50,*) ''

write(50,*) 'filter data ... :'
write(50,*) 'nx=',indx2-indx1+1, ', ny=',indy2-indy1+1
write(50,*) 'lon=',lon(indx1),'to',lon(indx2)
write(50,*) 'lat=',lat(indy1),'to',lat(indy2)
write(50,*) 'lon_inc=',lon_inc, ', lat_inc=',lat_inc
write(50,*) ''
write(50,*) 'condiction :' 
write(50,*) 'region: lonb=',lonb,', latb=',latb 
write(50,*) ''

write(50,*) 'new data for grads dimension'
write(50,*) 'xdef ',indx2-indx1+1,'linear',lon(indx1),lon_inc
write(50,*) 'ydef ',indy2-indy1+1,'linear',lat(indy1),lat_inc

write(50,*) ''
write(50,*) 'index lon in raw data: indx1=',indx1, 'indx2=',indx2
write(50,*) 'index lat in raw data: indy1=',indy1, 'indy2=',indy2
close(50)

allocate(trackmaskout(indx2-indx1+1, indy2-indy1+1))
INQUIRE (IOLENGTH=reclraw) trackmask
INQUIRE (IOLENGTH=reclout) trackmaskout
print*, 'reclraw', reclraw
print*, 'reclout', reclout
fname_trackmask = 'irt_tracks_mask.dat'
fname_trackmask_out = 'irt_tracks_mask_select.dat'
OPEN(10,FILE=trim(fname_trackmask),FORM='unformatted',ACTION='read',access='direct',recl=reclraw)
OPEN(20,FILE=trim(fname_trackmask_out),FORM='unformatted',ACTION='write',access='direct',recl=reclout)
DO it=1,time_steps-1
  READ(10,rec=it) trackmask(:,:)
  DO ix=indx1,indx2
    DO iy=indy1,indy2
      dummyreal1 = trackmask(ix,iy)
      IF (dummyreal1 <= 0.)THEN
        trackmaskout(ix-indx1+1, iy-indy1+1) = trackmask(ix,iy)
        cycle
      ENDIF

      IF( .not. istarget_trackID(int(dummyreal1))) THEN
        trackmaskout(ix-indx1+1, iy-indy1+1) = -2.
      ELSE ! target trackID
        !trackmaskout(ix-indx1+1, iy-indy1+1) = trackmask(ix,iy)
        trackmaskout(ix-indx1+1, iy-indy1+1) = real(trackID2ftrackID(int(dummyreal1)))
      ENDIF
    ENDDO !iy
  ENDDO !ix
  WRITE(20,rec=it) trackmaskout(:,:)
ENDDO !it
CLOSE(10)
CLOSE(20)

ENDPROGRAM select
