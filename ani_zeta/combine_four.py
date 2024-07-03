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

fdir='./combine_four/'
os.system(f'mkdir -p {fdir}')
source_folder = 'fig_olr_rain'
source_file   = 'bla_olrrain'

## source_folder = 'fig_czeta_50km'
## source_file   = 'bla_cwvczeta'

source_folder = 'fig_zeta'
source_file   = 'bla_11_zeta'

vid = []
#print('dum0')
#dum0 =  get_ImageSeq(f'./{source_folder}/{config.expList[2]}/{source_file}_*.png')
print('dum1')
dum1 =  get_ImageSeq(f'./{source_folder}/{config.expList[3]}/{source_file}_*.png')
print('dum2')
dum2 = get_ImageSeq(f'./{source_folder}/{config.expList[8]}/{source_file}_*.png')
print('dum3')
dum3 = get_ImageSeq(f'./{source_folder}/{config.expList[13]}/{source_file}_*.png')

vid = [dum1, dum2, dum3]

(w, h) = vid[0].size
x1, x2 = w*0.125, w*0.875
y1, y2 = 0, h
for i in range(len(vid)):
  vid[i] = crop(vid[i], x1=x1, y1=y1, x2=x2, y2=y2)

# Concat them
#final = concatenate_videoclips(vid)
final_clip = clips_array([vid])

# Write output to the file
final_clip.write_videofile(f"{fdir}/four_{source_file}.mp4", codec='libx264', \
                      threads=10, ffmpeg_params=['-pix_fmt','yuv420p'])

