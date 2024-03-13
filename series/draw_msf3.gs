function main(args)

nexp=7
vvmPath="/data/C.shaoyu/rrce/vvm/"
datPath="/data/C.shaoyu/rrce/data/"
expList='RCE_300K_3km_f0 RCE_300K_3km_f05 RRCE_3km_f00 RRCE_3km_f05 RRCE_3km_f10 RRCE_3km_f15 RRCE_3km_f20'
dtList='60 60 20 20 20 20 20'
tlastList='2137 2030 3654 2765 2286 2161 2138'
lcList='11 4 1 7 8 30 14'
'set rgb 30 255 85 33'
'set lwid 55 5'

outPath="./fig/"
'! mkdir -p 'outPath

'reinit'
'c'
it=1
while(it<=nexp)
  'open 'datPath'/series/'subwrd(expList,it)'.ctl'
  it=it+1
endwhile

TE=40
dt=subwrd(dtList,1)
idxTS=1
idxTE=math_format('%.0f', TE*24*60/dt+1)
'set t 1 'idxTE
'set xlabs 0||'TE/4'||'TE/2'||'TE*0.75'||'TE

'set parea 1.2 10.5 1 7.5'
'set xlopts 1 10 0.2'
'set ylopts 1 10 0.2'
'set grads off'
'set timelab off'
'set vrange 0 40'
'set ylabs 0|10|20|30|40'
*'set ylint 5'
i=1
while(i<=nexp)
  if ( i>1 )
    'off.gs'
  endif
  'set cmark 0'
  'set ccolor 'subwrd(lcList,i)
  'set cthick 55'
  'd msf3.'i'*1e-5'
  i=i+1
endwhile
'on.gs'

'set cthick 55'
'legend tl 'nexp' 'expList' 'lcList''

*X Limits = 1.2 to 10.5
*Y Limits = 1 to 7.5

'set string 1 c 10'
'set strsiz 0.17'
'draw string 5.85 0.5 [days]'

'set string 1 c 10 90'
'set strsiz 0.17'
'draw string 0.4 4.25 x10`a5`n [kg s`a-1`nm`a-1`n]'

'set string 1 bl 10 0'
'set strsiz 0.2'
*'draw string 1.2 8 'exp
'draw string 1.2 7.65 maximum stream function @2.75km'

'gxprint 'outPath'/sf3_max.png x1600 y1200'
'gxprint 'outPath'/white/sf3_max.png x1600 y1200 white'

exit
