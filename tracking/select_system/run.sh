#!/bin/bash

NPATH=`pwd`
datafolder=../tracking_data
mkdir -p ${datafolder}

# create ctl
cp ./irt_tracks_mask_select_example.ctl ./irt_tracks_mask_select.ctl
tmp=$(cat ../tracking_data/irt_tracks_mask.ctl |grep tdef)
i=0
echo ${tmp}
for ddmmyyyy in ${tmp};do
  i=$((${i}+1))
  if [ "${i}" -eq "4" ];then
    break
  fi
done
echo ${ddmmyyyy}

sed -i "s/OOXXTIMEXXOO/${ddmmyyyy}/" ./irt_tracks_mask_select.ctl
mv ./irt_tracks_mask_select.ctl ${datafolder}

# copy select code ( remind the selected condiction )
cp ./select_system.f90 ${datafolder}

echo ${exp}
ln -sf ../tracking_data/irt_tracklinks_output.txt .
ln -sf ../tracking_data/irt_tracks_mask.dat .
ln -sf ../tracking_code/irt_parameters.f90 .

./compile.sh
./select_system.x

mv ./irt_tracklinks_output_select.txt ${datafolder}
mv ./irt_tracks_mask_select.dat ${datafolder}
mv ./select_tracks_output.csv ${datafolder}
mv select_tracks_info.txt ${datafolder}

rm -f irt_parameters.f90 irt_parameters.mod irt_tracklinks_output.txt irt_tracks_mask.dat
  






