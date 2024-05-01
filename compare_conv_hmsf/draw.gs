
function main(args)

iexp = subwrd(args,1)
if (iexp = ''); iexp=3; endif

** ========= default =========**
te='none'
ts='none'
*mode='SAVEFIG'
mode='PAUSE'
type=''
** ========= default =========**

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

expList='RRCE_3km_f00_10 RRCE_3km_f00_15 RRCE_3km_f00_20 RRCE_3km_f00_25 RRCE_3km_f00_30 RRCE_3km_f00'
dtList='20 20 20 20 20 20'
tlastList='1441 493 2880 1441 1441 2881'

exp = subwrd(expList, iexp)
dt  = subwrd(dtList, iexp)
tlast = subwrd(tlastList, iexp)
sfctl = subwrd(sfCtlList, iexp)
sfen  = subwrd(enList, iexp)

if (ts='none'); ts=1; endif
if (te='none'); te=tlast; endif
if (te>tlast);  te=tlast; endif

say exp', 'dt', 'tlast', 'type
say 'ts='ts', te='te


outPath="./fig/"exp
'! mkdir -p 'outPath''

'reinit'
*'set background 1'
'c'
'open 'vvmPath'/'exp'/gs_ctl_files/Dynamic.ctl'
'open 'vvmPath'/'exp'/gs_ctl_files/Thermodynamic.ctl'
'open 'datPath'/wp/'exp'.ctl'
'open 'datPath'/convolve/'exp'/convolve.ctl'
'open 'datPath'/horimsf/msf_'exp'.ctl'

it = ts
while(it<=te)
say 't='it''
'c'
'set t 'it

'set parea 2.58333 8.41667 0.8 7.55'
'set xlopts 1 10 0.2'
'set ylopts 1 10 0.2'
'set grads off'
'set timelab off'
'set mpdraw off'
'set xlabs 0|288|576|864|1152'
'set ylabs 0|288|576|864|1152'

*zz(11) --> 1.49km
iz=11
'set z 'iz
'color -5 5 1 -gxout grfill'
'd 1e4*zeta.4(ens=25km)'
'xcbar 8.6 8.8 0.8 7.55 -ft 10 -fs 1'

'set gxout contour'
'set lwid 50 5'
'set cthick 50'
'set rgb 100 0 0 0'
'set ccolor 100'
'set clevs 1'
'set clab off'
'd 1e4*zeta.4(ens=100km)'

** 'set rgb 100 50 50 50'
** 'set ccolor 100'
** 'set clevs 0.5'
** 'd 1e4*zeta.4(ens=100km)'

'set cthick 10'
'color 1 50 1 -gxout contour -kind gray->gray'
'set clab masked'
'd msf.5*1e-5'

'set string 1 bl 10 0'
'set strsiz 0.15'
'draw string 8.55 8.0 con25km'
'draw string 8.55 7.65 zeta[10`a-5`ns`a-1`n]'


'set lwid 80 2'
'set rgb 83 0 0 0'
'set string 83 tl 80 0'
'set strsiz 0.1'
'draw string 2.75 7.5 black : con100km-zeta [1x10`a-5`ns`a-1`n]'
'set rgb 83 100 100 100'
'set string 83 tl 80 0'
'draw string 2.75 7.3 grey  : hori. sf. [10`a5`n kg*m`a2`ns`a-2`n]'

title='zeta / sf.'
day=(it-1)*dt/60/24
dy=math_format( '%.3f', day)
'set string 1 bl 10 0'
'set strsiz 0.2'
'draw string 2.6875 8 'exp
'draw string 2.6875 7.65 'title

'set string 1 br 10 0'
'set strsiz 0.2'
'draw string 8.3125 8 'dy'days'
'draw string 8.3125 7.65 @'lev'km'

if ( mode="SAVEFIG" )
  itt=math_format( '%06.0f', it)
*  'gxprint 'outPath'/whi_cwv'type'_'itt'.png x2400 y1800 white'
  'gxprint 'outPath'/bla_vort'type'_'itt'.png x2400 y1800'
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

