function main(args)
iexp = subwrd(args,1)
if (iexp = ''); iexp=1; endif

**default 
te='none'
ts='none'
*mode='SAVEFIG'
mode='PAUSE'
type='sfrain'
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
*tlast = 217
if (iexp<=1)
  tlast = 2521
else
  tlast = 217
endif

sfen  = subwrd(enList, iexp)
say exp', 'dt', 'tlast', 'type

if (ts='none'); ts=1; endif
if (te='none'); te=tlast; endif
if (te>tlast);  te=tlast; endif

drawsf="FALSE"
drawrain="FALSE"
appendstr=''
if ( type = 'sfrain' )
  drawsf="TRUE"
  drawrain="TRUE"
  sfidz=9
  sfhei='0.952km'
endif

outPath='./fig_'type''appendstr'/'exp
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

** read center file **
file = datPath'/find_center/sf_largest_0_'exp'.txt'
** read center file **
i=1
while(i<=7)
  res = read(file)
  line1 = sublin(res,1)
  line2 = sublin(res,2)
  if (i=3)
    sfidz = subwrd(line2,6)+1
    sfhei = subwrd(line2,3)
    sfhei = sfhei'm'
    say 'draw 'sfhei'meter ( 'sfidz' )'
  endif
  i=i+1
endwhile

while (1)
  res = read(file)
  line1 = sublin(res,1)
  line2 = sublin(res,2)
  rc1 = subwrd(line1,1)
  if (rc1); break; endif

  cts = subwrd(line2,1)+1
  carea = subwrd(line2,3)
  if (carea>0)
    cx.cts  = subwrd(line2,5)+1
    cy.cts  = subwrd(line2,6)+1
  else
    cx.cts  = 'NaN'
    cy.cts  = 'NaN'
  endif
* say cts' 'cx.cts' 'cy.cts
endwhile
rc = close(file)

** get nx ny**
'q file 1'
line=sublin(result,5)
nx=subwrd(line,3)
ny=subwrd(line,6)
** get nx ny

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

***  check max value **
  'define rain=sprec.3*3600'
  'define sf=msf.5(z='sfidz')'
  'define psf=maskout(sf,sf>0)'
  'set x 1'
  'set y 1'
  'define maxrain=amax(rain,x=1,x='nx',y=1,y='ny')'
  'd maxrain'
  maxrain=subwrd(result,4)
  
  'define maxsf=amax(sf,x=1,x='nx',y=1,y='ny')'
  'd maxsf'
  maxsf=subwrd(result,4)

  'define maxsflocx=amaxlocx(sf,x=1,x='nx',y=1,y='ny')'
  'd maxsflocx'
  grx=subwrd(result,4)

  'define maxsflocy=amaxlocy(sf,x=1,x='nx',y=1,y='ny')'
  'd maxsflocy'
  gry=subwrd(result,4)
  say 'maxsf='maxsf', grx='grx', gry='gry

  'set x 1 'nx
  'set y 1 'ny
***  check max value **

'color 10 60 2 -kind white->wheat->darkcyan->darkblue->(4,130,191) -gxout grfill'
*'color 10 60 2.5 -kind white->wheat->darkcyan->darkblue -gxout grfill'
lnum=(60-10)/2+2+15
*'set rgb 'lnum' 0 250 250'
'd cwv.4(z=1)'
'xcbar 8.6 8.8 4 7.5 -ft 10 -fs 5'
*'xcbar 8.6 8.8 4 7.5 -ft 10 -fs 2'

'set string 1 bl 10 0'
'set strsiz 0.2'
'draw string 8.55 8.0 CWV'
'draw string 8.55 7.65 [mm]'

if ( drawrain="TRUE" )
  clevs='1 5 15 40'
  ckind='(255,255,255,0)->grainbow'
  ckind='white->plum->purple'
  'color -levs 'clevs' -gxout grfill -kind 'ckind' -xcbar 8.6 8.8 0.8 3.3 -ft 10'
  say 'maxrain = 'maxrain' mm/hr'
  if ( maxrain>1); 'd maskout(rain,rain-1)'; endif
  'set string 1 bl 10 0'
  'set strsiz 0.15'
  'draw string 8.55 3.4 Rain'
endif

if ( drawsf="TRUE" )
  'set lwid 50 2'
  'set cthick 50'
  c='(0,0,0)'
  'color 0.5 25 0.5 -gxout contour -kind 'c'->'c''
  'set clab masked'
  'd sf*1e-5'

  'set rgb 50 0 0 0'
  'set ccolor 50'
  'set clevs 0.1'
  'set clab masked'
  'd sf*1e-5'

  'set rgb 50 200 200 200'
  'set ccolor 50'
  'set clevs 0'
  'set clab masked'
  'd sf*1e-5'

  'q gr2xy 'grx' 'gry
  x=subwrd(result,3)
  y=subwrd(result,6)
  say 'maxsf='maxsf', (x,y)='x','y
  'set line 2'
  'draw mark 3 'x' 'y' 0.15'
  'set string 2 bc'
  'set strsiz 0.15'
  'draw string 'x' 'y+0.16' max'

  say 'mean sf loc, (x,y)='cx.it', 'cy.it
  if ( cx.it!='NaN' )
    'q gr2xy 'cx.it' 'cy.it''
    x=subwrd(result,3)
    y=subwrd(result,6)
    'set line 2'
    'draw mark 12 'x' 'y' 0.25'
    'set string 2 bc'
    'set strsiz 0.15'
    'draw string 'x' 'y+0.15' mean'
  else
    say 'mean sf loc, (x,y)='cx.it','cy.it
  endif

  'set lwid 80 2'
  'set rgb 83 0 0 0'
  'set string 83 tl 80 0'
  'set strsiz 0.1'
  'draw string 2.75 7.5 Stream Function @'sfhei' [10`a-5`n kg s`a-1`nm`a-1`n]'
endif

'set string 1 c 10'
'set strsiz 0.17'
'draw string 5.5 0.2 [km]'

'set string 1 c 10 90'
'set strsiz 0.17'
'draw string 1.7 4.375 [km]'

day=(it-1)*dt/60/24
dy=math_format( '%.3f', day)

hour=(it-1)*dt/60
hr=math_format('%.1f', hour)

'set string 1 bl 10 0'
'set strsiz 0.2'
'draw string 2.6875 8 'exp
itit=1
if ( drawsf="TRUE" ); title.itit='SF@'sfhei; itit=itit+1;endif
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
if ( RRCE_3km_f00=exp )
  'draw string 8.3125 8 'dy'days'
else
  'draw string 8.3125 8 'hr'hours'
endif

if ( mode="SAVEFIG" )
  itt=math_format( '%06.0f', it)
*  'gxprint 'outPath'/whi_sfrain_'itt'.png x2400 y1800 white'
  'gxprint 'outPath'/bla_sfrain_'itt'.png x2400 y1800'
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

