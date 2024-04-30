! needs the sorted output and the objects mask file as input
! generate sorted output with:
! > sort -n -k2 irt_tracks_nohead_output.txt > irt_tracks_sorted.txt
! writes out a mask file with track id's
! Compile: ifort -no-wrap-margin -o irt_trackmask_release.x irt_trackmask_release.f90

PROGRAM irt_trackmask

USE irt_parameters, ONLY: domainsize_x, domainsize_y, max_no_of_tracks, time_steps

IMPLICIT NONE
INTEGER              :: ii, ij, it, n,ncell, lrec
INTEGER              :: time_step, time_step_event
INTEGER              :: track_id(max_no_of_tracks)
INTEGER              :: cell_id(max_no_of_tracks)
INTEGER              :: cell_age1(max_no_of_tracks)
INTEGER              :: cell_age2(max_no_of_tracks)
INTEGER              :: status_beginning(max_no_of_tracks)
INTEGER              :: status_end(max_no_of_tracks)
INTEGER              :: track_length(max_no_of_tracks)
INTEGER              :: cell_timestep(max_no_of_tracks)
REAL                 :: in_field(domainsize_x,domainsize_y)
REAL                 :: out_field(domainsize_x,domainsize_y)
INTEGER              :: readline(9), ind

CHARACTER (len=90), PARAMETER   :: input_filename1 = "irt_objects_mask.dat"
CHARACTER (len=90), PARAMETER   :: input_filename2 = "irt_tracks_sorted.txt"
CHARACTER (len=90), PARAMETER   :: output_filename = "irt_tracks_mask.dat"

INQUIRE(IOLENGTH=lrec) in_field
OPEN(10,FILE=trim(input_filename1),FORM='unformatted', ACTION='read',access='direct',recl=lrec)
OPEN(20,FILE=trim(input_filename2),FORM='formatted', ACTION='read')
OPEN(30,FILE=trim(output_filename),FORM='unformatted',ACTION='write',access='direct',recl=lrec)

! read the first line in sorted
READ(20,*) readline(1:9)

DO it=1, time_steps-1
print*, 'timestep: ',it
READ(10,rec=it) in_field(:,:)


! reset and create the ID1 table for all variables, 
! and the last readline is the first rows in the next timestep
DO
  IF(readline(2)>it) EXIT
  ind = readline(5)
  track_id(ind) = readline(1)
  time_step_event = readline(2)
  cell_age1(ind) = readline(3)
  cell_age2(ind) = readline(4)
  cell_id(ind)   = readline(5)
  status_beginning(ind) = readline(6)
  status_end(ind)       = readline(7)
  track_length(ind)     = readline(8)
  cell_timestep(ind)    = readline(9)
  READ(20,*,END=999) readline(1:9)
ENDDO !! readline
999 CONTINUE

!! remap the data to the out field
out_field = 0.
DO ij=1,domainsize_y
  DO ii=1,domainsize_x
    IF(in_field(ii,ij) .GT. 0.) THEN
      out_field(ii,ij) = track_id(NINT(in_field(ii,ij)))
    ELSE IF (in_field(ii,ij) .LT. 0) THEN
      out_field(ii,ij) = -1.
    ENDIF
  ENDDO !! ii
ENDDO !! ij

!! write trackmask
WRITE(30,rec=it) out_field(:,:)

!! create new table for the next timestep
track_id(:) = -2
cell_age1(:) = -2
cell_age2(:) = -2
status_beginning(:) = -2
status_end(:)       = -2
track_length(:)     = -2
cell_timestep(:)    = -2

ind = readline(5)
track_id(ind) = readline(1)
time_step_event = readline(2)
cell_age1(ind) = readline(3)
cell_age2(ind) = readline(4)
cell_id(ind)   = readline(5)
status_beginning(ind) = readline(6)
status_end(ind)       = readline(7)
track_length(ind)     = readline(8)
cell_timestep(ind)    = readline(9)

ENDDO  !! it


CLOSE(10)
CLOSE(20)
CLOSE(30)

ENDPROGRAM irt_trackmask
