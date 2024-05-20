from moviepy.editor import VideoFileClip, ImageSequenceClip, concatenate_videoclips, clips_array
from moviepy.video.fx.all import crop
import sys, os
sys.path.insert(1,'../')
import config
import glob

def get_ImageSeq(fname, fps=12):
    flist=glob.glob(fname)
    flist.sort()
    return ImageSequenceClip(flist, fps=fps)

iexp=0
#iexp = int(sys.argv[1])

fdir='./combine_small/'
os.system(f'mkdir -p {fdir}')
#for iexp in range(len(config.expList)):
for iexp in [14, 15, 16, 17]:
#for iexp in [-1]:
  exp=config.expList[iexp]
  print(exp)

  vid = []

  dum0 = get_ImageSeq(f'./fig_olr_rain/{exp}/bla_olrrain_*.png')
  dum1 = get_ImageSeq(f'./fig_czeta_50km/{exp}/bla_cwvczeta_*.png')
  dum2 = get_ImageSeq(f'../ani_zeta/fig_zeta/{exp}/bla_11_zeta_*.png')
  #dum2 = get_ImageSeq(f'../compare_conv_hmsf/fig/{exp}/bla_vort_*.png')
  vid = [dum0, dum1, dum2]

  (w, h) = vid[0].size
  x1, x2 = w*0.125, w*0.875
  y1, y2 = 0, h
  for i in range(len(vid)):
    vid[i] = crop(vid[i], x1=x1, y1=y1, x2=x2, y2=y2)
  
  # Concat them
  #final = concatenate_videoclips(vid)
  final_clip = clips_array([vid])

  # Write output to the file
  final_clip.write_videofile(f"{fdir}/alls_{exp}.mp4", codec='libx264', \
                        threads=10, ffmpeg_params=['-pix_fmt','yuv420p'])

