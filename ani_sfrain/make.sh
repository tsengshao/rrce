#!/usr/bin/bash

source ~/.bashrc

conda activate py311
mkdir mp4

for kind in fig_sfrain ;do
  
  for dir in $(ls "./${kind}/");do
    echo ${dir}
    fname=${dir}
    ~/ffmglob.sh "./${kind}/${dir}/bla*.png" ./mp4/${fname}.mp4
  done
  
done
