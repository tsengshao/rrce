function main(args)
iexp = subwrd(args,1)
if (iexp = ''); iexp=4; endif

**default 
te='none'
ts='none'
*mode='SAVEFIG'
mode='PAUSE'
type='water'
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
dt  = 20

exp = 'RRCE_3km_'subwrd(expList, iexp)
if ( exp = 'RRCE_3km_f00' )
    tlast = subwrd(tlastList, iexp)
else
    tlast = 217
endif
say exp', 'dt', 'tlast', 'type

if (ts='none'); ts=1; endif
if (te='none'); te=tlast; endif
if (te>tlast);  te=tlast; endif

outPath='./fig_'type'/'exp
say outPath
'! mkdir -p 'outPath

******** write the status *******
say ''
say '**********'
say 'drawing mode ... 'mode
say 'iexp='iexp', exp='exp', dt='dt
say 'ts='ts', te='te

say 'outpath='outPath
say '**********'
say ''
********************************

'reinit'
*'set background 1'
'c'
'open 'datPath'/wp/'exp'.ctl'
'open 'vvmPath'/'exp'/gs_ctl_files/Surface.ctl'

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


***** draw cwv *****
'color 10 60 2 -kind white->wheat->darkcyan->darkblue->(4,130,191) -gxout grfill'
lnum=(60-10)/2+2+15
'set rgb 'lnum' 0 250 250'
'd cwv.1(z=1)'
*'xcbar 8.7 9.0 0.8 2.8 -ft 10 -fs 5'
*'xcbar 8.7 9.0 0.8 4.0 -ft 10 -fs 2'
'xcbar 8.7 9.0 0.8 7.55 -ft 10 -fs 5'

***** draw rain *****
'set clab off'
'set lwid 50 3'
'set cthick 50'
'set gxout contour'
'set clevs 1'
'set ccolor 2'
'd sprec.2(z=1)*3600'

***** draw olr *****
'color 100 220 10 -kind (255,255,255)-(0)->(255,255,255,0) -gxout shaded'
'd olr.2(z=1)'

***** draw text *****
'set string 1 bl 10 0'
'set strsiz 0.2'
'draw string 8.55 8.0 CWV'
'draw string 8.55 7.65 [mm]'

'set string 1 br 10 0'
'set strsiz 0.10'
'draw string 8.27 8 transpart white is OLR (100 to 220 W/m2)'

'set string 2 br 10 0'
'set strsiz 0.10'
'draw string 8.27 8.2 red line is rain > 1 mm/hr'

***** draw x/y label *****
'set string 1 c 10'
'set strsiz 0.17'
'draw string 5.5 0.2 [km]'

'set string 1 c 10 90'
'set strsiz 0.10'
'draw string 1.7 4.375 [km]'

***** draw  title (exp name and time) *****
day=(it-1)*dt/60/24
dy=math_format( '%.3f', day)

hour=(it-1)*dt/60
hr=math_format('%.1f', hour)

'set string 1 bl 10 0'
'set strsiz 0.2'
*'draw string 2.6875 8 'title
'draw string 2.6875 7.65 'exp

'set string 1 br 10 0'
'set strsiz 0.2'
if ( exp = 'RRCE_3km_f00' )
  'draw string 8.3125 7.65 'dy'days'
else
  'draw string 8.3125 7.65 'hr'hours'
endif

if ( mode="SAVEFIG" )
  itt=math_format( '%06.0f', it)
  'gxprint 'outPath'/whi_'type'_'itt'.png x2400 y1800 white'
  'gxprint 'outPath'/bla_'type'_'itt'.png x2400 y1800'
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

