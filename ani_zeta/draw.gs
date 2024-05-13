function main(args)
iexp = subwrd(args,1)
if (iexp = ''); iexp=6; endif

**default 
te='none'
ts='none'
*mode='SAVEFIG'
mode='PAUSE'
type='zeta'
zidx=1
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
    if( arg = '-zidx' ) ; zidx=subwrd(args,i) ; i=i+1 ; break ; endif
    say 'syntax error: 'arg
    return
  endwhile
endwhile

vvmPath="/data/C.shaoyu/rrce/vvm/"
datPath="/data/C.shaoyu/rrce/data/"


*expList='RRCE_3km_f00 RRCE_3km_f00_10 RRCE_3km_f00_15 RRCE_3km_f00_20 RRCE_3km_f00_21 RRCE_3km_f00_25 RRCE_3km_f00_30'
*dtList='20 20 20 20 20 20 20'
*tlastList='2881 1441 1081 2880 361 1441 1441 2881'
dt  = subwrd(dtList, iexp)

expList='f00 f10 f00_10 f00_15 f00_16 f00_17 f00_18 f00_19 f00_20 f00_21 f00_22 f00_23 f00_24 f00_25 f00_30'
*tlastList='2881 2161 1441 1081 2880 361 361 361 1441 1441'

exp = 'RRCE_3km_'subwrd(expList, iexp)
dt  = 20
* if (iexp<=2)
*   tlast = subwrd(tlastList, iexp)
* else
*   tlast = 361
* endif
tlast = 217
sfctl = subwrd(sfCtlList, iexp)
sfen  = subwrd(enList, iexp)
say exp', 'dt', 'tlast', 'type

if (zidx=1); zname='1.5km';   iz=11; endif
if (zidx=2); zname='5.75km';  iz=20; endif
if (zidx=3); zname='12.25km'; iz=33; endif

if (ts='none'); ts=1; endif
if (te='none'); te=tlast; endif
if (te>tlast);  te=tlast; endif

drawzeta="FALSE"
drawcore="FALSE"
if ( type = 'zeta' )
  drawzeta="TRUE"
  drawcore="TRUE"
endif

outPath="./fig_"type"/"exp
'! mkdir -p 'outPath

******** write the status *******
say ''
say '**********'
say 'drawing mode ... 'mode
say 'iexp='iexp', exp='exp', dt='dt
say 'ts='ts', te='te
say 'drawrain='drawrain
say 'height='zname' ( 'iz' )'

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
if ( type='zeta' )
  'open 'datPath'/convolve/'exp'/convolve.ctl'
  'open 'datPath'/horimsf/msf_'exp'.ctl'
endif

it = ts
say it' 'ts' 'te
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
'set z 'iz
'color -5 5 1 -gxout grfill'
'd 1e4*zeta.4(ens=25km)'
'xcbar 8.6 8.8 0.8 7.55 -ft 10 -fs 1'

'set cthick 10'
'color 1 50 1 -gxout contour -kind gray->gray'
'set clab masked'
'd msf.5*1e-5'

'set gxout contour'
'set lwid 50 5'
'set cthick 50'
'set rgb 100 0 0 0'
'set ccolor 100'
'set clevs 1'
'set clab off'
'd 1e4*zeta.4(ens=100km)'

'set string 1 bl 10 0'
'set strsiz 0.2'

'set string 1 c 10'
'set strsiz 0.17'
'draw string 5.5 0.2 [km]'

'set string 1 c 10 90'
'set strsiz 0.17'
'draw string 1.7 4.375 [km]'

'set lwid 80 2'
'set strsiz 0.1'
'set rgb 83 0 0 0'
'set string 83 tl 80 0'
'draw string 2.75 7.5 black  : zeta ( 100km / 25km )'
'set rgb 83 100 100 100'
'draw string 2.75 7.3 grey  : hori. sf. [10`a5`n kg*m`a2`ns`a-2`n]'

title='zeta [10`a-4`ns`a-1`n] / sf.'
day=(it-1)*dt/60/24
dy=math_format( '%.3f', day)

hour=(it-1)*dt/60
hr=math_format('%.1f', hour)

'set string 1 bl 10 0'
'set strsiz 0.2'
'draw string 2.6875 8 'exp
'draw string 2.6875 7.65 'title

'set string 1 br 10 0'
'set strsiz 0.2'
*'draw string 8.3125 8 'dy'days'
'draw string 8.3125 8 'hr'hours'
'draw string 8.3125 7.65 @'zname

if ( mode="SAVEFIG" )
  itt=math_format( '%06.0f', it)
* 'gxprint 'outPath'/whi_olr'type'_'itt'.png x2400 y1800 white'
  'gxprint 'outPath'/bla_'iz'_'type'_'itt'.png x2400 y1800'
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

