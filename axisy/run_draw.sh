#!/usr/bin/bash

source ~/.bashrc
conda activate py311

py='draw_hov_inflow_f00.py'
py='draw_hov_inflow.py'
#py='draw_tang_wind.py'

#for i in $(seq 18 -1 1);do
for i in 1 2 8 13 18 0;do
  echo ${i}
  python -u ${py} ${i}
  #mpiexec -n 20 python -u ${py} ${i}
done
#python -u ${py} 0
