function main(args)
iexp = subwrd(args,1)
if (iexp = ''); iexp=4; endif

**default 
te='none'
ts='none'
*mode='SAVEFIG'
mode='PAUSE'
**default

i = 2
while( 1 )
  arg = subwrd( args, i )
  i=i+1
  if( arg = '' )
    break
  endif

  while( 1 )
    if( arg = '-te' ) ; te=subwrd(args,i) ; i=i+1 ; break ; endif
    if( arg = '-ts' ) ; ts=subwrd(args,i) ; i=i+1 ; break ; endif
    if( arg = '-mode' ) ; mode=subwrd(args,i) ; i=i+1 ; break ; endif
    say 'syntax error: 'arg
    return
  endwhile
endwhile

vvmPath="/data/C.shaoyu/rrce/vvm/"
datPath="/data/C.shaoyu/rrce/data/"
expList='RCE_300K_3km_f0 RCE_300K_3km_f05 RRCE_3km_f00 RRCE_3km_f10 RRCE_3km_f15 RRCE_3km_f20'
dtList='60 60 20 20 20 20 20'
tlastList='2137 2030 3654 2286 2161 2138'

sfCtlList='RCE_300K_3km RCE_300K_3km RRCE_3km RRCE_3km RRCE_3km RRCE_3km'
enList='1 2 1 2 3 4'

exp = subwrd(expList, iexp)
dt  = subwrd(dtList, iexp)
tlast = subwrd(tlastList, iexp)
sfctl = subwrd(sfCtlList, iexp)
sfen  = subwrd(enList, iexp)
say exp', 'dt', 'tlast

if (ts='none'); ts=1; endif
if (te='none'); te=tlast; endif
if (te>tlast);  te=tlast; endif

drawsf="TRUE"
drawdis="TRUE"
drawws="FALSE"

outPath="./fig/"exp
'! mkdir -p 'outPath

******** write the status *******
say ''
say '**********'
say 'drawing mode ... 'mode
say 'iexp='iexp', exp='exp', dt='dt
say 'ts='ts', te='te
say 'SFunc: 'drawsf', 'sfctl', en='sfen
say 'WS   : 'drawws
say 'Dist : 'drawdis

say 'outpath='outPath
say '**********'
say ''
********************************

'reinit'
*'set background 1'
'c'
'open 'vvmPath'/'exp'/gs_ctl_files/Dynamic.ctl'
'open 'datPath'/wp/'exp'.ctl'
'open 'datPath'/horisf/'sfctl'_000.ctl'
'open 'datPath'/distance/'exp'.ctl'

it = ts
*while(it<=tlast)
while(it<=te)
say 't='it''
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

if ( drawdis="TRUE" )
  'set gxout contour'
  'set clevs 100 200 300 400 500 600'
  'set rgb 40 0 0 0'
  'set ccolor 40'
  'set clab off'
  'set cthick 10'
  'd dis.4'
  
  'set clevs 3'
  'set rgb 40 120 120 120'
  'set ccolor 40'
  'set clab off'
  'set lwid 50 20'
  'set cthick 50'
  'd dis.4'
endif

if ( drawsf="TRUE" )
**   'set gxout contour'
**   'set clevs 1e5 1e6'
**   'set ccols 12 2'
**   'set cthick 5'
**   'set clab off'
**   'd hsf.3(e='sfen')'
**   
**   'set rgb 70 100 100 100'
**   'set clevs 0 1e4'
**   'set ccols 15 70'
**   'set cthick 5'
**   'set clab off'
**   'd hsf.3(e='sfen')'
**   
**   'set clevs 2.5e5'
**   'set ccols 0'
**   'set cthick 10'
**   'set clab off'
**   'd hsf.3(e='sfen')'
  'set gxout contour'
  'set clevs 0 1 5 10 15 20 25 30 35 40 45 50'
  'set rgb 50 120 120 120'
  'set ccolor 50'
  'set lwid 50 5'
  'set cthick 50'
  'set clab off'
  'd hsf.3(e='sfen')*1e-5'
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

if ( mode="SAVEFIG" )
  itt=math_format( '%06.0f', it)
  'gxprint 'outPath'/whi_cwvsf_'itt'.png x2400 y1800 white'
  'gxprint 'outPath'/bla_cwvsf_'itt'.png x2400 y1800'
  it = it+1
endif

if ( mode="PAUSE")
  te=tlast
  pull step
  if(step='q'|step='quit'|step='exit');exit;endif
  if(step='');it=it+1;continue;else
    rc=valnum(step)
    if(rc=0);step;pull step;endif
    if(rc=1&step>0);it=step;endif
  endif
endif

endwhile

