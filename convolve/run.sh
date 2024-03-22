#!/bin/bash



for i in $(seq 7 9);do
echo ${i}
mpirun -np 30 python -u cal_convolve.py ${i}
done
