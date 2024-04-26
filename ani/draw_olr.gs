function main(args)
iexp = subwrd(args,1)
if (iexp = ''); iexp=4; endif

**default 
te='none'
ts='none'
*mode='SAVEFIG'
mode='PAUSE'
type='rain'
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
    if( arg = '-type' ) ; type=subwrd(args,i) ; i=i+1 ; break ; endif
    say 'syntax error: 'arg
    return
  endwhile
endwhile

vvmPath="/data/C.shaoyu/rrce/vvm/"
datPath="/data/C.shaoyu/rrce/data/"

** expList='RCE_300K_3km_f0 RCE_300K_3km_f05 RRCE_3km_f00 RRCE_3km_f05 RRCE_3km_f10 RRCE_3km_f15 RRCE_3km_f20'
** dtList='60 60 20 20 20 20 20'
** tlastList='2137 2030 3654 2765 2286 2161 2138'
** sfCtlList='RCE_300K_3km RCE_300K_3km RRCE_3km RRCE_3km RRCE_3km RRCE_3km RRCE_3km'
** enList='1 2 1 2 3 4 5'

expList='RRCE_3km_f00_10 RRCE_3km_f00_20 RRCE_3km_f00_25 RRCE_3km_f00_30 RRCE_3km_f00'
dtList='20 20 20 20 20'
tlastList='1441 1441 1441 1441 2881'


exp = subwrd(expList, iexp)
dt  = subwrd(dtList, iexp)
tlast = subwrd(tlastList, iexp)
sfctl = subwrd(sfCtlList, iexp)
sfen  = subwrd(enList, iexp)
say exp', 'dt', 'tlast', 'type

if (ts='none'); ts=1; endif
if (te='none'); te=tlast; endif
if (te>tlast);  te=tlast; endif

drawrain="FALSE"
drawcwv="FALSE"
if ( type = 'rain' )
  drawrain="TRUE"
  drawcwv="TRUE"
endif

outPath="./fig_olr_"type"/"exp
'! mkdir -p 'outPath

******** write the status *******
say ''
say '**********'
say 'drawing mode ... 'mode
say 'iexp='iexp', exp='exp', dt='dt
say 'ts='ts', te='te
say 'drawrain='drawrain

say 'outpath='outPath
say '**********'
say ''
********************************

'reinit'
*'set background 1'
'c'
'open 'vvmPath'/'exp'/gs_ctl_files/Dynamic.ctl'
'open 'vvmPath'/'exp'/gs_ctl_files/Thermodynamic.ctl'
'open 'vvmPath'/'exp'/gs_ctl_files/Surface.ctl'
if ( type='rain' )
  'open 'datPath'/wp/'exp'.ctl'
endif

it = ts
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
'color 100 300 20 -kind white->black -gxout grfill'
'd olr.3(z=1)'
'xcbar 8.6 8.8 4 7.5 -ft 10 -fs 1'

'set string 1 bl 10 0'
'set strsiz 0.2'
'draw string 8.55 8.0 OLR'
'draw string 8.55 7.65 [Wm`a2`n]'

if ( drawrain="TRUE" )
  clevs='1 3 5 7 10 15 30 50'
  'color -levs 'clevs' -gxout grfill -kind (255,255,255,0)->grainbow'
  'd sprec.3*3600'
  'xcbar 8.6 8.8 0.8 3.3 -ft 10'
  'set string 1 bl 10 0'
  'set strsiz 0.15'
  'draw string 8.55 3.4 Rain'
endif
if (drawcwv="TRUE" )
  'set gxout contour'
  'set clevs 40'
  'set ccolor 2'
  'set cthick 5'
  'set clab off'
  'd cwv.4'
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
itit=1
if ( drawrain="TRUE" ); title.itit='CWV [40mm]'; itit=itit+1;endif
if ( drawrain="TRUE" ); title.itit='rain[mm/hr`a-1`n]'; itit=itit+1;endif
itit = itit - 1

title=title.itit
itit = itit - 1
while(itit>=1)
title = title' / 'title.itit
itit = itit - 1
endwhile


'draw string 2.6875 7.65 'title

'set string 1 br 10 0'
'set strsiz 0.2'
'draw string 8.3125 8 'dy'days'

if ( mode="SAVEFIG" )
  itt=math_format( '%06.0f', it)
* 'gxprint 'outPath'/whi_cwv'type'_'itt'.png x2400 y1800 white'
  'gxprint 'outPath'/bla_cwv'type'_'itt'.png x2400 y1800'
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

