"""
This example is follow
https://research.computing.yale.edu/sites/default/files/files/mpi4py.pdf
"""

import numpy as np
from mpi4py import MPI

def rbind(comm, x):
  return np.vstack(comm.allgather(x))

def rbind2(comm, x):
  size = comm.Get_size()
  m = np.zeros((size, len(x)), dtype=int)
  comm.Allgather([x, MPI.INT], [m, MPI.INT])
  return m

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
x = np.arange(4, dtype=int) * rank
a = rbind(comm, x)
a2 = rbind(comm, x)

if rank==0:
  print(rank, a.shape, a, sep='\n')
  print('...')
  print(rank, a2.shape, a, sep='\n')
