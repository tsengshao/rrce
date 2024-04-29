function main(args)

vvmPath="/data/C.shaoyu/rrce/vvm/"
datPath="/data/C.shaoyu/rrce/data/"

nexp=7
expList='RCE_300K_3km_f0 RCE_300K_3km_f05 RRCE_3km_f00 RRCE_3km_f05 RRCE_3km_f10 RRCE_3km_f15 RRCE_3km_f20'
dtList='60 60 20 20 20 20 20'
tlastList='2137 2030 3654 2765 2286 2161 2138'
lcList='11 4 1 7 8 30 14'
'set rgb 30 255 85 33'
'set lwid 55 5'
TE=40
hashtag=''

nexp=5
expList='RRCE_3km_f00 RRCE_3km_f00_10 RRCE_3km_f00_20 RRCE_3km_f00_25 RRCE_3km_f00_30'
dtList='20 20 20 20 20'
tlastList='2881 1441 2880 1441 1441'
lcList='1 7 8 30 14'
'set rgb 30 255 85 33'
'set lwid 55 5'
TE=60
hashtag='re_'

outPath="./fig/"
'! mkdir -p 'outPath

'reinit'
'c'
it=1
while(it<=nexp)
* 'open 'datPath'/series/'subwrd(expList,it)'.ctl'
  'open 'datPath'/series/series_'subwrd(expList,it)'.ctl'
  it=it+1
endwhile

dt=subwrd(dtList,1)
idxTS=1
idxTE=math_format('%.0f', TE*24*60/dt+1)
'set t 1 'idxTE
'set xlabs 0||'TE/4'||'TE/2'||'TE*0.75'||'TE

'set parea 1.2 10.5 1 7.5'
'set xlopts 1 10 0.2'
'set ylopts 1 10 0.2'
'set grads off'
'set timelab off'
'set vrange -1 80'
i=1
while(i<=nexp)
  if ( i>1 )
    'off.gs'
  endif
  'set cmark 0'
  'set ccolor 'subwrd(lcList,i)
  'set cthick 55'
  'd 100*dryf.'i''
  i=i+1
endwhile
'on.gs'

'set cthick 55'
'legend tl 'nexp' 10 55 'expList' 'lcList''

*X Limits = 1.2 to 10.5
*Y Limits = 1 to 7.5

'set string 1 c 10'
'set strsiz 0.17'
'draw string 5.85 0.5 [days]'

'set string 1 c 10 90'
'set strsiz 0.17'
'draw string 0.4 4.25 [%]'

'set string 1 bl 10 0'
'set strsiz 0.2'
*'draw string 1.2 8 'exp
'draw string 1.2 7.65 dry frac. [cwv<30mm]'

'gxprint 'outPath'/'hashtag'dryfrac.png x1600 y1200'
'gxprint 'outPath'/white/'hashtag'dryfrac.png x1600 y1200 white'

exit
