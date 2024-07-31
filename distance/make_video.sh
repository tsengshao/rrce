#!/usr/bin/bash

source ~/.bashrc

conda activate py311
mkdir mp4_axisym

for kind in fig_axisym/sf_largest_0 ;do
  
  for dir in $(ls "./${kind}/");do
    echo ${dir}
    fname=${dir}
    ~/ffmglob.sh "./${kind}/${dir}/bla*.png" ./mp4_axisym/${fname}.mp4
  done
  
done
