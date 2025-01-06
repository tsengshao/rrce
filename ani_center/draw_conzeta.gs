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
kernel='150km'
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
expNameList='D00_off D00_on D10_on D15_on D16_on D17_on D18_on D19_on D20_on D21_on D22_on D23_on D24_on D25_on D26_on D27_on D28_on D29_on D30_on'

exp = 'RRCE_3km_'subwrd(expList, iexp)
explabel = subwrd(expNameList, iexp)
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

outPath='./whi_fig_conzeta/'exp
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

** prepare center location **
*../../data/find_center/czeta0km_positivemean/RRCE_3km_f00.txt
file = datPath'/find_center/czeta0km_positivemean/'exp'.txt'
meancx = readfile(file, 'mean_x')
meancy = readfile(file, 'mean_y')
maxcx = readfile(file, 'max_x')
maxcy = readfile(file, 'max_y')

file = datPath'/find_center/czeta0km_allmean/'exp'.txt'
allmeancx = readfile(file, 'mean_x')
allmeancy = readfile(file, 'mean_y')

file = datPath'/find_center/czeta'kernel'_positivemean/'exp'.txt'
conmaxcx = readfile(file, 'max_x')
conmaxcy = readfile(file, 'max_y')

file = datPath'/find_center/sf_positivemean/'exp'.txt'
sfmaxcx = readfile(file, 'max_x')
sfmaxcy = readfile(file, 'max_y')


'reinit'
'set background 1'
'c'
'open 'vvmPath'/'exp'/gs_ctl_files/Dynamic.ctl'
'open 'datPath'horimsf/msf_'exp'.ctl'
* ens 150km(e=1), 100km(e=2), 50km(e=3), 25km(e=4)
'open 'datPath'/convolve/'exp'/convolve.ctl'

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
*'define val=zeta.1'
'define val=zeta.3(ens='kernel')'
'd val*'scale
'xcbar 8.7 9.0 0.8 7.55 -ft 10 -fs 1'

'set gxout contour'
'set cmin -10'
'set cint  1'
'set clab off'
'd msf.2/1e5'

'set clab masked'
'set cthick 5'
'set clevs 0'
'set ccolor 1'
'd msf.2/1e5'

***** draw center point *****
*green
'set rgb 40 67 100 0'
*orange
'set rgb 41 230 140 0'

cx=subwrd(maxcx,it)
cy=subwrd(maxcy,it)
rc=drawpoint(0,cx,cy,'max_zeta', 5, 40)

cx=subwrd(conmaxcx,it)
cy=subwrd(conmaxcy,it)
rc=drawpoint(0,cx,cy,'max_zetaCON150km', 12, 40)

cx=subwrd(sfmaxcx,it)
cy=subwrd(sfmaxcy,it)
rc=drawpoint(0,cx,cy,'max_sf', 3, 40)

cx=subwrd(meancx,it)
cy=subwrd(meancy,it)
rc=drawpoint(0,cx,cy,'mean_zeta', 9, 40)

cx=subwrd(allmeancx,it)
cy=subwrd(allmeancy,it)
rc=drawpoint(0,cx,cy,'mean_all_zeta', 8, 41)

*rc=drawlegend(4,'a b c d', '9 5 3 12')
style='1 1 1 1 1'
name='positive_zeta_centorid all_zeta_centroid zeta_max con'kernel'_zeta_max stream_func_max'
color='40 41 40 40 40'
mark='9 8 5 12 3'
'legend_marker br 5 10 1 'name' 'color' 'style' 'mark''

***** draw text *****
title='zeta ['scale'`ns`a-1`n]'
'set string 1 bl 10 0'
'set strsiz 0.15'
'draw string 8.68 8.05 zeta-con'kernel
'draw string 8.68 7.7 ['scale'`ns`a-1`n]'

'set string 1 br 10 0'
'set strsiz 0.17'
'draw string 8.27 7.98 @'zname

'set string 1 br 10 0'
'set strsiz 0.13'
'draw string 8.27 8.3 horizontal sf. interval 10`a5`n [kg*m`a2`ns`a-2`n]'

***** draw x/y label *****
'set string 1 c 10'
'set strsiz 0.17'
'draw string 5.5 0.2 [km]'

'set string 1 c 10 90'
'set strsiz 0.17'
'draw string 1.7 4.375 [km]'

***** draw  title (exp name and time) *****
day=(it-1)*dt/60/24
dy=math_format( '%.3f', day)
dy00=math_format( '%.0f', day)
if ( day = dy00 ); dy=dy00; endif

hour=(it-1)*dt/60
hr=math_format('%.1f', hour)
hr00=math_format( '%.0f', hour)
if ( hour = hr00 ); hr=hr00; endif

'set lwid 30 3'
'set string 1 bl 30 0'
'set strsiz 0.25'
'draw string 2.6875 7.65 'explabel

'set string 1 br 30 0'
'set strsiz 0.25'
if ( exp = 'RRCE_3km_f00' )
  'draw string 8.3125 7.65 'dy'days'
else
  'draw string 8.3125 7.65 'hr'hours'
endif

if ( mode="SAVEFIG" )
  itt=math_format( '%06.0f', it)
 'gxprint 'outPath'/conzeta_'iz'_'kernel'_'itt'.png x2400 y1800'
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

function drawlegend(n,name,style)
  'q gxinfo'
  lin = sublin(result, 3)
  xhi = subwrd(lin, 6)
  lin = sublin(result, 4)
  ylo = subwrd(lin, 4)
  fh   = 0.2
  xwei = 0.3
  yhei = (fh+0.1)*n
  xlo = xhi - xwei
  yhi = ylo + yhei
  
  'set rgb 40 255 255 255 100'
  'set line 40'
  'draw recf 'xlo' 'ylo' 'xhi' 'yhi''
  'set line 1'
  'draw rec 'xlo' 'ylo' 'xhi' 'yhi''


* end drawlegend
return

function drawpoint(value, cx, cy, name, style, color)
  'q gr2xy 'cx' 'cy''
  x=subwrd(result,3)
  y=subwrd(result,6)
  c=math_format('%.2f', value)
  if (style=5 | style=3)
    size=0.15
  else
    size=0.2
  endif

  if (style=8)
    'set lwid 90 4'
    'set line 'color' 1 90'
    'draw mark 'style' 'x' 'y' 'size
  else
    'set rgb 105 255 255 255'
    'set line 105'
    'draw mark 'style' 'x' 'y' 'size*1.5
    'set line 'color
    'draw mark 'style' 'x' 'y' 'size
  endif
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
*  say cts', 'subwrd(line2,5)', 'subwrd(line2,6)
endwhile
rc = close(file)

if (name='mean_value'); return meanlist; endif
if (name='mean_x'); return meanxlist; endif
if (name='mean_y'); return meanylist; endif

if (name='max_value'); return maxlist; endif
if (name='max_x'); return maxxlist; endif
if (name='max_y'); return maxylist; endif

return 
