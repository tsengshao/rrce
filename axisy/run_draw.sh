#!/usr/bin/bash

source ~/.bashrc
conda activate py311

py='draw_hov_inflow.py'

for i in $(seq 18 -1 1);do
  echo ${i}
  python -u ${py} ${i}
done
python -u ${py} 0
