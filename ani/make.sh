#!/usr/bin/bash

source ~/.bashrc

conda activate py311
cd fig_czeta
for dir in $(ls);do
  echo ${dir}
  ~/ffmglob.sh "./${dir}/bla*.png" ./${dir}.mp4
done
