function main(args)
iexp = subwrd(args,1)
if (iexp = ''); iexp=12; endif

**default 
te='none'
ts='1'
*mode='SAVEFIG'
mode='PAUSE'
type='zeta'
zidx=5
contype='0km'
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


expList='f00 f10 f00_10 f00_15 f00_16 f00_17 f00_18 f00_19 f00_20 f00_21 f00_22 f00_23 f00_24 f00_25 f00_26 f00_27 f00_28 f00_29 f00_30'
tlastList='2881 2161 1441 1081 2880 361 361 361 1441 1441'
tlastList='2521 2161 1441 1081 2880 361 361 361 1441 1441'

conZetaList='0km 25km 50km 100km'

exp = 'RRCE_3km_'subwrd(expList, iexp)
dt  = 20
if (iexp<=1)
  tlast = subwrd(tlastList, iexp)
else
  tlast = 217
endif
sfctl = subwrd(sfCtlList, iexp)
sfen  = subwrd(enList, iexp)
say exp', 'dt', 'tlast', 'type

if (zidx=1); zname='1.5km';   iz=11; endif
if (zidx=2); zname='5.75km';  iz=20; endif
if (zidx=3); zname='12.25km'; iz=33; endif
if (zidx=4); zname='0.457km'; iz=6; endif
if (zidx=5); zname='0.952km'; iz=9; endif
if (zidx=6); zname='0.240km'; iz=4; endif

if (ts='none'); ts=1; endif
if (te='none'); te=tlast; endif
if (te>tlast);  te=tlast; endif

drawzeta="FALSE"
drawcore="FALSE"
if ( type = 'zeta' )
  drawzeta="TRUE"
  drawcore="TRUE"
endif

outPath="./fig_"type"_ws/"exp
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

icon = 1
while(icon<=4)
contype=subwrd(conZetaList,icon)
'c'

*'set parea 2.58333 8.41667 0.8 7.55'
'set parea 1 9.5 0.8 7.55'
'set xlopts 1 10 0.2'
'set ylopts 1 10 0.2'
'set grads off'
'set timelab off'
'set mpdraw off'

* 'set xlabs 0|288|576|864|1152'
* 'set ylabs 0|288|576|864|1152'

'set x 1 384'
'set y 192 384'
'set xlabs 0|288|576|864|1152'
'set ylabs 576|864|1152'

'set t 'it
'set z 'iz

*X Limits = 1 to 9.5
*Y Limits = 1.61834 to 6.73166

'set gxout shaded'
'color -levs -100 -10 0 10 100 -gxout grfill -kind (73,32,255)->white->(255,132,36)'
if ( contype='0km')
  'd zeta.1*1e5'
else
  'd zeta.4(ens='contype')*1e5'
endif
'xcbar 9.7 9.85 1.61834 6.73166 -ft 10 -fs 1 -fw 0.1 -fh 0.15'

'set gxout contour'
'set cthick 5'
'set ccolor 0'
'set clab masked'
'set clevs 3'
'd mag(u,v)'

** *'color -levs 1 3 5 7 -kind grainbow'
** 'set cthick 3'
** 'set arrscl 0.5 10'
** 'set clevs 1 4 7'
** 'set rgb 50 100 100 100'
** 'set rgb 52 150 150 150'
** 'set ccols -1 1 52 50'
** 'd skip(u,3);v;mag(u,v)'
** 'xcbar 10.5 10.65 1.61834 6.73166 -ft 10 -fs 1 -fw 0.1 -fh 0.15 -line off'

*X Limits = 1 to 9.5
*Y Limits = 1.61834 to 6.73166
'set string 1 bl 10 0'
'set strsiz 0.2'

'set string 1 c 10'
'set strsiz 0.17'
'draw string 5.5 1 [km]'

'set string 1 c 10 90'
'set strsiz 0.17'
'draw string 0.1 4.375 [km]'

title='wind speed [m/s] / con-'contype' zeta [10`a5`ns`a-1`n]'
day=(it-1)*dt/60/24
dy=math_format( '%.3f', day)

hour=(it-1)*dt/60
hr=math_format('%.1f', hour)

'set string 1 bl 10 0'
'set strsiz 0.2'
'draw string 1 7.45 'exp
'draw string 1 7. 'title

'set string 1 br 10 0'
'set strsiz 0.2'
if ( exp='RRCE_3km_f00' )
  'draw string 9.5 7.45 @'zname' / 'dy'days'
else
  'draw string 9.5 7.45 @'zname' / 'hr'hours'
endif
*'draw string 9.5 8 @'zname

itt=math_format( '%06.0f', it)
'gxprint 'outPath'/bla_'iz'_'type'_con'contype'_'itt'.png x2400 y1800'
*pull get

* contype
icon = icon+1
endwhile

*it=it+216
it=it+3*72
endwhile

exit
*if ( mode="SAVEFIG" )
if ( mode="PAUSE")
  itt=math_format( '%06.0f', it)
* 'gxprint 'outPath'/whi_olr'type'_'itt'.png x2400 y1800 white'
  'gxprint 'outPath'/bla_'iz'_'type'_con'contype'_'itt'.png x2400 y1800'
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

