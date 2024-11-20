'reinit'
'open /data/C.shaoyu/rrce/data/axisy/czeta0km_positivemean/axmean_rcemip_mg_square_diag2.ctl'

'set x 1 30'
'set lev 1 12000'
'set xlabs 0km|30km|60km|90km'

nt=216
it=1
say 'please intput timestep to draw ... from 'it' to 'nt''
pull it
'set t 'it

*draw pv
'c'
'color -15 15 2'
'd pv*1e6'
'cbar'
'draw title PV [PVU] (t='it')'

*draw total ADV
say 'press to continue ...'
pull x
'c'
'color -1 1'
'd totadv/10*1e6*1e2'
'cbar'
'draw title total ADV [0.01*PVU/s] (t='it')'

*draw total diabatic
say 'press to continue ...'
pull x
'c'
'color -1 1'
'd (zetadia+xidia+etadia)*1e6*1e2'
'cbar'
'draw title total DIA [0.01*PVU/s] (t='it')'

exit

* say 'inquary timestep or quit(q) ... '
* pull step
* if(step='q'|step='quit'|step='exit');exit;endif
* if(step='');it=it+1;continue;else
*   rc=valnum(step)
*   if(rc=0);step;pull step;endif
*   if(rc=1&step>0);it=step;endif
* endif
* 
* endwhile


