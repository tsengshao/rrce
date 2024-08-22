function main(args)
iexp = subwrd(args,1)
if (iexp = ''); iexp=1; endif

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
expList='f00 f10 f00_10 f00_15 f00_16 f00_17 f00_18 f00_19 f00_20 f00_21 f00_22 f00_23 f00_24 f00_25 f00_26 f00_27 f00_28 f00_29 f00_30'
*tlastList='2881 2161 1441 1081 2880 361 361 361 1441 1441'

exp = 'RRCE_3km_'subwrd(expList, iexp)
dt  = 20
*tlast = subwrd(tlastList, iexp)
*tlast = 217
if (iexp<=1)
  tlast = 2521
else
  tlast = 217
endif
say exp', 'dt', 'tlast

if (ts='none'); ts=1; endif
if (te='none'); te=tlast; endif
if (te>tlast);  te=tlast; endif

centertype='sf_largest_0'

drawradi="TRUE"
drawtang="FALSE"
drawqc="FALSE"
drawqv="FALSE"

outPath="./fig_axisym/"centertype"/"exp"/"
'! mkdir -p 'outPath

******** write the status *******
say ''
say '**********'
say 'drawing mode ... 'mode
say 'iexp='iexp', exp='exp', dt='dt
say 'ts='ts', te='te
say 'radial   : 'drawradi
say 'tang     : 'drawtang
say 'qc   : 'drawqc
say 'qv   : 'drawqv

say 'outpath='outPath
say '**********'
say ''
********************************

'reinit'
*'set background 1'
'c'
'open 'datPath'/distance/'centertype'/axisym_'exp'.ctl'
'open 'datPath'/distance/'centertype'/axisym_gamma_'exp'.ctl'

* get dx
'q ctlinfo'
line=sublin(result, 5)
dx = subwrd(line,5)
nx = subwrd(line,2)

it = ts
while(it<=te)
say 't='it''
'c'

'set parea 1 9.5 3 7.5'
'set xlopts 1 10 0.2'
'set ylopts 1 10 0.2'
'set grads off'
'set timelab off'
'set mpdraw off'

'set x 1 'nx
'set lev 0 16000'
'set xlabs ||||||||||'
'set ylabs 0|2|4|6|8|10|12|14|16'

'set t 'it
if (drawqv="TRUE")
  'color -5 5 1 -kind darkviolet->blueviolet->white->orange->crimson -gxout shaded'
  'd (qv-ave(qv,x=1,x=160))*1e3)'
  'xcbar 9.8 10 3.5 7.5 -ft 10' 
endif

if ( drawradi="TRUE" )
  'color -5 5 1 -kind darkviolet->blueviolet->white->orange->crimson -gxout grfill'
  'd radi'

  'set gxout contour'
  'set clevs 0.1 0.5 0.75 1'
  'set rgb 40 0 0 0'
  'set ccolor 40'
  'set clab masked'
  'd radi.2'
  'xcbar 9.8 10 3.5 7.5 -ft 10' 

*  'xcbar 9.8 10 3.5 7.5 -ft 10' 
*   'color -15 15 1 -kind crimson->orange->white->blueviolet->darkviolet -gxout shaded'
*   'set clab off'
*   'd radi'
*   'xcbar 9.8 10 3.5 7.5 -ft 10 -fs 5' 
*  'd radi'
endif

if ( drawtang="TRUE" )
  'color -10 10 1 -kind darkviolet->blueviolet->white->orange->crimson -gxout grfill'
  'd tang'

  'set gxout contour'
  'set clevs 0.1 0.5 0.75 1'
  'set rgb 40 0 0 0'
  'set ccolor 40'
  'set clab masked'
  'd tang.2'

  'xcbar 9.8 10 3.5 7.5 -ft 10' 
endif


'set string 1 tc 10 90'
'set strsiz 0.17'
'draw string 0.25 5.25 [km]'

*------ draw lower pannel
tot=nx*dx
idxz=9
idxhei='0.9km'
idxz=1
idxhei='surface'

'set parea 1 9.5 1 3'
'set xlabs 0|'tot*1/10'|'tot*2/10'|'tot*3/10'|'tot*4/10'|'tot*5/10'|'tot*6/10'|'tot*7/10'|'tot*8/10'|'tot*9/10'|'tot

'set vrange 0 1'
'set ylabs 0|.25|0.5|0.75|1'
'set cmark 0'
'set lwid 50 5'
'set cthick 50'
'set ccolor 1'
'set z 'idxz
'd maskout(radi.2,sample(z=1)>0)'

'set parea 1 9.5 1 3'
'off'
'set vrange -4 4' 
'set cmark 0'
'set cthick 50'

'set rgb 50 240 145 255'
'set ccolor 50'
'd maskout(radi, sample(z=1)>0)'
'set string 50 l 10 0'
'draw string 9.6 1   -4'
'draw string 9.6 1.5 -2'
'draw string 9.6 2   0'
'draw string 9.6 2.5 2'
'draw string 9.6 3   4'

'set string 50 tc 10 90'
'draw string 10.2 2 Wind`btangential`n@0.9km'
'draw string 10.6 2 [m/s]'
'on'

'set string 1 c 10 90'
'set strsiz 0.2'
'draw string 0.15 2 axisymmetricity'

'set string 1 tr 10 0'
'set strsiz 0.17'
'draw string 5.5 0.5 [km]'


'set parea 1 9.5 3 7.5'
'set lev 0 16'

day=(it-1)*dt/60/24
dy=math_format( '%.3f', day)

hour=(it-1)*dt/60
hr=math_format('%.1f', hour)

'set string 1 bl 10 0'
'set strsiz 0.2'
'draw string 1 8 'exp
title='tangwind[m/s] / axisymmetricity'
if ( drawradi="TRUE" ); title=title' / radial wind [m/s]';endif
if ( drawqc="TRUE"); title=title' / qc [g/kg]'; endif
if ( drawqv="TRUE"); title=title' / anomaly_qv [g/kg]'; endif

'draw string 1 7.65 'title

'set string 1 br 10 0'
'set strsiz 0.2'
if ( RRCE_3km_f00=exp )
  'draw string 9.5 8 'dy'days'
else
  'draw string 9.5 8 'hr'hours'
endif

*if ( mode="SAVEFIG" )
if ( mode="PAUSE")
  itt=math_format( '%06.0f', it)
*  'gxprint 'outPath'/whi_axisym_radi_'itt'.png x2400 y1800 white'
  'gxprint 'outPath'/bla_axisym_radi_'itt'.png x2400 y1800'
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

