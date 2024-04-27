from moviepy.editor import VideoFileClip, concatenate_videoclips, clips_array
from moviepy.video.fx.all import crop
import sys, os
sys.path.insert(1,'../')
import config

iexp=0
iexp = int(sys.argv[1])
exp=config.expList[iexp]
figlist = [f'fig_czeta_25km', 'fig_czeta_50km', 'fig_czeta_100km']
outpath='./combine/'
os.system(f'mkdir -p {outpath}')

# Read files
vid = []
for i in range(len(figlist)):
  vid.append(VideoFileClip(f'./{figlist[i]}/{exp}.mp4'))
(w, h) = vid[0].size
x1, x2 = w*0.125, w*0.875
y1, y2 = 0, h
for i in range(len(figlist)):
  vid[i] = crop(vid[i], x1=x1, y1=y1, x2=x2, y2=y2)

# Concat them
#final = concatenate_videoclips(vid)
final_clip = clips_array([vid])

# Write output to the file
final_clip.write_videofile(f"{outpath}/conv_{exp}.mp4", codec='libx264', \
                      threads=10, ffmpeg_params=['-pix_fmt','yuv420p'])

