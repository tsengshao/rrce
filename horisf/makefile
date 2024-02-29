# compiler
FC = mpiifort 
DEBUG = -g -traceback 
FCFLAGS = -O3 -r8 -free -mcmodel=large -heap-arrays 10 -shared-intel $(DEBUG)
FINCLUDE = -I/opt/libs-intel-oneapi/pnetcdf-1.12.2/include -I/opt/libs-intel-oneapi/netcdf-4.7.4/include -I/opt/libs-intel-oneapi/petsc-3.14.0/include
LDLIBS = -L/opt/libs-intel-oneapi/pnetcdf-1.12.2/lib -lpnetcdf -L/opt/libs-intel-oneapi/netcdf-4.7.4/lib -lnetcdff -lnetcdf -L/opt/libs-intel-oneapi/petsc-3.14.0/lib -lpetsc -qmkl

# code paths
VPATH = src

# objects
LIST = test.F petsc_vvm_solver.F 
LIST_o = $(LIST:.F=.o)
target = test.exe

test.exe: test.o petsc_vvm_solver.o
test.o: petsc_vvm_solver.o test.F
petsc_vvm_solver.o: petsc_vvm_solver.F

all: $(target)

$(LIST_o): %.o: %.F
	$(FC) $(FCFLAGS) $(FINCLUDE) -c $<

$(target) : $(LIST_o)
	$(FC) $(FCFLAGS) $(FINCLUDE) $^ -o $@ $(LDLIBS)

clean:
	rm -rf *.o *.mod test.exe
