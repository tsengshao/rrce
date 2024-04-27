function main(args)

vvmPath="/data/C.shaoyu/rrce/vvm/"
datPath="/data/C.shaoyu/rrce/data/"

nexp=5
expList='RRCE_3km_f00 RRCE_3km_f00_10 RRCE_3km_f00_20 RRCE_3km_f00_25 RRCE_3km_f00_30'
dtList='20 20 20 20 20'
tlastList='2881 1441 2880 1441 1441'
lcList='1 7 8 30 14'
'set rgb 30 255 85 33'
'set lwid 55 3'
TE=60
hashtag='re_'
klen='50km'

outPath="./fig/"
'! mkdir -p 'outPath

'reinit'
'c'
it=1
while(it<=nexp)
*  'open 'datPath'/series/'subwrd(expList,it)'.ctl'
  'open 'datPath'/series/conv_'subwrd(expList,it)'.ctl'
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
'set vrange 0 1'
i=1
while(i<=nexp)
*  if ( i>1 )
*    'off.gs'
*  endif
  'set cmark 0'
  'set ccolor 'subwrd(lcList,i)
  'set cthick 55'
  'd mzeta.'i'(ens='klen') * 1e3'
  i=i+1
endwhile
'on.gs'

'set cthick 55'
'legend tl 'nexp' 'expList' 'lcList''

*X Limits = 1.2 to 10.5
*Y Limits = 1 to 7.5

'set string 1 c 10'
'set strsiz 0.17'
'draw string 5.85 0.5 [days]'

'set string 1 c 10 90'
'set strsiz 0.17'
'draw string 0.4 4.25 [x10`a-3`n s`a-1`n]'

'set string 1 bl 10 0'
'set strsiz 0.2'
*'draw string 1.2 8 'exp
'draw string 1.2 7.65 maximum zeta @1.5km with 'klen' gaussian kernel'

'gxprint 'outPath'/'hashtag'con'klen'_zetamax.png x1600 y1200'
'gxprint 'outPath'/white/'hashtag'con'klen'_zetamax.png x1600 y1200 white'

exit
