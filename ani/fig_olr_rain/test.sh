#!/bin/bash

mkdir fig
for dir in $(ls -d ./RRCE_3km_f00*);do
  for it in 2 217;do
  itt=$(printf "%06d" ${it})
  file=$(ls ${dir}/*${itt}.png)

  exp=$(echo ${dir}|cut -d/ -f2)
  echo ${file} "./fig/${exp}_${itt}.png"
  cp ${file} ./fig/${exp}_${itt}.png

  done
done

