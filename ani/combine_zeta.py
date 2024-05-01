from moviepy.editor import VideoFileClip, concatenate_videoclips, clips_array
from moviepy.video.fx.all import crop
import sys, os
sys.path.insert(1,'../')
import config

iexp=0
iexp = int(sys.argv[1])
exp=config.expList[iexp]
srcPath='/data/C.shaoyu/rrce/src'
mp4list  = [f'{srcPath}/ani/fig_czeta_50km/{exp}.mp4',\
            f'{srcPath}/ani/fig_olr_rain/{exp}.mp4',\
            f'{srcPath}/compare_conv_hmsf/fig/{exp}.mp4']
outpath='./combine/'
os.system(f'mkdir -p {outpath}')

# Read files
vid = []
for i in range(len(mp4list)):
  vid.append(VideoFileClip(f'{mp4list[i]}'))
  #vid.append(VideoFileClip(f'{mp4list[i]}').subclip(5,6))

(w, h) = vid[0].size
x1, x2 = w*0.125, w*0.875
y1, y2 = 0, h
for i in range(len(mp4list)):
  if i==2:
    vid[i] = crop(vid[i], x1=w*0.125, y1=y1, x2=w*0.92, y2=y2)
  else:
    vid[i] = crop(vid[i], x1=x1, y1=y1, x2=x2, y2=y2)

# Concat them
#final = concatenate_videoclips(vid)
final_clip = clips_array([vid])

# Write output to the file
final_clip.write_videofile(f"{outpath}/all_{exp}.mp4", codec='libx264', \
                      threads=1, ffmpeg_params=['-pix_fmt','yuv420p'])

