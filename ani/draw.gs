function main(args)
iexp = subwrd(args,1)

vvmPath="/data/C.shaoyu/rrce/vvm/"
datPath="/data/C.shaoyu/rrce/data/"
expList='RCE_300K_3km_f05 RCE_300K_3km_f0 RRCE_3km_f00 RRCE_3km_f10 RRCE_3km_f15'
dtList='60 60 20 20 20'
tlastList='2030 2137 3654 2286 2161'


exp = subwrd(expList, iexp)
dt  = subwrd(dtList, iexp)
tlast = subwrd(tlastList, iexp)
say exp', 'dt', 'tlast

outPath="./fig/"exp
'! mkdir -p 'outPath

'reinit'
*'set background 1'
'c'
'open 'vvmPath'/'exp'/gs_ctl_files/Dynamic.ctl'
*'open 'datPath'/cwv/'exp'.ctl'
'open 'datPath'/wp/'exp'.ctl'

it = 1
while(it<=tlast)
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
'color 10 60 2 -kind white->wheat->darkcyan->darkblue->aqua -gxout grfill'
'd cwv.2(z=1)'
'xcbar 8.6 8.8 0.8 7.55 -ft 10 -fs 5'

'set gxout contour'
'set clevs 5 10'
'set ccols 15 12'
'set clab off'
'set cthick 5'
'd mag(u,v)'

'set clevs 18 33'
'set ccols 8 2'
'set clab off'
'set cthick 7'
'd mag(u,v)'

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
'draw string 2.6875 7.65 CWV[mm] / WS[ms`a-1`n]'

'set string 1 br 10 0'
'set strsiz 0.2'
'draw string 8.3125 7.65 'dy'days'
itt=math_format( '%06.0f', it)
'gxprint 'outPath'/cwvws_'itt'.png x2400 y1800 white'

it = it+1
endwhile


