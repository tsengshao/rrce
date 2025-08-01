** grads -a 1 
'reinit'
'set background 1'
'c'
exp='ctrl'
exp='d30on'
exp='d20on'
'open ./gs_ctl_files_'exp'/cwv.ctl'

'set lwid 77 10'
'set lwid 75 5'

'set parea 0.1 10.9 0.2 10.8'
'set xlopts 1 75 0.2'
'set ylopts 1 75 0.2'
'set grads off'
'set timelab off'
'set mpdraw off'
*'set xlabs 0|288|576|864|1152'
*'set ylabs 0|288|576|864|1152'
'set xlabs ||||'
'set ylabs ||||'

dt  = 20
it=2161
it=1441
it=217
'set t 'it

***** draw cwv *****
'color 10 60 2 -kind white->wheat->darkcyan->darkblue->(4,130,191) -gxout grfill'
lnum=(60-10)/2+2+15
'set rgb 'lnum' 0 250 250'
if (exp='RRCE_3km_f00' & it=1)
'd cwv.1(z=1)+lon*1e-10'
else
'd cwv.1(z=1)'
endif

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
say x1' 'x2' 'y1' 'y2

*-- draw colorbar for  previous variables --*
a1=x2+0.5
a2=a1+0.2
b1=y1+h/2
b2=b1+h*4/10
'xcbar 'a1' 'a2' 'b1' 'b2' -ft 75 -fs 5'
'set string 1 bl 77 0'
'set strsiz 0.15'
'draw string 'a1' 'b2+0.2' CWV[mm]'

***** draw  title (exp name and time) *****
day=(it-1)*dt/60/24
dy=math_format( '%.3f', day)
dy00=math_format( '%.0f', day)
if ( day = dy00 ); dy=dy00; endif

hour=(it-1)*dt/60
hr=math_format('%.1f', hour)
hr00=math_format( '%.0f', hour)
if ( hour = hr00 ); hr=hr00; endif

say day' 'hour

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

itt=math_format( '%06.0f', it)
'gxprint ./cwv_'exp'_'itt'.png x3300 y3100 white'

