PROGRAM irt_trackslink
USE irt_parameters, ONLY: n_fields

IMPLICIT NONE

INTEGER             :: j,m,n

integer            :: trackID,status_beginning,status_end,cell_timestep,&
                      ID1,ID2,age1,age2,xfirst,xlast,yfirst,ylast,&
                      lfl,slfl,lbl,slbl
real               :: area,field_mean,field_min,lsm_mean,lsm_min,lsm_max,&
                      field_max,center_of_mass_x,center_of_mass_y,&
                      velocity_x,velocity_y, field_mmm(3*(n_fields+1))
integer            :: first_timestep,track_length

INTEGER, PARAMETER :: buffer=100000000
integer            :: ID2toTrackID(buffer)
integer            :: TracksFBID2(buffer,4)

integer            :: parent_track1,parent_track2
integer            :: child_track1,child_track2


CHARACTER (len=90), PARAMETER   :: input_filename2 = "irt_tracks_output.txt"
CHARACTER (len=90), PARAMETER   :: output_filename = "irt_tracklinks_output.txt"

print*,size(field_mmm)
!!! create a ID2 to trackID table
OPEN(20,FILE=trim(input_filename2),FORM='formatted', ACTION='read')
do
read(20,*,end=999) ! #newline
read(20,*) trackID,first_timestep,track_length,&
                   status_beginning,status_end
do j=1,track_length
  read(20,*) trackID,cell_timestep,&
             ID1,ID2,age1,age2,area,field_mmm,&
             xfirst,xlast,yfirst,ylast,center_of_mass_x,center_of_mass_y,&
             velocity_x,velocity_y,lfl,slfl,lbl,slbl
  if(ID2>buffer) then
    stop "Please increase the 'buffer' in irt_tracllink_release_shao.f90"
  endif
  if(j==1) TracksFBID2(trackID,3:4)=(/lbl,slbl/)
  ID2toTrackID(ID2) = trackID
enddo !j,track_length
TracksFBID2(trackID,1:2)=(/lfl,slfl/) !record last tracks forward and backward

enddo !main loop
999 continue
close(20)

!!! read and output trackslink_output
OPEN(20,FILE=trim(input_filename2),FORM='formatted', ACTION='read')
OPEN(30,FILE=trim(output_filename),FORM='formatted', ACTION='write')
do
parent_track1=0
parent_track2=0
child_track1=0
child_track2=0
read(20,*,end=888) ! #newline
read(20,*) trackID,first_timestep,track_length,&
                   status_beginning,status_end

if(TracksFBID2(trackID,3).gt.0) parent_track1=ID2toTrackID(TracksFBID2(trackID,3)) !lbl
if(TracksFBID2(trackID,4).gt.0) parent_track2=ID2toTrackID(TracksFBID2(trackID,4)) !slbl
if(TracksFBID2(trackID,1).gt.0) child_track1=ID2toTrackID(TracksFBID2(trackID,1))  !lfl
if(TracksFBID2(trackID,2).gt.0) child_track2=ID2toTrackID(TracksFBID2(trackID,2))  !slfl

if(TracksFBID2(trackID,3).eq.-1) parent_track1 = -1 !lbl
if(TracksFBID2(trackID,4).eq.-1) parent_track2 = -1 !slbl
if(TracksFBID2(trackID,1).eq.-1) child_track1  = -1  !lfl
if(TracksFBID2(trackID,2).eq.-1) child_track2  = -1  !slfl

write(30,*) '*'
write(30,*) trackID,first_timestep,track_length,&
            status_beginning,status_end,&
            parent_track1,parent_track2,&
            child_track1,child_track2

if(status_beginning.eq.0 .and. parent_track1.ne.0) then
  print*, '!!! DEBUG ERROR!!!'
  print*, status_beginning, parent_track1
  print*, TracksFBID2(trackID,:)
  print*, child_track1,child_track2,parent_track1,parent_track2
  stop
endif
            

do j=1,track_length
  read(20,*) trackID,cell_timestep,&
             ID1,ID2,age1,age2,area,field_mmm,&
             xfirst,xlast,yfirst,ylast,center_of_mass_x,center_of_mass_y,&
             velocity_x,velocity_y,lfl,slfl,lbl,slbl
  write(30,*) trackID,cell_timestep,&
             ID1,ID2,age1,age2,area,field_mmm,&
             xfirst,xlast,yfirst,ylast,center_of_mass_x,center_of_mass_y,&
             velocity_x,velocity_y,lfl,slfl,lbl,slbl

enddo !j,track_length

enddo !main loop
888 continue
close(20)
close(30)



END PROGRAM irt_trackslink
