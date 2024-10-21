'reinit'
exp  = RRCE_3km_f00_20
flag = '_ano'
flag = ''
'open /data/C.shaoyu/rrce/data/axisy/czeta0km_positivemean/axmean'flag'_'exp'.ctl'
it=216
var='CWV'

'set z 1'
'set t 'it
'set parea 1 10 1 4'
'set xlabs 0|144|288|432|576'
'set vrange 0 1'
'd 'var'(e=2)'
'draw xlab km'
'draw ylab axisymmetricity'

'set parea 1 10 4.5 7.5'
'set xlabs 0|144|288|432|576'
if ( flag = '_ano' ); 'set vrange -25 25'; endif
if ( flag = '' ); 'set vrange 10 60'; endif
'd 'var
'draw ylab 'var''flag''

'draw title 'var''flag' / 'exp' it='it
