from moviepy.editor import VideoFileClip, ImageSequenceClip, concatenate_videoclips, clips_array
from moviepy.video.fx.all import crop
import sys, os
sys.path.insert(1,'../')
import config
import glob

iexp=0
#iexp = int(sys.argv[1])

os.system(f'mkdir -p ./combine')
#for iexp in range(len(config.expList)):
for iexp in [14,15,16,17]:
  exp=config.expList[iexp]
  print(exp)

  vid = []
  for idxz in [11, 20, 33]:
    # read 
    flist=glob.glob(f'./fig_zeta/{exp}/bla_{idxz}_zeta_*.png')
    flist.sort()
    vid.append(ImageSequenceClip(flist, fps=12))

  (w, h) = vid[0].size
  x1, x2 = w*0.125, w*0.875
  y1, y2 = 0, h
  for i in range(len(vid)):
    vid[i] = crop(vid[i], x1=x1, y1=y1, x2=x2, y2=y2)
  
  # Concat them
  #final = concatenate_videoclips(vid)
  final_clip = clips_array([vid])

  # Write output to the file
  final_clip.write_videofile(f"./combine/zeta_{exp}.mp4", codec='libx264', \
                        threads=10, ffmpeg_params=['-pix_fmt','yuv420p'])

