function main(args)
iexp = subwrd(args,1)
if (iexp = ''); iexp=6; endif

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

drawradi="TRUE"
exp = subwrd(expList, iexp)
dt  = subwrd(dtList, iexp)
tlast = subwrd(tlastList, iexp)
sfctl = subwrd(sfCtlList, iexp)
sfen  = subwrd(enList, iexp)
say exp', 'dt', 'tlast

if (ts='none'); ts=1; endif
if (te='none'); te=tlast; endif
if (te>tlast);  te=tlast; endif

outPath="./fig/"exp"/"
'! mkdir -p 'outPath

******** write the status *******
say ''
say '**********'
say 'drawing mode ... 'mode
say 'iexp='iexp', exp='exp', dt='dt
say 'ts='ts', te='te
say 'radial   : 'drawradi

say 'outpath='outPath
say 'outPathBlack='outPathBlack
say '**********'
say ''
********************************

'reinit'
*'set background 1'
'c'
'open 'datPath'/distance/'exp'_axisym.ctl'

it = ts
*while(it<=tlast)
while(it<=te)
say 't='it''
'c'

'set parea 1 9.5 3 7.5'
'set xlopts 1 10 0.2'
'set ylopts 1 10 0.2'
'set grads off'
'set timelab off'
'set mpdraw off'

'set x 1 60'
'set lev 0 16'
'set xlabs ||||||'
'set ylabs 0|4|8|12|16'

'set t 'it
if ( drawradi="TRUE" )
  'color -15 15 1 -kind crimson->orange->white->blueviolet->darkviolet -gxout shaded'
  'set clab off'
  'd radi'
  'xcbar 9.8 10 3.5 7.5 -ft 10 -fs 5' 
endif
*'color -levs 0 0.02 0.04 0.06 0.08 0.1 0.2 0.3 -kind (0,0,0,0)-(0)->(150,150,150)->white'
'set gxout contour'
'set clevs 0 0.02 0.04 0.06 0.08 0.1 0.15 0.2 0.3 1'
'set cthick 8'
'set rgb 40 0 0 0'
'set ccolor 40'
' d qc*1e3'


'set string 1 tr 10 90'
'set strsiz 0.17'
'draw string 0.25 4.5 [km]'

*------ draw lower pannel
'set parea 1 9.5 1 3'
'set xlabs 0|50|100|150|200|250|300'
'set vrange 10 90'
'set ylabs 10|30|50|70|90'
'set cmark 0'
'set lwid 50 5'
'set cthick 50'
'set ccolor 1'
'set z 1'
'd maskout(cwv,sample>0)'

'set parea 1 9.5 1 3'
'off'
'set vrange -10 30'
'set cmark 0'
'set cthick 50'

'set rgb 50 240 145 255'
'set ccolor 50'
'd maskout(tang(z=1), sample>0)'
'set string 50 l 10 0'
'draw string 9.6 1   -10'
'draw string 9.6 1.5 0'
'draw string 9.6 2   10'
'draw string 9.6 2.5 20'
'draw string 9.6 3   30'

'set string 50 tc 10 90'
'draw string 10.2 2 Wind`btangential`n@Surf.'
'draw string 10.6 2 [m/s]'
'on'

'set string 1 c 10 90'
'set strsiz 0.17'
'draw string 0.25 2 CWV [mm]'

'set string 1 tr 10 0'
'set strsiz 0.17'
'draw string 5.5 0.5 [km]'

day=(it-1)*dt/60/24
dy=math_format( '%.3f', day)
'set string 1 bl 10 0'
'set strsiz 0.2'
'draw string 1 8 'exp
title='qc [g/kg]'
if ( drawradi="TRUE" ); title=title' / radial wind [m/s]';endif

'draw string 1 7.65 'title

'set string 1 br 10 0'
'set strsiz 0.2'
'draw string 9.5 7.65 'dy'days'

if ( mode="SAVEFIG" )
  itt=math_format( '%06.0f', it)
  'gxprint 'outPath'/whi_axsym_radi_'itt'.png x2400 y1800 white'
  'gxprint 'outPath'/bla_axsym_radi_'itt'.png x2400 y1800'
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

