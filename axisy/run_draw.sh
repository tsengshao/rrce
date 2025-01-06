#!/usr/bin/bash

source ~/.bashrc
conda activate py311

py='draw_hov_inflow_f00.py'
py='draw_hov_inflow.py'
# py='draw_tang_wind_one.py'
# py='draw_radi_wind_one.py'
py='draw_mse.py'

# python -u ${py} 0
# exit

for i in $(seq 18 -1 0);do
#for i in 1 2 8 13 18;do
  echo ${i}
  python -u ${1} ${i}
  #mpiexec -n 20 python -u ${py} ${i}
done
