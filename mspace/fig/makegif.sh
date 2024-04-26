
conda activate py311
for exp in RRCE_3km_f00_25 RRCE_3km_f00 RRCE_3km_f00_10 RRCE_3km_f00_20 RRCE_3km_f00_30;do
  ffmpeg -framerate 2 -pattern_type glob -i "./${exp}/mspace_0*.png" ${exp}.gif
done
