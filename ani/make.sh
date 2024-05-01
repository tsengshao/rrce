#!/usr/bin/bash

source ~/.bashrc

conda activate py311

#for klen in 100km 50km 25km;do
#cd fig_czeta_${klen}

cd fig_czeta
for dir in $(find R* -type d);do
  echo ${dir}
  ~/ffmglob.sh "./${dir}/bla*.png" ./${dir}.mp4
done

#cd ..
#done
