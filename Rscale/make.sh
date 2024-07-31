#!/usr/bin/bash

source ~/.bashrc

conda activate py311
vname="u_tang"
vname="ws"
mkdir mp4_${vname}

for kind in "fig/sf_largest_0" ;do
  for dir in $(ls "./${kind}/");do
    if [ "${dir}" != "RRCE_3km_f00_30" ];then continue; fi
    echo ${dir}
    fname=${dir}
    export ofram=9
    echo ${ofram}
    ~/ffmglob.sh "./${kind}/${dir}/${vname}*.png" ./mp4_${vname}/${fname}.mp4
  done
done
