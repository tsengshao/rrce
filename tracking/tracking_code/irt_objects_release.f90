! identifies objects and establishes links
! needs input data as SRV file
! Compile: ifort -no-wrap-margin -o irt_objects_release.x irt_objects_release.f90 irt_parameters.f90

PROGRAM irt_objects

USE irt_tools
USE irt_parameters, ONLY: domainsize_x, domainsize_y, lperiodic_x, lperiodic_y, &
    n_fields, time_steps, nt_bins, nx_bins, ny_bins, threshold, &
    minimum_size, max_no_of_cells, miss

IMPLICIT NONE

INTEGER              :: domsize_x, domsize_y,lrec

INTEGER              :: ii, ij,ix,iy,idx,idy
REAL                 :: readdata(domainsize_x,domainsize_y)
!REAL, ALLOCATABLE    :: input_field(:,:,:)
!REAL, ALLOCATABLE    :: overlay_field(:,:)
!INTEGER, ALLOCATABLE :: event_number(:,:,:)
!LOGICAL, ALLOCATABLE :: occupied(:,:)
REAL                 :: input_field(domainsize_x,domainsize_y,n_fields+1)
REAL                 :: overlay_field(domainsize_x,domainsize_y)
INTEGER              :: event_number(domainsize_x,domainsize_y,3)
LOGICAL              :: occupied(domainsize_x,domainsize_y)

INTEGER              :: i,j,i_prev,i_act,c,t,it,fileid
INTEGER              :: counter_actual, counter_previous, counter_mixed
INTEGER              :: counter_total_actual, counter_total_previous
LOGICAL              :: delete_cell
REAL                 :: totarea_sum

! for cell statistics
REAL                 :: totarea(max_no_of_cells,2)
REAL                 :: field_mean(max_no_of_cells,2,n_fields+1)
REAL                 :: field_min(max_no_of_cells,2,n_fields+1)
REAL                 :: field_max(max_no_of_cells,2,n_fields+1)
REAL                 :: center_of_mass_x(max_no_of_cells,2),center_of_mass_y(max_no_of_cells,2)
INTEGER              :: cell_age1(max_no_of_cells,2), cell_age2(max_no_of_cells,2)
INTEGER              :: first_point_x(max_no_of_cells,2),first_point_y(max_no_of_cells,2)
INTEGER              :: xfirst(max_no_of_cells,2), xlast(max_no_of_cells,2)
INTEGER              :: yfirst(max_no_of_cells,2), ylast(max_no_of_cells,2)
INTEGER              :: checkcounter

! variables for the overlay field
INTEGER              :: xfirst_mixed,xlast_mixed,yfirst_mixed,ylast_mixed

! for link statistics
INTEGER              :: largest_forward_link(max_no_of_cells)
REAL                 :: largest_forward_link_size(max_no_of_cells)
INTEGER              :: second_largest_forward_link(max_no_of_cells)
REAL                 :: second_largest_forward_link_size(max_no_of_cells)
INTEGER              :: largest_backward_link(max_no_of_cells)
REAL                 :: largest_backward_link_size(max_no_of_cells)
INTEGER              :: second_largest_backward_link(max_no_of_cells)
REAL                 :: second_largest_backward_link_size(max_no_of_cells)

! diagnosed cell velocities
REAL                 :: velocity_x(max_no_of_cells)
REAL                 :: velocity_y(max_no_of_cells)
REAL                 :: area_weight(max_no_of_cells)

! dummy variables for velocity diagnosis
REAL                 :: dx,dy

INTEGER              :: srv_header_input(8)
INTEGER              :: srv_header_coarse(8)

! file names
CHARACTER (len=90)   :: input_filename(n_fields+1)
CHARACTER (len=90)   :: output_filename
CHARACTER (len=90)   :: mask_filename
CHARACTER (len=90)   :: coarsevel_filename

CHARACTER (len=1)    :: iteration_str
INTEGER              :: headlen

! time handling
INTEGER              :: n_actual,n_previous,n_previous_it
LOGICAL              :: previous_exists
INTEGER              :: previousdate, previoustime, previoustimestep
INTEGER              :: actualdate, actualtime

! which iteration?
INTEGER              :: iteration = 1   ! 1: first iteration
                                        ! 2: second iteration

! for advection velocity field
REAL                 :: coarse_vel_x(nx_bins,ny_bins,nt_bins)
REAL                 :: coarse_vel_y(nx_bins,ny_bins,nt_bins)
REAL                 :: coarse_dummy(nx_bins,ny_bins)
REAL                 :: vx,vy


INQUIRE(IOLENGTH=lrec) readdata
DO i=1,n_fields+1
  WRITE(input_filename(i),"(A18,I2.2,A)") "irt_objects_input_",i-1,""
ENDDO

output_filename = "irt_objects_output.txt"
mask_filename = "irt_objects_mask.dat"
coarsevel_filename = "irt_advection_field.srv"

CALL getarg(1,iteration_str)

IF (iteration_str .EQ. "1") THEN
   iteration = 1
ELSEIF (iteration_str .EQ. "2") THEN
   iteration = 2
ELSE
  WRITE (*,*) "ERROR: 1 for first iteration, 2 for subsequent iterations"
  STOP
ENDIF

OPEN(20,FILE=trim(output_filename),FORM='formatted', ACTION='write')
OPEN(30,FILE=trim(mask_filename),FORM='unformatted',ACTION='write',ACCESS='direct',recl=lrec)

! if not first iteration, read in the coarse velocity field
IF (iteration == 2) THEN
  OPEN (50,FILE=trim(coarsevel_filename),FORM='unformatted', STATUS='old', ACTION='read')
  DO i=1,nt_bins
    READ (50, END=200) srv_header_coarse
    READ (50) coarse_vel_x(:,:,i)
    READ (50) srv_header_coarse
    READ (50) coarse_vel_y(:,:,i)
    READ (50) srv_header_coarse
    READ (50) coarse_dummy(:,:)
  ENDDO
  CLOSE (50)
ENDIF

n_actual   = 1
n_previous = 2

previous_exists = .FALSE.  ! because it's the first time step
counter_actual = 0
counter_total_actual = 0
counter_total_previous = 0
!previoustimestep=-1

velocity_x = 0.
velocity_y = 0.
area_weight = 0.

! beginning of main loop
DO previoustimestep=0,time_steps-1

previousdate=srv_header_input(3)
previoustime=srv_header_input(4)
!previoustimestep=previoustimestep+1

input_field(:,:,:) = miss-1.
DO fileid=1,n_fields+1
  CALL read_single_dat(input_filename(fileid),previoustimestep+1,input_field(:,:,fileid))
ENDDO

!!!ORIGINAL srv reader!!!
!! DO fileid=0,n_fields
!!   READ (fileid,END=200) srv_header_input
!!   actualdate=srv_header_input(3)
!!   actualtime=srv_header_input(4)
!!   IF (lperiodic_x .AND. lperiodic_y) THEN
!!     READ (fileid) input_field(:,:,fileid)
!!   ELSEIF (lperiodic_y) THEN
!!     input_field(:,:,fileid) = miss-1.
!!     READ (fileid) input_field(2:domsize_x-1,:,fileid)
!!   ELSEIF (lperiodic_x) THEN
!!     input_field(:,:,fileid) = miss-1.
!!     READ (fileid) input_field(:,2:domsize_y-1,fileid)
!!   ELSE
!!     input_field(:,:,fileid) = miss-1.
!!     READ (fileid) input_field(2:domsize_x-1,2:domsize_y-1,fileid)
!!   ENDIF
!! ENDDO
occupied(:,:)=.FALSE.
event_number(:,:,n_actual)=0
!counter_previous = MAX(1,counter_actual)
counter_previous = counter_actual
counter_actual=0


! identification of patches
DO iy=1, domainsize_y
  DO ix=1, domainsize_x
    IF (input_field(ix,iy,1) .GE. threshold .AND. .NOT. occupied(ix,iy)) THEN
      counter_actual = counter_actual+1
      IF (counter_actual .GT. max_no_of_cells) THEN
        WRITE(*,*) "ERROR: number of cells >",max_no_of_cells
        STOP
      ENDIF
      !!  ii = ix
      !!  ij = iy
      !!  totarea(counter_actual,n_actual)=0
      !!  field_mean(counter_actual,n_actual,:)=0
      !!  field_min(counter_actual,n_actual,:)=1E+9
      !!  field_max(counter_actual,n_actual,:)=-1E+9
      !!  center_of_mass_x(counter_actual,n_actual)=0
      !!  center_of_mass_y(counter_actual,n_actual)=0
      !!  xfirst(counter_actual,n_actual)=ii
      !!  xlast(counter_actual,n_actual)=ii
      !!  yfirst(counter_actual,n_actual)=ij
      !!  ylast(counter_actual,n_actual)=ij
      !!  delete_cell = .FALSE.
      !!  CALL area(ii, ij, input_field, &
      !!     occupied, counter_actual,event_number(:,:,n_actual),totarea(counter_actual,n_actual), &
      !!     field_mean(counter_actual,n_actual,:),field_min(counter_actual,n_actual,:),field_max(counter_actual,n_actual,:), &
      !!     center_of_mass_x(counter_actual,n_actual),center_of_mass_y(counter_actual,n_actual), &
      !!     delete_cell,xfirst(counter_actual,n_actual),xlast(counter_actual,n_actual), &
      !!     yfirst(counter_actual,n_actual),ylast(counter_actual,n_actual))
      CALL four_connect(ix, iy, input_field, &
         occupied, counter_actual,event_number(:,:,n_actual),totarea(counter_actual,n_actual), &
         field_mean(counter_actual,n_actual,:),field_min(counter_actual,n_actual,:),field_max(counter_actual,n_actual,:), &
         center_of_mass_x(counter_actual,n_actual),center_of_mass_y(counter_actual,n_actual), &
         delete_cell,xfirst(counter_actual,n_actual),xlast(counter_actual,n_actual), &
         yfirst(counter_actual,n_actual),ylast(counter_actual,n_actual))
      IF (delete_cell) THEN
        ! delete this cell by overwriting it with -1 in event_number
        CALL set_event_number_to_value(domainsize_x,domainsize_y,-1,event_number(:,:,n_actual),counter_actual, &
                                       xfirst(counter_actual,n_actual),xlast(counter_actual,n_actual), &
                                       yfirst(counter_actual,n_actual),ylast(counter_actual,n_actual))
        counter_actual = counter_actual - 1
      ELSEIF (totarea(counter_actual,n_actual) .GT. minimum_size) THEN
        !! already done in four_connect function
        !! center_of_mass_x(counter_actual,n_actual)=center_of_mass_x(counter_actual,n_actual)/ &
        !!                                           field_mean(counter_actual,n_actual,1)
        !! center_of_mass_y(counter_actual,n_actual)=center_of_mass_y(counter_actual,n_actual)/ &
        !!                                           field_mean(counter_actual,n_actual,1)
        !! field_mean(counter_actual,n_actual,:)=field_mean(counter_actual,n_actual,:)/ &
        !!                                       totarea(counter_actual,n_actual)
        
        !! ! take care for periodic boundary conditions
        !! IF (center_of_mass_x(counter_actual,n_actual) .GE. domainsize_x+1) THEN
        !!   center_of_mass_x(counter_actual,n_actual)=center_of_mass_x(counter_actual,n_actual)-domainsize_x
        !! ENDIF
        !! IF (center_of_mass_x(counter_actual,n_actual) .LT. 1) THEN
        !!   center_of_mass_x(counter_actual,n_actual)=center_of_mass_x(counter_actual,n_actual)+domainsize_x
        !! ENDIF
        !! IF (center_of_mass_y(counter_actual,n_actual) .GE. domainsize_y+1) THEN
        !!   center_of_mass_y(counter_actual,n_actual)=center_of_mass_y(counter_actual,n_actual)-domainsize_y
        !! ENDIF
        !! IF (center_of_mass_y(counter_actual,n_actual) .LT. 1) THEN
        !!   center_of_mass_y(counter_actual,n_actual)=center_of_mass_y(counter_actual,n_actual)+domainsize_y
        !! ENDIF
        
        first_point_x(counter_actual,n_actual)=ix
        first_point_y(counter_actual,n_actual)=iy
        cell_age1(counter_actual,n_actual)=1   ! new born cell. Will be adjusted later
        cell_age2(counter_actual,n_actual)=1
      ELSE   ! if cell is too small, delete it
        CALL set_event_number_to_value(domainsize_x,domainsize_y,0,event_number(:,:,n_actual),counter_actual, &
                                       xfirst(counter_actual,n_actual),xlast(counter_actual,n_actual), &
                                       yfirst(counter_actual,n_actual),ylast(counter_actual,n_actual))
        counter_actual = counter_actual - 1
      ENDIF
    ELSE
      occupied(ix,iy)=.TRUE.
    ENDIF
  ENDDO
ENDDO

WRITE(*,*) 't=',previoustimestep+1,'(total_obj=',counter_actual,')'

!! write the mask 2d fields
CALL write_dat(30,previoustimestep+1,REAL(event_number(:,:,n_actual)))

counter_total_previous = counter_total_actual
counter_total_actual = counter_total_actual+counter_previous

! do we have to read in the next step also?
IF (.NOT. previous_exists) THEN
  previous_exists = .TRUE.
  ! flip time indices and advance 1 time step
  n_actual   = 3-n_actual
  n_previous = 3-n_previous
  !WRITE (*,*) "JUMP"
  CYCLE
ENDIF

! perform second iteration on "previous" field
IF (iteration .EQ. 2) THEN
  event_number(:,:,3)=0
  DO iy=1,domainsize_y
    DO ix=1,domainsize_x
      i = event_number(ix,iy,n_previous)
       IF (i .LT. 1) CYCLE
      ii  = NINT(center_of_mass_x(i,n_previous))
      ij  = NINT(center_of_mass_y(i,n_previous))
      CALL time_interpolation(domainsize_x,domainsize_y,time_steps,nx_bins,ny_bins,nt_bins,lperiodic_x,lperiodic_y, &
                              coarse_vel_x,coarse_vel_y,ii,ij,MAX(1,previoustimestep),vx,vy)
      idx = NINT(vx)
      idy = NINT(vy)
      IF (idx .LE. miss+1 .OR. idy .LE. miss+1) CYCLE
      IF (ix+idx .LT. 1 .OR. ix+idx .GT. domainsize_x .OR. iy+idy .LT. 1 .OR. iy+idy .GT. domainsize_y) CYCLE
      event_number(ix+idx,iy+idy,3) = i
      first_point_x(i,n_previous) = ix+idx
      first_point_y(i,n_previous) = iy+idy
    ENDDO
  ENDDO
  n_previous_it = 3
  !CALL write_srv(domsize_x,domsize_y,REAL(event_number(:,:,4)),previousdate,previoustime+30,30)
ELSE
  n_previous_it = n_previous
ENDIF


! identify foreward links and velocity
largest_forward_link=0
largest_forward_link_size=0
second_largest_forward_link=0
second_largest_forward_link_size=0

DO iy=1, domainsize_y
  DO ix=1, domainsize_x
    i_prev = event_number(ix,iy,n_previous_it)
    i_act = event_number(ix,iy,n_actual)
    IF (i_prev .GT. 0 .AND. i_act .NE. 0) THEN
      IF (largest_forward_link(i_prev) .EQ. -1) CYCLE
      IF (i_act .GT. 0) THEN
        ! already done?
        IF (largest_forward_link(i_prev) .EQ. counter_total_actual+i_act .OR. &
            second_largest_forward_link(i_prev) .EQ. counter_total_actual+i_act) CYCLE
        dx = center_of_mass_x(i_act,n_actual)-center_of_mass_x(i_prev,n_previous)
        dy = center_of_mass_y(i_act,n_actual)-center_of_mass_y(i_prev,n_previous)
        IF (dx .GT. domainsize_x/2)  dx = dx-domsize_x
        IF (dx .LT. -domainsize_x/2) dx = dx+domsize_x
        IF (dy .GT. domainsize_y/2)  dy = dy-domainsize_y
        IF (dy .LT. -domainsize_y/2) dy = dy+domainsize_y
        velocity_x(i_prev) = velocity_x(i_prev)+dx*totarea(i_act,n_actual)
        velocity_y(i_prev) = velocity_y(i_prev)+dy*totarea(i_act,n_actual)
        area_weight(i_prev) = area_weight(i_prev)+totarea(i_act,n_actual)
        IF (totarea(i_act,n_actual) .GT. largest_forward_link_size(i_prev)) THEN
          second_largest_forward_link(i_prev) = largest_forward_link(i_prev)
          second_largest_forward_link_size(i_prev) = largest_forward_link_size(i_prev)
          largest_forward_link(i_prev) = counter_total_actual+i_act
          largest_forward_link_size(i_prev) = totarea(i_act,n_actual)
        ELSEIF (totarea(i_act,n_actual) .GT. second_largest_forward_link_size(i_prev)) THEN
          second_largest_forward_link(i_prev) = counter_total_actual+i_act
          second_largest_forward_link_size(i_prev) = totarea(i_act,n_actual)
        ENDIF
      ELSE
        largest_forward_link(i_prev) = -1 ! interrupted by missing values
      ENDIF  
    ENDIF
  ENDDO
ENDDO
DO i=1,counter_previous
  !WRITE(*,*)i,velocity_x(i),velocity_y(i),area_weight(i)
  IF (area_weight(i) .GE. minimum_size) THEN
    velocity_x(i) = velocity_x(i)/area_weight(i)
    velocity_y(i) = velocity_y(i)/area_weight(i)
  ELSE
    velocity_x(i) = miss
    velocity_y(i) = miss
  ENDIF
ENDDO

! write sizes
IF (counter_previous==0) THEN
  !IF (cell_age1(1,n_previous).LT.cell_age2(1,n_previous)) THEN
  !  WRITE(*,*) "cell age(cp=1):",cell_age1(1,n_previous),cell_age2(1,n_previous)
  !ENDIF
  WRITE(20,*) previoustimestep,0,counter_total_previous, &
              cell_age1(1,n_previous),cell_age2(1,n_previous),totarea(1,n_previous), &
              field_mean(1,n_previous,:),field_min(1,n_previous,:),field_max(1,n_previous,:), &
              xfirst(1,n_previous),xlast(1,n_previous),yfirst(1,n_previous),ylast(1,n_previous), &
              center_of_mass_x(1,n_previous),center_of_mass_y(1,n_previous), &
              velocity_x(1),velocity_y(1), &
              largest_forward_link(1),largest_forward_link_size(1), &
              second_largest_forward_link(1),second_largest_forward_link_size(1), &
              largest_backward_link(1),largest_backward_link_size(1), &
              second_largest_backward_link(1),second_largest_backward_link_size(1)
ENDIF
DO i=1,counter_previous
  !IF (cell_age1(i,n_previous).LT.cell_age2(i,n_previous)) THEN
  !  WRITE(*,*) "cell age:",cell_age1(i,n_previous),cell_age2(i,n_previous)
  !ENDIF
  WRITE(20,*) previoustimestep,i,counter_total_previous+i, &
              cell_age1(i,n_previous),cell_age2(i,n_previous),totarea(i,n_previous), &
              field_mean(i,n_previous,:),field_min(i,n_previous,:),field_max(i,n_previous,:), &
              xfirst(i,n_previous),xlast(i,n_previous),yfirst(i,n_previous),ylast(i,n_previous), &
              center_of_mass_x(i,n_previous),center_of_mass_y(i,n_previous), &
              velocity_x(i),velocity_y(i), &
              largest_forward_link(i),largest_forward_link_size(i), &
              second_largest_forward_link(i),second_largest_forward_link_size(i), &
              largest_backward_link(i),largest_backward_link_size(i), &
              second_largest_backward_link(i),second_largest_backward_link_size(i)
ENDDO

! identify backward links
largest_backward_link=0
largest_backward_link_size=0
second_largest_backward_link=0
second_largest_backward_link_size=0
velocity_x = 0.
velocity_y = 0.
area_weight = 0.
DO iy=1, domainsize_y
  DO ix=1, domainsize_x
    i_prev = event_number(ix,iy,n_previous_it)
    i_act = event_number(ix,iy,n_actual)
    IF (i_act .GT. 0 .AND. i_prev .NE. 0) THEN
      IF (largest_backward_link(i_act) .EQ. -1) CYCLE
      IF (i_prev .GT. 0) THEN
        ! already done?
        IF (largest_backward_link(i_act) .EQ. counter_total_previous+i_prev .OR. &
            second_largest_backward_link(i_act) .EQ. counter_total_previous+i_prev) CYCLE
        dx = center_of_mass_x(i_act,n_actual)-center_of_mass_x(i_prev,n_previous)
        dy = center_of_mass_y(i_act,n_actual)-center_of_mass_y(i_prev,n_previous)
        IF (dx .GT.  domainsize_x/2)  dx = dx-domainsize_x
        IF (dx .LT. -domainsize_x/2)  dx = dx+domainsize_x
        IF (dy .GT.  domainsize_y/2)  dy = dy-domainsize_y
        IF (dy .LT. -domainsize_y/2)  dy = dy+domainsize_y
        velocity_x(i_prev) = velocity_x(i_prev)+dx*totarea(i_act,n_actual)
        velocity_y(i_prev) = velocity_y(i_prev)+dy*totarea(i_act,n_actual)
        area_weight(i_prev) = area_weight(i_prev)+totarea(i_act,n_actual)
        IF (cell_age1(i_prev,n_previous) .GE. cell_age1(i_act,n_actual)) THEN
          ! object inherits age from oldest predecessor
          cell_age1(i_act,n_actual)=cell_age1(i_prev,n_previous)+1 ! aging cell
        ENDIF
        IF (totarea(i_prev,n_previous) .GT. largest_backward_link_size(i_act)) THEN
          second_largest_backward_link(i_act) = largest_backward_link(i_act)
          second_largest_backward_link_size(i_act) = largest_backward_link_size(i_act)
          largest_backward_link(i_act) = counter_total_previous+i_prev
          largest_backward_link_size(i_act) = totarea(i_prev,n_previous)
          ! object inherits age from largest predecessor
          cell_age2(i_act,n_actual)=cell_age2(i_prev,n_previous)+1 ! aging cell
        ELSEIF (totarea(i_prev,n_previous) .GT. second_largest_backward_link_size(i_act)) THEN
          second_largest_backward_link(i_act) = counter_total_previous+i_prev
          second_largest_backward_link_size(i_act) = totarea(i_prev,n_previous)
        ENDIF
      ELSE
        largest_backward_link(i_act) = -1 ! interrupted by missing values
      ENDIF
    ENDIF
  ENDDO
ENDDO

! flip time indices
n_actual   = 3-n_actual
n_previous = 3-n_previous

! end main loop
ENDDO

200 CONTINUE

! close input/output files
CLOSE(20)

!DO fileid=1,n_fields+1
!  CLOSE(fileid)
!ENDDO


END PROGRAM irt_objects


!++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
!                           SUBROUTINES
!++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


SUBROUTINE write_srv(field,date,time,file_id)

  USE irt_parameters, ONLY: domainsize_x, domainsize_y

  IMPLICIT NONE
  !INTEGER, INTENT(IN)   :: domainsize_x,domainsize_y
  REAL, INTENT(IN)      :: field(domainsize_x,domainsize_y)
  INTEGER, INTENT(IN)   :: date,time
  INTEGER, INTENT(IN)   :: file_id
  INTEGER               :: srv_header(8)

  srv_header(1) = 1	      ! Code
  srv_header(2) = 1	      ! Level
  srv_header(3) = date        ! Datum
  srv_header(4) = time        ! Zeitinkrement
  srv_header(5) = domainsize_x
  srv_header(6) = domainsize_y
  srv_header(7) = 0
  srv_header(8) = 0

  WRITE (file_id) srv_header
  WRITE (file_id) field
  
  RETURN

END SUBROUTINE write_srv


!++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

SUBROUTINE set_event_number_to_value(domainsize_x,domainsize_y,value,event_number,nevent, &
                                     xfirst,xlast,yfirst,ylast)

  USE irt_parameters, ONLY: lperiodic_x, lperiodic_y

  IMPLICIT NONE
  INTEGER, INTENT(IN)       :: domainsize_x,domainsize_y
  INTEGER, INTENT(IN)       :: value
  INTEGER, INTENT(INOUT)    :: event_number(domainsize_x,domainsize_y)
  INTEGER, INTENT(IN)       :: nevent
  INTEGER, INTENT(IN)       :: xfirst,xlast,yfirst,ylast
  INTEGER                   :: ix,iy,ix_mod,iy_mod
  integer                   :: x1, x2, y1, y2

  x1 = xfirst
  x2 = xlast
  y1 = yfirst
  y2 = ylast

  !! reminding the object over the boundary in periodic condiction
  if( x2 < x1 .and. lperiodic_x) x2 = x2 + domainsize_x
  if( y2 < y1 .and. lperiodic_y) y2 = y2 + domainsize_y

  if(x2<x1) STOP "!!! ERROR !!!, func: set_event_number, x2 should be larger than or equal to x1"
  if(y2<y1) STOP "!!! ERROR !!!, func: set_event_number, y2 should be larger than or equal to y1"

  DO iy=y1,y2
    DO ix=x1,x2
      ix_mod = MOD(ix-1+domainsize_x,domainsize_x)+1
      iy_mod = MOD(iy-1+domainsize_y,domainsize_y)+1
      IF (event_number(ix_mod,iy_mod)==nevent) event_number(ix_mod,iy_mod)=value
    ENDDO
  ENDDO

  RETURN

END SUBROUTINE set_event_number_to_value

!++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

SUBROUTINE decrease_resolution(domsize_x,domsize_y,miss,field)

  IMPLICIT NONE
  INTEGER, INTENT(IN)   :: domsize_x,domsize_y
  REAL, INTENT(INOUT)   :: field(domsize_x,domsize_y)
  REAL                  :: value_mean
  REAL, INTENT(IN)      :: miss            ! value<miss ==> missing_value
  INTEGER               :: ix,iy

  ! build 2x2 km grid out of 1x1 km grid
  DO ix=1,domsize_x-1,2
    DO iy=1,domsize_y-1,2
      IF (field(ix,iy) .LT. miss .OR. field(ix,iy+1) .LT. miss .OR. field(ix+1,iy) .LT. miss .OR. field(ix+1,iy+1) .LT. miss) THEN
	value_mean = miss-1
      ELSE
        value_mean = NINT((field(ix,iy)+field(ix,iy+1)+field(ix+1,iy)+field(ix+1,iy+1))*0.25)
      ENDIF
      field(ix  ,iy  ) = value_mean
      field(ix  ,iy+1) = value_mean
      field(ix+1,iy  ) = value_mean
      field(ix+1,iy+1) = value_mean
    ENDDO
  ENDDO

END SUBROUTINE decrease_resolution

!++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

SUBROUTINE four_connect(startX, startY, input_field, occupied, nowid,&
                        label_field, totarea, field_mean, field_min, field_max,&
                        COMx, COMy, delete_cell, xfirst, xlast, yfirst, ylast)
USE irt_parameters, ONLY: n_fields, threshold, miss, llonlatgrid, &
                          unit_area, lat_first, lat_inc, lon_inc, &
                          lperiodic_x, lperiodic_y, domainsize_x, domainsize_y

REAL, intent(in)    :: input_field(domainsize_x,domainsize_y,n_fields+1)
INTEGER, intent(inout) :: label_field(domainsize_x,domainsize_y)
INTEGER, intent(in) :: startX, startY, nowid
LOGICAL, intent(inout) :: occupied(domainsize_x,domainsize_y)

REAL, intent(out) :: totarea, field_mean(n_fields+1)
REAL, intent(out) :: field_min(n_fields+1), field_max(n_fields+1)
REAL, intent(out) :: COMx, COMy
LOGICAL, intent(out) :: delete_cell
INTEGER, intent(out) :: xfirst, xlast, yfirst, ylast

INTEGER, parameter :: GRIDSIZE=domainsize_x*domainsize_x
INTEGER            :: stackX(GRIDSIZE),stackY(GRIDSIZE), stack_num
REAL               :: gridboxarea
INTEGER            :: fileid
REAL, PARAMETER    :: deg2rad = 3.141592654/180.

INTEGER, PARAMETER :: nmove=4
INTEGER, PARAMETER :: moveX(nmove)=(/0,0,-1,1/)
INTEGER, PARAMETER :: moveY(nmove)=(/-1,1,0,0/)

INTEGER             :: iox, ioy, imove, locx2, locy2, locx, locy, fieldid

IF(input_field(startX,startY,1) .lt. threshold .or. occupied(startX,startY)) then
  stop ' !!SUBROUTINE refill_obj !! ERROR : label_field(startX,startY) .le. 0 or occupied'
endif

totarea = 0.
field_mean(:) = 0.
field_min(:) = +9e10
field_max(:) = -9e10
COMx = 0.
COMy = 0.
delete_cell = .FALSE.
xfirst = startX
xlast = startX
yfirst = startY
ylast = startY

stackX(1)=startX
stackY(1)=startY
stack_num = 1
do while( stack_num .GT. 0)
  locx = stackX(stack_num)
  locy = stackY(stack_num)
  iox = MODULO(locx-1+domainsize_x,domainsize_x)+1
  ioy = MODULO(locy-1+domainsize_y,domainsize_y)+1
  stack_num = stack_num - 1

  if (input_field(iox,ioy,1).lt.threshold) cycle

  ! start to calculate properties

  ! create the size of a gridbox
  IF (llonlatgrid) THEN
    ! area in km^2
    gridboxarea = lon_inc*lat_inc*unit_area*COS((lat_first+ioy*lat_inc)*deg2rad)
  ELSE
    gridboxarea = unit_area
  ENDIF

  occupied(iox,ioy) = .True.
  label_field(iox,ioy) = nowid
  totarea = totarea + gridboxarea
  COMx = COMx + locx*input_field(iox,ioy,1)*gridboxarea
  COMy = COMy + locy*input_field(iox,ioy,1)*gridboxarea

  xfirst = MIN(locx,xfirst)
  xlast  = MAX(locx,xlast)
  yfirst = MIN(locy,yfirst)
  ylast  = MAX(locy,ylast)

  DO fieldid=1,n_fields+1
    field_mean(fieldid) = field_mean(fieldid)  + input_field(iox,ioy,fieldid)*gridboxarea
    field_min(fieldid)  = MIN(field_min(fieldid),input_field(iox,ioy,fieldid))
    field_max(fieldid)  = MAX(field_max(fieldid),input_field(iox,ioy,fieldid))
  ENDDO

  ! check next grid
  do imove=1,nmove
    locx2 = locx + moveX(imove)
    locy2 = locy + moveY(imove)
    iox = MODULO(locx2-1+domainsize_x,domainsize_x)+1
    ioy = MODULO(locy2-1+domainsize_y,domainsize_y)+1

    ! check touch x boundery
    if((.not. lperiodic_x) .and.&
       (locx2>domainsize_x .or. locx2<1)) THEN
       delete_cell=.True.
       cycle
    ENDIF

    ! check touch y boundary
    if((.not. lperiodic_y) .and.&
       (locy2>domainsize_y .or. locy2<1)) THEN
      delete_cell=.True.
      cycle
    ENDIF

    if(iox<=0 .or. ioy<=0 .or. ioy>domainsize_y .or. iox>domainsize_x)then
      print*, 'MODULO(',locx2,'-1+',domainsize_x,',',domainsize_x,')+1 = ',iox
      print*, 'MODULO(',locy2,'-1+',domainsize_y,',',domainsize_y,')+1 = ',ioy
      print*, locx, locx2, iox
      print*, locy, locy2, ioy
    endif
    ! check touch miss
    if(input_field(iox,ioy,1) .le.miss)THEN
      delete_cell=.True.
      cycle
    ENDIF

    if (occupied(iox,ioy)) cycle

    occupied(iox,ioy) = .True.
    stackX(stack_num + 1) = locx2
    stackY(stack_num + 1) = locy2
    stack_num = stack_num + 1
  enddo !imove
enddo   ! stack_num

xfirst = MODULO(xfirst-1+domainsize_x,domainsize_x)+1
xlast  = MODULO(xlast -1+domainsize_x,domainsize_x)+1

yfirst = MODULO(yfirst-1+domainsize_y,domainsize_y)+1
ylast  = MODULO(ylast -1+domainsize_y,domainsize_y)+1

COMx   = MODULO(COMx/field_mean(1)  -1+real(domainsize_x),real(domainsize_x))+1.
COMy   = MODULO(COMy/field_mean(1)  -1+real(domainsize_y),real(domainsize_y))+1.
field_mean(:) = field_mean(:) / totarea


ENDSUBROUTINE four_connect

!++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


RECURSIVE SUBROUTINE area(ii,ij,input_field, &
                  occupied,nevent,event_number,totarea,field_mean,field_min,field_max, &
		  COMx,COMy,delete_cell,xfirst,xlast,yfirst,ylast,checkcounter)

  USE irt_parameters, ONLY: n_fields, threshold, miss, llonlatgrid, &
                            unit_area, lat_first, lat_inc, lon_inc, &
                            lperiodic_x, lperiodic_y, domainsize_x, domainsize_y

  IMPLICIT NONE

  INTEGER, INTENT(IN)	 :: ii, ij
  !REAL, INTENT(IN)	 :: miss
  !INTEGER, INTENT(IN)	 :: n_fields
  REAL, INTENT(IN)       :: input_field(domainsize_x,domainsize_y,n_fields+1)
  INTEGER,INTENT(INOUT)  :: event_number(domainsize_x,domainsize_y)
  LOGICAL, INTENT(INOUT) :: occupied(domainsize_x,domainsize_y)
  INTEGER, INTENT(INOUT) :: nevent
  REAL, INTENT(INOUT)    :: field_mean(n_fields+1),field_min(n_fields+1),field_max(n_fields+1)
  REAL, INTENT(INOUT)    :: totarea
  REAL, INTENT(INOUT)	 :: COMx,COMy
  INTEGER, INTENT(INOUT) :: xfirst,xlast,yfirst,ylast
  INTEGER		 :: i, ii_mod, ij_mod,fieldid
  INTEGER		 :: icell(4), jcell(4)
  !REAL, INTENT(IN)       :: threshold
  LOGICAL, INTENT(INOUT) :: delete_cell
  INTEGER, INTENT(INOUT) :: checkcounter

  REAL, PARAMETER        :: deg2rad = 3.141592654/180.
  REAL                   :: gridboxarea
  
  checkcounter = checkcounter+1
  print*, 'checkcounter =',checkcounter
  ii_mod = ii
  ij_mod = ij
  if(lperiodic_x) ii_mod = MOD(ii-1+domainsize_x,domainsize_x)+1
  if(lperiodic_y) ij_mod = MOD(ij-1+domainsize_y,domainsize_y)+1
  if(ii_mod<=0 .or. ii_mod>domainsize_x .or. &
     ij_mod<=0 .or. ij_mod>domainsize_y ) then
    delete_cell = .TRUE.
    RETURN
  endif
  if(ij_mod<=0)then
    print*,'Y:',ij_mod,ij,domainsize_y
    print*,'X:',ii_mod,ii,domainsize_x
  endif

  icell = (/ ii_mod+1, ii_mod  , ii_mod-1, ii_mod  /)
  jcell = (/ ij_mod  , ij_mod+1, ij_mod  , ij_mod-1 /)

  print*, 'FLAG: checkout (ii_mod,ij_mod)=',ii_mod,ij_mod 
  IF (.NOT. occupied(ii_mod,ij_mod)) THEN
     ! take care for periodic boundary conditions:
     IF (ii_mod .LT. xfirst) xfirst = ii_mod
     IF (ii_mod .GT. xlast)  xlast  = ii_mod
     IF (ij_mod .LT. yfirst) yfirst = ij_mod
     IF (ij_mod .GT. ylast)  ylast  = ij_mod
     occupied(ii_mod,ij_mod) = .TRUE.

     !print*, '..... start_to calcualte variables'
     IF (input_field(ii_mod,ij_mod,1) .GE. threshold) THEN
        ! center of mass is now weighted by intensity!!!
        IF (llonlatgrid) THEN
          ! area in km^2
          gridboxarea = lon_inc*lat_inc*unit_area*COS((lat_first+ij_mod*lat_inc)*deg2rad)
        ELSE
          gridboxarea = unit_area
        ENDIF
        COMx = COMx + ii*input_field(ii_mod,ij_mod,1)*gridboxarea
        COMy = COMy + ij*input_field(ii_mod,ij_mod,1)*gridboxarea
        event_number(ii_mod,ij_mod) = nevent
        !IF (gridboxarea .LT. 0.5) WRITE (*,*) "gridboxarea=",gridboxarea
        DO fieldid=1,n_fields+1
          field_mean(fieldid) = field_mean(fieldid) + input_field(ii_mod,ij_mod,fieldid)*gridboxarea
          field_min(fieldid)  = MIN(field_min(fieldid),input_field(ii_mod,ij_mod,fieldid))
          field_max(fieldid)  = MAX(field_max(fieldid),input_field(ii_mod,ij_mod,fieldid))
        ENDDO
        totarea = totarea + gridboxarea
        DO i=1,4
           CALL area(icell(i),jcell(i),input_field,&
                     occupied,nevent,event_number,totarea,field_mean,field_min,field_max, &
                     COMx,COMy,delete_cell,xfirst,xlast,yfirst,ylast,checkcounter)
        ENDDO
     ELSEIF (input_field(ii_mod,ij_mod,1) .LE. miss) THEN
        ! if cell touches missing value, this cell will be deleted
        print*, "I thinks this messange should not raise !!! If you see, the irt_objects_release.f90 need to be examine QQ!"
        delete_cell = .TRUE.
     ENDIF
  ENDIF

  RETURN

END SUBROUTINE area

!++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

RECURSIVE SUBROUTINE overlay_area(miss, ii,ij,domsize_x,domsize_y,input_field,occupied,nevent, &
                                  event_number,delete_cell,xfirst,xlast,yfirst,ylast)
  IMPLICIT NONE
  INTEGER, INTENT(IN)	 :: ii, ij
  INTEGER, INTENT(IN)	 :: domsize_x,domsize_y
  REAL, INTENT(IN)	 :: miss
  REAL, INTENT(IN)       :: input_field(domsize_x,domsize_y)
  INTEGER,INTENT(INOUT)  :: event_number(domsize_x,domsize_y)
  LOGICAL, INTENT(INOUT) :: occupied(domsize_x,domsize_y)
  INTEGER, INTENT(INOUT) :: nevent
  INTEGER, INTENT(INOUT) :: xfirst,xlast,yfirst,ylast
  INTEGER		 :: i, ii_mod, ij_mod
  INTEGER		 :: icell(4), jcell(4)
  LOGICAL, INTENT(INOUT) :: delete_cell
  
  ! Indices for all 4 flow directions
  icell = (/ ii+1, ii  , ii-1, ii  /)
  jcell = (/ ij  , ij+1, ij  , ij-1 /)
  
  ii_mod = MOD(ii-1+domsize_x,domsize_x)+1
  ij_mod = MOD(ij-1+domsize_y,domsize_y)+1
  
  IF (.NOT. occupied(ii_mod,ij_mod)) THEN
     ! take care for periodic boundary conditions:
     IF (ii .LT. xfirst) xfirst=ii
     IF (ii .GT. xlast) xlast=ii
     IF (ij .LT. yfirst) yfirst=ij
     IF (ij .GT. ylast) ylast=ij
     occupied(ii_mod,ij_mod) = .TRUE.
     IF (input_field(ii_mod,ij_mod) .GE. 0.5) THEN
	! center of mass is now weighted by intensity!!!
        event_number(ii_mod,ij_mod) = nevent
	DO i=1,4
           CALL overlay_area(miss, icell(i),jcell(i),domsize_x,domsize_y,input_field,occupied,nevent, &
	             event_number,delete_cell,xfirst,xlast,yfirst,ylast)
        ENDDO
     ! Bugfix! Do NOT delete boundary cells in the overlaid field!!!
     !ELSEIF (input_field(ii_mod,ij_mod) .LE. miss) THEN
     !   ! if cell touches missing value, this cell will be deleted
     !   delete_cell = .TRUE.
     ENDIF
  ENDIF

  RETURN

END SUBROUTINE overlay_area

!++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
! linear time interpolation of velocity field

SUBROUTINE time_interpolation(domsize_x,domsize_y,time_steps,nx_bins,ny_bins,nt_bins,lperiodic_x,lperiodic_y, &
                              coarse_vel_x,coarse_vel_y,ix,iy,it,vel_x,vel_y)

INTEGER, INTENT(IN)  :: domsize_x,domsize_y
INTEGER, INTENT(IN)  :: time_steps
INTEGER, INTENT(IN)  :: nx_bins
INTEGER, INTENT(IN)  :: ny_bins
INTEGER, INTENT(IN)  :: nt_bins
INTEGER, INTENT(IN)  :: ix,iy,it
LOGICAL, INTENT(IN)  :: lperiodic_x,lperiodic_y    ! periodic boundaries?

REAL, INTENT(IN)     :: coarse_vel_x(nx_bins,ny_bins,nt_bins)
REAL, INTENT(IN)     :: coarse_vel_y(nx_bins,ny_bins,nt_bins)

REAL, INTENT(OUT)    :: vel_x,vel_y

REAL                 :: vel_x_prev,vel_y_prev
REAL                 :: vel_x_next,vel_y_next
REAL                 :: weight
INTEGER              :: nt

nt = MIN(FLOOR((REAL(it-1)/REAL(time_steps))*nt_bins)+1,nt_bins)
weight = (REAL(it-1)/REAL(time_steps))*nt_bins
weight = weight-FLOOR(weight)

IF ((nt .EQ. 1 .AND. weight .LT. 0.5) .OR. (nt .EQ. nt_bins .AND. weight .GT. 0.5)) THEN
  CALL bilinear_interpolation(domsize_x,domsize_y,nx_bins,ny_bins,lperiodic_x,lperiodic_y,coarse_vel_x(:,:,nt),ix,iy,vel_x)
  CALL bilinear_interpolation(domsize_x,domsize_y,nx_bins,ny_bins,lperiodic_x,lperiodic_y,coarse_vel_y(:,:,nt),ix,iy,vel_y)
ELSEIF (weight .LT. 0.5) THEN
  CALL bilinear_interpolation(domsize_x,domsize_y,nx_bins,ny_bins,lperiodic_x,lperiodic_y,coarse_vel_x(:,:,nt-1),ix,iy,vel_x_prev)
  CALL bilinear_interpolation(domsize_x,domsize_y,nx_bins,ny_bins,lperiodic_x,lperiodic_y,coarse_vel_y(:,:,nt-1),ix,iy,vel_y_prev)
  CALL bilinear_interpolation(domsize_x,domsize_y,nx_bins,ny_bins,lperiodic_x,lperiodic_y,coarse_vel_x(:,:,nt),ix,iy,vel_x_next)
  CALL bilinear_interpolation(domsize_x,domsize_y,nx_bins,ny_bins,lperiodic_x,lperiodic_y,coarse_vel_y(:,:,nt),ix,iy,vel_y_next)
  vel_x = (0.5-weight)*vel_x_prev + (weight+0.5)*vel_x_next
  vel_y = (0.5-weight)*vel_y_prev + (weight+0.5)*vel_y_next
ELSE
  CALL bilinear_interpolation(domsize_x,domsize_y,nx_bins,ny_bins,lperiodic_x,lperiodic_y,coarse_vel_x(:,:,nt),ix,iy,vel_x_prev)
  CALL bilinear_interpolation(domsize_x,domsize_y,nx_bins,ny_bins,lperiodic_x,lperiodic_y,coarse_vel_y(:,:,nt),ix,iy,vel_y_prev)
  CALL bilinear_interpolation(domsize_x,domsize_y,nx_bins,ny_bins,lperiodic_x,lperiodic_y,coarse_vel_x(:,:,nt-1),ix,iy,vel_x_next)
  CALL bilinear_interpolation(domsize_x,domsize_y,nx_bins,ny_bins,lperiodic_x,lperiodic_y,coarse_vel_y(:,:,nt-1),ix,iy,vel_y_next)
  vel_x = (1.5-weight)*vel_x_prev + (weight-0.5)*vel_x_next
  vel_y = (1.5-weight)*vel_y_prev + (weight-0.5)*vel_y_next
ENDIF

END SUBROUTINE time_interpolation


!++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
! bilinear spatial interpolation of coarse velocity field

SUBROUTINE bilinear_interpolation(domsize_x,domsize_y,nx_bins,ny_bins,lperiodic_x,lperiodic_y,coarse_field,ix,iy,out_value)

IMPLICIT NONE

INTEGER, INTENT(IN)  :: domsize_x,domsize_y
INTEGER, INTENT(IN)  :: nx_bins
INTEGER, INTENT(IN)  :: ny_bins
INTEGER, INTENT(IN)  :: ix,iy
LOGICAL, INTENT(IN)  :: lperiodic_x,lperiodic_y    ! periodic boundaries?

REAL, INTENT(IN)     :: coarse_field(nx_bins,ny_bins)

REAL, INTENT(OUT)    :: out_value

REAL                 :: halfbin_x,halfbin_y
REAL                 :: weight_x, weight_y
INTEGER              :: nx,ny
INTEGER              :: nx_west, nx_east, ny_south, ny_north

halfbin_x = NINT(REAL(domsize_x)/REAL(nx_bins)/2.)
halfbin_y = NINT(REAL(domsize_y)/REAL(ny_bins)/2.)

nx = FLOOR((REAL(ix+halfbin_x)/REAL(domsize_x))*nx_bins)
weight_x = (REAL(ix+halfbin_x)/REAL(domsize_x))*nx_bins
weight_x = weight_x-FLOOR(weight_x)

ny = FLOOR((REAL(iy+halfbin_y)/REAL(domsize_y))*ny_bins)
weight_y = (REAL(iy+halfbin_y)/REAL(domsize_y))*ny_bins
weight_y = weight_y-FLOOR(weight_y)

!catch
IF (nx<0 .OR. nx>nx_bins .OR. ny<0 .OR. ny>ny_bins) THEN
  WRITE (*,*) "ERROR in bilinear_interpolation: indices out of range."
  STOP
ENDIF

IF (lperiodic_x) THEN ! periodic boundaries

  IF (nx==0) THEN
    nx_west = nx_bins
    nx_east = nx+1
  ELSEIF (nx==nx_bins) THEN
    nx_west = nx
    nx_east = 1
  ELSE
    nx_west = nx
    nx_east = nx+1
  ENDIF

ELSE

  IF (nx==0) THEN
    nx_west = nx+1
    nx_east = nx+1
  ELSEIF (nx==nx_bins) THEN
    nx_west = nx
    nx_east = nx
  ELSE
    nx_west = nx
    nx_east = nx+1
  ENDIF

ENDIF

IF (lperiodic_y) THEN ! periodic boundaries

  IF (ny==0) THEN
    ny_south = ny_bins
    ny_north = ny+1
  ELSEIF (ny==ny_bins) THEN
    ny_south = ny
    ny_north = 1
  ELSE
    ny_south = ny
    ny_north = ny+1
  ENDIF

ELSE

  IF (ny==0) THEN
    ny_south = ny+1
    ny_north = ny+1
  ELSEIF (ny==ny_bins) THEN
    ny_south = ny
    ny_north = ny
  ELSE
    ny_south = ny
    ny_north = ny+1
  ENDIF

ENDIF

out_value = coarse_field(nx_west,ny_south)*(1.-weight_x)*(1.-weight_y) + &
            coarse_field(nx_west,ny_north)*(1.-weight_x)*weight_y + &
            coarse_field(nx_east,ny_south)*weight_x*(1.-weight_y) + &
            coarse_field(nx_east,ny_north)*weight_x*weight_y

END SUBROUTINE
