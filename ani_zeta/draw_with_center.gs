function main(args) 

iexp = subwrd(args,1)
if (iexp = ''); iexp=19; endif

**default 
te='none'
ts='none'
*mode='SAVEFIG'
mode='PAUSE'
type='zeta'
zidx=5
kernel='0km'
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
    if( arg = '-kernel' ) ; kernel=subwrd(args,i) ; i=i+1 ; break ; endif
    say 'syntax error: 'arg
    return
  endwhile
endwhile

vvmPath="/data/C.shaoyu/rrce/vvm/"
datPath="/data/C.shaoyu/rrce/data/"


expList='f00 f10 f00_10 f00_15 f00_16 f00_17 f00_18 f00_19 f00_20 f00_21 f00_22 f00_23 f00_24 f00_25 f00_26 f00_27 f00_28 f00_29 f00_30'

exp = 'RRCE_3km_'subwrd(expList, iexp)
dt  = 20
if (iexp<=1)
  tlast = subwrd(tlastList, iexp)
  tlast = 2521
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

outPath='./fig_zeta_with_center/'exp
'! mkdir -p 'outPath

******** write the status *******
say ''
say '**********'
say 'drawing mode ... 'mode
say 'iexp='iexp', exp='exp', dt='dt
say 'ts='ts', te='te
say 'drawrain='drawrain
say 'height='zname' ( 'iz' )'
say 'kernel_size = 'kernel

say 'outpath='outPath
say '**********'
say ''
********************************

*../../data/find_center/czeta100km_domainmean/RRCE_3km_f00_30.txt
file = datPath'/find_center/czeta'kernel'_domainmean/'exp'.txt'
maxvalue = readfile(file, 'max_value')
maxcx = readfile(file, 'max_x')
maxcy = readfile(file, 'max_y')
meanvalue = readfile(file, 'mean_value')
meancx = readfile(file, 'mean_x')
meancy = readfile(file, 'mean_y')


'reinit'
*'set background 1'
'c'
'open 'vvmPath'/'exp'/gs_ctl_files/Dynamic.ctl'
'open 'vvmPath'/'exp'/gs_ctl_files/Thermodynamic.ctl'
'open 'vvmPath'/'exp'/gs_ctl_files/Surface.ctl'
'open 'datPath'/convolve/'exp'/convolve.ctl'
'open 'datPath'/horimsf/msf_'exp'.ctl'

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
scale = 1e5
'color -levs -100 -50 -30 -20 -10 -5 0 5 10 20 30 50 100 -gxout grfill'
if (kernel='0km')
  'define val=zeta.1'
else
  'define val=zeta.4(ens='kernel')'
endif
'd val*'scale
'xcbar 8.6 8.8 0.8 7.55 -ft 10 -fs 1'

*** draw cetner location **
value=subwrd(maxvalue,it)*scale
cx=subwrd(maxcx,it)
cy=subwrd(maxcy,it)
rc=drawpoint(value,cx,cy,'max')

value=subwrd(meanvalue,it)*scale
cx=subwrd(meancx,it)
cy=subwrd(meancy,it)
rc=drawpoint(value,cx,cy,'mean')

'set string 1 bl 10 0'
'set strsiz 0.2'

'set string 1 c 10'
'set strsiz 0.17'
'draw string 5.5 0.2 [km]'

'set string 1 c 10 90'
'set strsiz 0.17'
'draw string 1.7 4.375 [km]'

** 'set lwid 80 2'
** 'set strsiz 0.1'
** 'set rgb 83 0 0 0'
** 'set string 83 tl 80 0'
** 'draw string 2.75 7.5 black  : zeta ( 100km / 25km )'
** 'set rgb 83 100 100 100'
** 'draw string 2.75 7.3 grey  : hori. sf. [10`a5`n kg*m`a2`ns`a-2`n]'

title='zeta ['scale'`ns`a-1`n]'
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
  'gxprint 'outPath'/bla_'iz'_'kernel'_'itt'.png x2400 y1800'
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

*end main function
return

function drawpoint(value, cx, cy, name)
  'q gr2xy 'cx' 'cy''
  x=subwrd(result,3)
  y=subwrd(result,6)
  c=math_format('%.2f', value)
  'set line 40'
  'draw mark 6 'x' 'y' 0.10'
  'set string 40 bc 10'
  'set strsiz 0.15'
  'draw string 'x' 'y+0.15' 'name'('c')'
return 0

function readfile(file,name)
** read center file **
*file = datPath'/find_center/conzeta'contype'_max_'exp'.txt'
*say file
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

meanlist  = ''
meanxlist = ''
meanylist = ''

maxlist  = ''
maxxlist = ''
maxylist = ''

while (1)
  res = read(file)
  line1 = sublin(res,1)
  line2 = sublin(res,2)
  rc1 = subwrd(line1,1)
  if (rc1); break; endif

  cts = subwrd(line2,1)+1
  carea = subwrd(line2,4)
  if (carea>=0)
    meanlist   = meanlist' 'subwrd(line2,2)
    meanxlist   = meanxlist' 'subwrd(line2,5)+1
    meanylist   = meanylist' 'subwrd(line2,6)+1
    
    maxlist    = maxlist' 'subwrd(line2,3)
    maxxlist   = maxxlist' 'subwrd(line2,7)+1
    maxylist   = maxylist' 'subwrd(line2,8)+1

  else
    meanlist    =  meanlist' NaN'
    meanxlist   = meanxlist' NaN'
    meanylist   = meanylist' NaN'
    
    maxlist    =  maxlist' NaN'
    maxxlist   = maxxlist' NaN'
    maxylist   = maxylist' NaN'
  endif
*say cts' 'carea' 'cx.cts' 'cy.cts
endwhile
rc = close(file)

if (name='mean_value'); return meanlist; endif
if (name='mean_x'); return meanxlist; endif
if (name='mean_y'); return meanylist; endif

if (name='max_value'); return maxlist; endif
if (name='max_x'); return maxxlist; endif
if (name='max_y'); return maxylist; endif

return 

