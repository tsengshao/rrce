#!/usr/bin/bash

source ~/.bashrc

conda activate py311

for kind in fig_czeta_100km fig_czeta_50km fig_czeta_25km fig_olr_rain;do
cd ${kind}
  
  for dir in $(find R* -type d);do
    echo ${dir}
    if [ -f ${dir}.mp4 ]; then continue; fi
    ~/ffmglob.sh "./${dir}/bla*.png" ./${dir}.mp4
  done
  
cd ..
done
