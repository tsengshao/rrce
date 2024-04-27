function main(args)
iexp = subwrd(args,1)
if (iexp = ''); iexp=4; endif

**default 
te='none'
ts='none'
*mode='SAVEFIG'
mode='PAUSE'
type='cwv'
type='czeta'
*type=cwv, sf, ws, czeta
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
tlastList='1441 2880 1441 1441 2881'


exp = subwrd(expList, iexp)
dt  = subwrd(dtList, iexp)
tlast = subwrd(tlastList, iexp)
sfctl = subwrd(sfCtlList, iexp)
sfen  = subwrd(enList, iexp)
say exp', 'dt', 'tlast', 'type

if (ts='none'); ts=1; endif
if (te='none'); te=tlast; endif
if (te>tlast);  te=tlast; endif

drawsf="FALSE"
drawdis="FALSE"
drawws="FALSE"
drawczeta="FALSE"
drawarr="FALSE"
if ( type = 'ws' )
  drawws="TRUE"
endif
if ( type = 'sf' )
  drawsf="TRUE"
  drawdis="TRUE"
endif
if ( type = 'czeta' )
  klen='25km'
  drawczeta="TRUE"
  drawarr="TRUE"
endif

outPath="./fig_"type"/"exp
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
say 'Czeta: 'drawczeta

say 'outpath='outPath
say '**********'
say ''
********************************

'reinit'
*'set background 1'
'c'
'open 'vvmPath'/'exp'/gs_ctl_files/Dynamic.ctl'
'open 'datPath'/wp/'exp'.ctl'
if ( type='sf')
  'open 'datPath'/horisf/'sfctl'_000.ctl'
  'open 'datPath'/distance/'exp'.ctl'
endif
if ( type='czeta' )
  'open 'datPath'/convolve/'exp'/convolve.ctl'
endif

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
*'color 10 60 2 -kind white->wheat->darkcyan->darkblue->aqua -gxout grfill'
'color 10 60 2 -kind white->wheat->darkcyan->darkblue->(4,130,191) -gxout grfill'
lnum=(60-10)/2+2+15
'set rgb 'lnum' 0 250 250'
'd cwv.2(z=1)'
'xcbar 8.6 8.8 0.8 7.55 -ft 10 -fs 5'

'set string 1 bl 10 0'
'set strsiz 0.2'
'draw string 8.55 8.0 CWV'
'draw string 8.55 7.65 [mm]'

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

if ( drawarr = "TRUE" )
  'set gxout vector'
  'set arrscl 0.5 20'
  'set arrowhead 0.1'
  'set cthick 8'
  'set rgb 80 180 180 180'
  'set ccolor 80'
  iz=12
  magv=3
  'define vv=maskout(v(z='iz'), mag(u(z='iz'),v(z='iz'))>='magv')'
  'd skip(u(z='iz'),10);vv'
endif

if ( drawczeta = "TRUE" )
*  'set lwid 50 2'
*  'set gxout contour'
*  'set clevs 5e-5'
*  'set rgb 20 200 200 200'
*  'set ccolor 20'
*  'set cthick 10'
*  'set clab off'
*  'd zeta.3(z=12)'

  'set lwid 50 3'
  'set gxout contour'
  'set clevs 1e-4 2e-4 3e-4'
  'set ccolor 8'
  'set cthick 50'
  'set clab off'
  'd zeta.3(z=12, ens='klen')'

  'set cmin 4e-4'
  'set cmax 1e-3'
  'set cint 1e-4'
  'set ccolor 2'
  'set cthick 50'
  'set clab off'
  'd zeta.3(z=12, ens='klen')'

  'set cmin 1e-3'
  'set cmax 1e2'
  'set cint 1e-4'
  'set ccolor 9'
  'set cthick 50'
  'set clab off'
  'd zeta.3(z=12, ens='klen')'

  'set lwid 80 2'
  'set rgb 83 0 0 0'
  'set string 83 tl 80 0'
  'set strsiz 0.1'
  'draw string 2.75 7.5 kernel:'klen

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
if ( drawws="TRUE" ); title.itit='WS[ms`a-1`n]'; itit=itit+1;endif
if ( drawsf="TRUE" ); title.itit='SF@Suf.[kg s`a-1`nm`a-1`n]'; itit=itit+1;endif
if ( drawczeta="TRUE" ); title.itit='cZeta@1.5km [s`a-1`n]'; itit=itit+1;endif
if ( drawarr="TRUE" ); title.itit='Wind@1.5km [ms`a-1`n]'; itit=itit+1;endif
itit = itit - 1

title=title.itit
itit = itit - 1
while(itit>=1)
title = title' / 'title.itit
itit = itit - 1
endwhile

if ( type = "czeta" )
title = 'conZeta[s`a-1`n]/Wind[ms`a-1`n] @1.5km'
endif

'draw string 2.6875 7.65 'title

'set string 1 br 10 0'
'set strsiz 0.2'
'draw string 8.3125 8 'dy'days'

if ( mode="SAVEFIG" )
  itt=math_format( '%06.0f', it)
*  'gxprint 'outPath'/whi_cwv'type'_'itt'.png x2400 y1800 white'
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

