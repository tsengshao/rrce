function main(args)
iexp = subwrd(args,1)
if (iexp = ''); iexp=4; endif

**default 
te='none'
ts='none'
*mode='SAVEFIG'
mode='PAUSE'
type='olr'
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
expNameList='CTRL D00_on D10_on D15_on D16_on D17_on D18_on D19_on D20_on D21_on D22_on D23_on D24_on D25_on D26_on D27_on D28_on D29_on D30_on'

exp = 'RRCE_3km_'subwrd(expList, iexp)
explabel = subwrd(expNameList, iexp)
if ( exp = 'RRCE_3km_f00' )
*    tlast = subwrd(tlastList, iexp)
    tlast = 2520+1
else
    tlast = 217
endif
say explabel', 'exp', 'dt', 'tlast', 'type

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

'reinit'
'set background 1'
'c'
'open 'datPath'/wp/'exp'.ctl'
'open 'vvmPath'/'exp'/gs_ctl_files/Surface.ctl'

it = ts
while(it<=te)
say 't='it''
'c'
'set t 'it

'set lwid 77 10'
'set lwid 75 5'

'set parea 2.58333 8.41667 0.8 7.55'
'set xlopts 1 75 0.2'
'set ylopts 1 75 0.2'
'set grads off'
'set timelab off'
'set mpdraw off'
*'set xlabs 0|288|576|864|1152'
*'set ylabs 0|288|576|864|1152'
'set xlabs ||||'
'set ylabs ||||'

***** draw olr *****
'color 100 300 10 -kind white->black -gxout grfill'
if (exp='RRCE_3km_f00' & it=1)
'd max(max(olr.2(z=1,t=2),x=1,x=384),y=1,y=384)+lon*1e-10'
else
'd olr.2(z=1)'
endif

*'xcbar 8.7 9.0 0.8 7.55 -ft 75 -fs 2'

***** draw cwv *****
'set gxout contour'
'set cmin 10'
'set cmax 80'
'set cint 10'
*'set cthick 13'
'set clab off'
'set rgb 80 137 38 36'
'set ccolor 80'
*'d cwv.1'

***** get fig x/y ****
'q gxinfo'
linex=sublin(result,3)
x1=subwrd(linex,4)
x2=subwrd(linex,6)
liney=sublin(result,4)
y1=subwrd(liney,4)
y2=subwrd(liney,6)
w=x2-x1
h=y2-y1

*-- draw colorbar for  previous variables --*
a1=x2+0.5
a2=a1+0.2
b1=y1+h/2
b2=b1+h*4/10
'xcbar 'a1' 'a2' 'b1' 'b2' -ft 75 -fs 5'
'set string 1 bl 77 0'
'set strsiz 0.15'
'draw string 'a1' 'b2+0.2' OLR [W/m`a-2`n]'

***** draw rain *****
if(it>1)
clevs='1 3 5 7 10 15 30 50'
'color -levs 'clevs' -gxout grfill -kind (0,0,0,0)-(0)->(157,193,220,255)->(38,69,134)'
'define rain=sprec.2*3600'
'd maskout(rain,rain-1)'
a1=x2+0.5
a2=a1+0.2
b1=y1
b2=b1+h*4/10
'xcbar 'a1' 'a2' 'b1' 'b2' -ft 75'
'set string 1 bl 77 0'
'set strsiz 0.15'
'draw string 'a1' 'b2+0.2' Rain [mm/hr]'
endif

* ***** draw x/y label *****
* 'set string 1 c 75'
* 'set strsiz 0.17'
* 'draw string 5.5 0.2 [km]'
* 
* 'set string 1 c 75 90'
* 'set strsiz 0.17'
* 'draw string 1.7 4.375 [km]'

***** draw  title (exp name and time) *****
day=(it-1)*dt/60/24
dy=math_format( '%.3f', day)
dy00=math_format( '%.0f', day)
if ( day = dy00 ); dy=dy00; endif

hour=(it-1)*dt/60
hr=math_format('%.1f', hour)
hr00=math_format( '%.0f', hour)
if ( hour = hr00 ); hr=hr00; endif

'set string 1 bl 77 0'
'set strsiz 0.25'
*'draw string 2.6875 7.65 'explabel
'draw string 'x1' 'y2+0.2' 'explabel


'set string 1 br 77 0'
'set strsiz 0.25'
if ( exp = 'RRCE_3km_f00' )
*  'draw string 8.3125 7.65 'dy'days'
  'draw string 'x2' 'y2+0.2' 'dy'days'
else
*  'draw string 8.3125 7.65 'hr'hours'
  'draw string 'x2' 'y2+0.2' 'hr'hours'
endif

if ( mode="SAVEFIG" )
  itt=math_format( '%06.0f', it)
  'gxprint 'outPath'/whi_'type'_'itt'.png x3300 y2550 white'
*  'gxprint 'outPath'/bla_'type'_'itt'.png x2400 y1800'
  it = it+72
endif

if ( mode="PAUSE")
  te=tlast
  pull step
  if(step='q'|step='quit'|step='exit');exit;endif
*  if(step='');it=it+1;continue;else
  if(step='');it=it+72;continue;else
    rc=valnum(step)
    if(rc=0);step;pull step;endif
    if(rc=1&step>0);it=step;endif
  endif
endif

endwhile

*end main function
return

