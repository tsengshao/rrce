MODULE irt_parameters
! grid information
INTEGER, PARAMETER    :: domainsize_x = 2576
INTEGER, PARAMETER    :: domainsize_y = 1280

LOGICAL, PARAMETER    :: llonlatgrid = .TRUE.
REAL, PARAMETER       :: unit_area = 10000. ! in 1degx1deg -> about 10000.km2
! only used if llonlatgrid=.TRUE., otherwise set to arbitrary value:
REAL, PARAMETER       :: lat_first = -89.929688
REAL, PARAMETER       :: lat_inc = 0.14062500
REAL, PARAMETER       :: lon_inc = 0.13975155

LOGICAL, PARAMETER    :: lperiodic_x = .TRUE. 
LOGICAL, PARAMETER    :: lperiodic_y = .FALSE.

INTEGER, PARAMETER    :: n_fields = 1   ! number of additional averaging

! bins of coarse velocity field
INTEGER, PARAMETER    :: time_steps = 912    ! total number of timesteps
INTEGER, PARAMETER    :: nt_bins = 24         ! 24 hours
INTEGER, PARAMETER    :: nx_bins = 10
INTEGER, PARAMETER    :: ny_bins = 10

REAL, PARAMETER       :: threshold = 1          ! for intensity
REAL, PARAMETER       :: minimum_size = 1.       ! events smaller than that will be sorted out, unit is following unit_area(in this example, the unit is km2)

REAL, PARAMETER       :: termination_sensitivity=1.     ! Choose value between 0.0 and 1.0

REAL, PARAMETER       :: max_velocity = 10.   ! adjust acordingly
                                              ! velocities>max_velocity will be ignored to remove outliers
! define a minimal number of cells required for a coarse grained coordinate to be evaluated 
! if there are less, missing value will be assigned to that coarse cell
INTEGER, PARAMETER    :: min_cells = 10

INTEGER, PARAMETER    :: max_no_of_cells=500000  ! buffer size, increase if necessary
INTEGER, PARAMETER    :: max_no_of_tracks=100000    ! buffer size, increase if necessary
INTEGER, PARAMETER    :: max_length_of_track=1500  ! buffer size, increase if necessary

REAL, PARAMETER       :: miss=-999000000.0+1           ! value<miss ==> missing_value

END MODULE irt_parameters
