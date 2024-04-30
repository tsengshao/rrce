#!/usr/bin/bash

source ~/.bashrc

conda activate py311
cd fig
#cd fig_czeta_100km
for dir in $(find R* -type d);do
  echo ${dir}
  ~/ffmglob.sh "./${dir}/bla*.png" ./${dir}.mp4
done
