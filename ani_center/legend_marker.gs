function legend_marker(args)
************************
frame=1
mg=0.01; h=0.4
*mg: distance between legend and margin
*h : hight of a line
************************
if(args='')
help()
return
endif

pos=subwrd(args,1);num=subwrd(args,2)
fth =subwrd(args,3);lw=subwrd(args,4)
say pos', num='num', fth='fth', lw='lw
*n=3;n2=n+num-1;ind=1
n=5;n2=n+num-1;ind=1
while(n<=n2);name.ind=subwrd(args,n);ind=ind+1;n=n+1;endwhile
n2=n+num-1;ind=1
while(n<=n2);color.ind=subwrd(args,n);ind=ind+1;n=n+1;endwhile
n2=n+num-1;ind=1
while(n<=n2);style.ind=subwrd(args,n);ind=ind+1;n=n+1;endwhile
n2=n+num-1;ind=1
while(n<=n2);mark.ind=subwrd(args,n);ind=ind+1;n=n+1;endwhile

n=1
long=0
'set strsiz 'h*0.382' 'h*0.427
while(n<=num)
'q string 'name.n
temp=subwrd(result,4)
if(temp>long);long=temp;endif
if(style.n='style.'n|style.n='');style.n=1;endif
if(mark.n='mark.'n|mark.n='');mark.n=0;endif
n=n+1
endwhile
*w=long+1
w=long+0.7

'q gxinfo'
xinfo=sublin(result,3)
yinfo=sublin(result,4)
xl=subwrd(xinfo,4)
xr=subwrd(xinfo,6)
yb=subwrd(yinfo,4)
yt=subwrd(yinfo,6)

if(pos=tl);xl=xl+mg;yt=yt-mg;xr=xl+w;yb=yt-num*h;endif
if(pos=tc);xl=(xl+xr)/2-w/2;yt=yt-mg;xr=xl+w;yb=yt-num*h;endif
if(pos=tr);xr=xr-mg;yt=yt-mg;xl=xr-w;yb=yt-num*h;endif
if(pos=l);xl=xl+mg;yt=(yt+yb)/2+h*num/2;xr=xl+w;yb=yt-num*h;endif
if(pos=c);xl=(xl+xr)/2-w/2;yt=(yt+yb)/2+h*num/2;xr=xl+w;yb=yt-num*h;endif
if(pos=r);xr=xr-mg;yt=(yt+yb)/2+h*num/2;xl=xr-w;yb=yt-num*h;endif
if(pos=bl);xl=xl+mg;yb=yb+mg;xr=xl+w;yt=yb+num*h;endif
if(pos=bc);xl=(xl+xr)/2-w/2;yb=yb+mg;xr=xl+w;yt=yb+num*h;endif
if(pos=br);xr=xr-mg;yb=yb+mg;xl=xr-w;yt=yb+num*h;endif

'set rgb 200 255 255 255 100'
'set line 200 1 5'
'draw recf 'xl' 'yb' 'xr' 'yt
if(frame);'set line 1';'draw rec 'xl' 'yb' 'xr' 'yt;endif
xr=xr-0.1
_wr=xl+long+0.1
_ll=_wr+0.1
n=1
while(n<=num)
_y.n=yt-h/2-(n-1)*h

if (mark.n=1 | mark.n=2 | mark.n=4 | mark.n=6 | mark.n=7 | mark.n=8)
  'set lwid 90 4'
  'set line 'color.n' 1 90'
  'draw mark 'mark.n' '%(_ll+xr)/2%' '_y.n' 0.2'
else
* white edge
  'set rgb 201 255 255 255'
  'set line 201'
  'draw mark 'mark.n' '%(_ll+xr)/2%' '_y.n' '0.2*1.5
  'set line 'color.n' 'style.n' 'lw
  'draw mark 'mark.n' '%(_ll+xr)/2%' '_y.n' 0.2'
endif

*'draw line '_ll' '_y.n' 'xr' '_y.n
'set string 1 r 'fth
'draw string '_wr' '_y.n' 'name.n
n=n+1
endwhile

return

function help()
say '** For legend.gs **'
say 'legend pos num fthickness lw string.1 ... string.num color.1 ... color.num [style.1 ... style.num [mark.1 ... mark.num]]'
say ''
say '** For legend.gsf **'
say 'rc = gsfallow("on")'
say 'rc = legend(pos,num,strings,colors,styles)'
say ''
say 'pos: position of legend, num: number of items'
say 'num: number of line'
say 'fthickness: font thickness'
say 'lw : line width'
say 'strings: ''name#1 name#2 ...'''
say 'colors: ''color#1 color#2 ...'''
say 'styles(optional): ''line_style#1 line_style#2 ...''(default=1)'
say '      tl        tc         tr          tl - top left'
say '       + ------- + ------- +           tc - top center'
say '       |                   |           tr - top right'
say '       |                   |           '
say '       |                   |           l - left'
say '       +l        +c       r+           c - center            '
say '       |                   |           r - right'
say '       |                   |'
say '       |                   |           bl - bottom left'
say '       + ------- + ------- +           bc - bottom center'
say '      bl         bc        br          br - bottom right'
return
