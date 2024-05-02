'reinit'

vvmPath="/data/C.shaoyu/rrce/vvm/"
datPath="/data/C.shaoyu/rrce/data/"
outPath="./fig"
'! mkdir -p 'outPath

exp='RRCE_3km_f00'

'open 'datPath'mspace/'exp'.ctl'

nday = 5
dayList='10 15 20 25 30'
legList='10_days 15_days 20_days 25_days 30_days'
lcList='7 8 30 90 14'
'set rgb 30 255 85 33'
'set rgb 90 252 56 241'
'set lwid 55 5'

'set x 1 70'
'set xlabs 0|10|20|30|40|50|60|70'

'set parea 1.2 10.5 1 7.5'
'set xlopts 1 10 0.2'
'set ylopts 1 10 0.2'
'set grads off'
'set timelab off'
'set z 1'

i=1
while(i<=nday)
  day=subwrd(dayList,i)
  line = day2it(day)
  t0 = subwrd(line,1)
  t1 = subwrd(line,2)
  say 'day='day', t=('t0','t1')'
  'define dat=sum(nsample,t='t0',t='t1')'
  'define dat = dat / 384 / 384 / 't1-t0+1' * 100 ' 
  'set cmark 0'
  'set ccolor 'subwrd(lcList,i)
  'set cthick 55'
  'set vrange 0 14'
  'set ylint 2'
  'set gxout line'
  'd dat'
  i=i+1
endwhile

'set cthick 55'
'legend tr 'nday' 10 55 'legList' 'lcList''

*X Limits = 1.2 to 10.5
*Y Limits = 1 to 7.5

'set string 1 c 10'
'set strsiz 0.17'
'draw string 5.85 0.4 CWV [mm]'

'set string 1 c 10 90'
'set strsiz 0.17'
'draw string 0.4 4.25 [%]'

'set string 1 bl 10 0'
'set strsiz 0.2'
'draw string 1.2 7.65 probability of CWV'

'set string 1 br 10 0'
'set strsiz 0.2'
'draw string 10.5 7.65 'exp

'gxprint 'outPath'/cwv_dist.png x1600 y1200'
'gxprint 'outPath'/white/cwv_dist.png x1600 y1200 white'

function day2it(day)
  t0=(day-1)*72+1
  t1=day*72+1
return t0' 't1
