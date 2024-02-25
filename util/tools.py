
def get_mpi_time_span(start_t, end_t, cpuid, nproc):
  # time MPI(time span start_t~end_t-1)
  nt = end_t - start_t
  i = nt//nproc
  j = nt%nproc
  spoint = cpuid*i+start_t
  count = i
  if (cpuid<j):
    count+=1
    spoint+=cpuid
  else:
    spoint+=j
  epoint = spoint+count
  return spoint, epoint
  print(cpuid, spoint, epoint, count)
