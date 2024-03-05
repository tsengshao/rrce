function main(args)
iexp = subwrd(args,1)

vvmPath="/data/C.shaoyu/rrce/vvm/"
datPath="/data/C.shaoyu/rrce/data/"
expList='RCE_300K_3km_f0 RCE_300K_3km_f05 RRCE_3km_f00 RRCE_3km_f10 RRCE_3km_f15 RRCE_3km_f20'
dtList='60 60 20 20 20 20'
tlastList='2137 2030 3654 2286 2161 2138'

sfCtlList='RCE_300K_3km RCE_300K_3km RRCE_3km RRCE_3km RRCE_3km'
enList='1 2 1 2 3 4'

exp = subwrd(expList, iexp)
dt  = subwrd(dtList, iexp)
tlast = subwrd(tlastList, iexp)
sfctl = subwrd(sfCtlList, iexp)
sfen  = subwrd(enList, iexp)
say exp', 'dt', 'tlast

drawsf="TRUE"
drawws="FALSE"

outPath="./fig/"exp
'! mkdir -p 'outPath
outPathBlack="./fig_black/"exp
'! mkdir -p 'outPathBlack

'reinit'
*'set background 1'
'c'
'open 'vvmPath'/'exp'/gs_ctl_files/Dynamic.ctl'
*'open 'datPath'/cwv/'exp'.ctl'
'open 'datPath'/wp/'exp'.ctl'
'open 'datPath'/horisf/'sfctl'_000.ctl'

it = 1
while(it<=tlast)
'c'

'set parea 2.58333 8.41667 0.8 7.55'
'set xlopts 1 10 0.2'
'set ylopts 1 10 0.2'
'set grads off'
'set timelab off'
'set mpdraw off'
'set xlabs 0|288|576|864|1152'
'set ylabs 0|288|576|864|1152'

'set t 'it
'color 10 60 2 -kind white->wheat->darkcyan->darkblue->aqua -gxout grfill'
'd cwv.2(z=1)'
'xcbar 8.6 8.8 0.8 7.55 -ft 10 -fs 5'

if ( drawsf="TRUE" )
  'set gxout contour'
  'set clevs 1e5 1e6'
  'set ccols 12 2'
  'set cthick 5'
  'set clab off'
  'd hsf.3(e='sfen')'
  
  'set rgb 70 100 100 100'
  'set clevs 0 1e4'
  'set ccols 15 70'
  'set cthick 5'
  'set clab off'
  'd hsf.3(e='sfen')'
  
  'set clevs 2.5e5'
  'set ccols 0'
  'set cthick 10'
  'set clab off'
  'd hsf.3(e='sfen')'
endif


if ( drawws = "TRUE" )
  'set gxout contour'
  'set clevs 5 10'
  'set ccols 15 12'
  'set clab off'
  'set cthick 3'
  'd mag(u,v)'
  
  'set clevs 18 33'
  'set ccols 8 2'
  'set clab off'
  'set cthick 5'
  'd mag(u,v)'
endif

'set string 1 c 10'
'set strsiz 0.17'
'draw string 5.5 0.2 [km]'

'set string 1 c 10 90'
'set strsiz 0.17'
'draw string 1.7 4.375 [km]'

day=(it-1)*dt/60/24
dy=math_format( '%.3f', day)
'set string 1 bl 10 0'
'set strsiz 0.2'
'draw string 2.6875 8 'exp
title='CWV[mm]'
if ( drawws="TRUE" ); title=title' / WS[ms`a-1`n]';endif
if ( drawsf="TRUE" ); title=title' / SF@Suf.[kg s`a-1`nm`a-1`n]';endif

'draw string 2.6875 7.65 'title

'set string 1 br 10 0'
'set strsiz 0.2'
'draw string 8.3125 8 'dy'days'
itt=math_format( '%06.0f', it)
'gxprint 'outPath'/cwvsf_'itt'.png x2400 y1800 white'
'gxprint 'outPathBlack'/cwvsf_'itt'.png x2400 y1800'
it = it+1

** pull step
** if(step='q'|step='quit'|step='exit');exit;endif
** if(step='');it=it+1;continue;else
**   rc=valnum(step)
**   if(rc=0);step;pull step;endif
**   if(rc=1&step>0);it=step;endif
** endif

endwhile


