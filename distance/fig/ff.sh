

## export ofram=60
## for exp in RRCE_3km_f00  RRCE_3km_f10  RRCE_3km_f15  RRCE_3km_f20;do
##   echo ${exp}
##   nohup /home/C.shaoyu/ffmglob.sh "./${exp}/bla*.png" ./${exp}.mp4 &
## done
## 
## export ofram=20
## for exp in RCE_300K_3km_f0 RCE_300K_3km_f05;do
##   echo ${exp}
##   nohup /home/C.shaoyu/ffmglob.sh "./${exp}/bla*.png" ./${exp}.mp4 &
## done
## wait

for file in $(ls R*.mp4);do
  echo ${file}
  nohup ffmpeg -i ${file} -vf reverse rev_${file} &
done
wait
