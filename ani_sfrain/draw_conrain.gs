function main(args)
iexp = subwrd(args,1)
if (iexp = ''); iexp=1; endif

**default 
te='none'
ts='none'
*mode='SAVEFIG'
mode='PAUSE'
type='conrain'
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

expList='f00 f10 f00_10 f00_15 f00_16 f00_17 f00_18 f00_19 f00_20 f00_21 f00_22 f00_23 f00_24 f00_25 f00_26 f00_27 f00_28 f00_29 f00_30'
*tlastList='2881 2161 1441 1081 2880 361 361 361 1441 1441'

exp = 'RRCE_3km_'subwrd(expList, iexp)
dt  = 20
*tlast = subwrd(tlastList, iexp)
tlast = 217
if ( exp = 'RRCE_3km_f00' ); tlast=2161;endif

sfen  = subwrd(enList, iexp)
say exp', 'dt', 'tlast', 'type

if (ts='none'); ts=1; endif
if (te='none'); te=tlast; endif
if (te>tlast);  te=tlast; endif

drawsf="FALSE"
drawrain="FALSE"
drawcon="FALSE"
if ( type = 'conrain' )
  drawcon="TRUE"
  drawrain="TRUE"
  sfidz=9
  sfhei='0.952km'
endif

outPath='./fig_'type'/'exp
say outPath
'! mkdir -p 'outPath

******** write the status *******
say ''
say '**********'
say 'drawing mode ... 'mode
say 'iexp='iexp', exp='exp', dt='dt
say 'ts='ts', te='te
say 'SFunc: 'drawsf
say 'rain:  'drawrain
say 'Con:   'drawcon

say 'outpath='outPath
say '**********'
say ''
********************************

'reinit'
*'set background 1'
'c'
'open 'vvmPath'/'exp'/gs_ctl_files/Thermodynamic.ctl'
'open 'vvmPath'/'exp'/gs_ctl_files/Dynamic.ctl'
'open 'vvmPath'/'exp'/gs_ctl_files/Surface.ctl'
'open 'datPath'/wp/'exp'.ctl'
if ( type = 'sfrain' )
  'open 'datPath'/horimsf/msf_'exp'.ctl'
endif
if ( type = 'conrain' )
  'open 'datPath'/convolve/'exp'/convolve.ctl'
endif

it = ts
*while(it<=tlast)
while(it<=te)
say 't='it''
'c'
'set lwid 211 10'
'set lwid 212 20'
'set parea 2.58333 8.41667 0.8 7.55'
'set xlopts 1 211 0.2'
'set ylopts 1 211 0.2'
'set clopts 1 211 0.2'
'set annot 1 211'
'set grads off'
'set timelab off'
'set mpdraw off'
'set xlabs 0|288|576|864|1152'
'set ylabs 0|288|576|864|1152'

'set t 'it

'color 10 60 2 -kind white->wheat->darkcyan->darkblue->(4,130,191) -gxout grfill'
*'color 10 60 2.5 -kind white->wheat->darkcyan->darkblue -gxout grfill'
lnum=(60-10)/2+2+15
*'set rgb 'lnum' 0 250 250'
'd cwv.4(z=1)'
'xcbar 8.6 8.8 4 7.5 -ft 211 -fs 5'
*'xcbar 8.6 8.8 4 7.5 -ft 10 -fs 2'

'set string 1 bl 211 0'
'set strsiz 0.2'
'draw string 8.55 8.0 CWV'
'draw string 8.55 7.65 [mm]'


if ( drawrain="TRUE" )
  'define rain = sprec.3(z=1)*3600'
  'set x 1'
  'set y 1'
  'd amax(rain,x=1,x=384,y=1,y=384)'
  maxrain = subwrd(result,4)
  say 'maxrain: 'maxrain
  'set x 1 384'
  'set y 1 384'

*  clevs='1 5 15 40'
  clevs='1 3 5 7 10 15 30 50'
  ckind='(255,255,255,0)->grainbow'
  ckind='white->plum->purple'
  'color -levs 'clevs' -gxout grfill -kind 'ckind' -xcbar 8.6 8.8 0.8 3.3 -ft 211'
  if (maxrain>1)
    'd maskout(rain,rain-1)'
  endif
  'set string 1 bl 211 0'
  'set strsiz 0.15'
  'draw string 8.55 3.4 Rain'
endif

** if (drawcon="TRUE")
**   'set z 'sfidz
**   'set gxout contour'
**   'set cmin 1'
**   'set cint 2'
**   'set rgb 20 163 0 12'
**   'set ccolor 20'
**   'set cthick 211'
**   'set clab masked'
**   'set clab off'
**   'd zeta.5(ens=100km)*1e5'
** endif


'set string 1 c 211'
'set strsiz 0.17'
'draw string 5.5 0.2 [km]'

'set string 1 c 211 90'
'set strsiz 0.17'
'draw string 1.7 4.375 [km]'

day=(it-1)*dt/60/24
dy=math_format( '%.3f', day)

hour=(it-1)*dt/60
hr=math_format('%.1f', hour)

'set string 1 bl 211 0'
'set strsiz 0.2'
'draw string 2.6875 8 'exp
title = 'CWV[mm] / Rain[mm hr`a-1`n]'

'draw string 2.6875 7.65 'title

'set string 1 br 211 0'
'set strsiz 0.2'
if ( RRCE_3km_f00=exp )
  'draw string 8.3125 8 'dy'days'
else
  'draw string 8.3125 8 'hr'hours'
endif

if ( mode="SAVEFIG" )
  itt=math_format( '%06.0f', it)
*  'gxprint 'outPath'/bla_conrain_'itt'.png x2400 y1800'
  'gxprint 'outPath'/bla_conrain_'itt'.png x3000 y1800'
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

