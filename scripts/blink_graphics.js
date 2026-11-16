#!/usr/bin/env node
// Grafik animasi (canvas, deterministik) untuk video "kelip mata".
// Guna: node blink_graphics.js <outDir> <fStart> <fEnd>
// Hasil: <outDir>/back/%05d.png (di belakang orang) & <outDir>/front/%05d.png (kapsyen)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const [outDir, f0, f1] = [process.argv[2], +process.argv[3], +process.argv[4]];
const FPS = 30;

const PAGE = `<html><body style="margin:0;background:transparent">
<canvas id=b width=1080 height=1920></canvas><canvas id=f width=1080 height=1920></canvas>
<script>
const W=1080,H=1920;
const B=document.getElementById('b').getContext('2d'), F=document.getElementById('f').getContext('2d');
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const P=(t,a,d)=>clamp((t-a)/d);
const E={out:t=>1-Math.pow(1-t,3),inOut:t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2,
 back:t=>{const c1=1.70158,c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2)},
 elastic:t=>t==0?0:t==1?1:Math.pow(2,-10*t)*Math.sin((t*10-.75)*(2*Math.PI)/3)+1,
 lin:t=>t};
const lerp=(a,b,k)=>a+(b-a)*k;
const FONT='Inter, "Inter Display", sans-serif';
// visibility window -> {a: alpha, s: scale, k: in-progress}
function vis(t,a,b,din=.35,dout=.25){const i=E.back(P(t,a,din)),o=1-E.out(P(t,b,dout));
  return {a:clamp(P(t,a,din*.6))*o,s:Math.max(.001,i)*(0.85+0.15*o),k:i,on:t>=a&&t<b+dout};}
function txt(c,s,x,y,size,fill,o={}){c.save();c.font=(o.w||900)+' '+size+'px '+FONT;c.textAlign=o.al||'center';c.textBaseline='middle';
  if(o.rot)c.rotate(o.rot);
  if(o.glow){c.shadowColor=o.glow;c.shadowBlur=o.gb||40;}
  if(o.stroke){c.lineJoin='round';c.lineWidth=o.sw||10;c.strokeStyle=o.stroke;c.strokeText(s,x,y);}
  c.fillStyle=fill;c.fillText(s,x,y);c.restore();}
function rr(c,x,y,w,h,r){c.beginPath();c.moveTo(x+r,y);c.arcTo(x+w,y,x+w,y+h,r);c.arcTo(x+w,y+h,x,y+h,r);c.arcTo(x,y+h,x,y,r);c.arcTo(x,y,x+w,y,r);c.closePath();}
function withT(c,x,y,s,a,fn,rot=0){if(a<=0.003)return;c.save();c.globalAlpha*=a;c.translate(x,y);if(rot)c.rotate(rot);c.scale(s,s);fn();c.restore();}

// ---------- mata ----------
function blinkOpen(t,list){let o=1;for(const [t0,d] of list){if(t>t0&&t<t0+d){const p=(t-t0)/d;o=Math.min(o,1-Math.sin(Math.PI*p)*0.97);}}return o;}
function eye(c,cx,cy,w,open,opt={}){
  const h=w*.34*Math.max(open,.02);const red=opt.red||0,look=opt.look||[0,0];
  c.save();c.translate(cx,cy);
  const path=()=>{c.beginPath();c.moveTo(-w/2,0);c.bezierCurveTo(-w*.25,-h*1.45,w*.25,-h*1.45,w/2,0);c.bezierCurveTo(w*.25,h*1.45,-w*.25,h*1.45,-w/2,0);c.closePath();};
  c.shadowColor=opt.glow||'rgba(80,200,255,.7)';c.shadowBlur=w*.18;path();c.fillStyle='#fff';c.fill();c.shadowBlur=0;
  c.save();path();c.clip();
  let g=c.createLinearGradient(0,-h,0,h);g.fillStyle;g.addColorStop(0,'#e9eef5');g.addColorStop(1,'#ffffff');c.fillStyle=g;c.fillRect(-w,-h*2,w*2,h*4);
  if(red>0){c.fillStyle='rgba(255,50,50,'+(red*.45)+')';c.fillRect(-w,-h*2,w*2,h*4);
    c.strokeStyle='rgba(220,20,30,'+(red*.9)+')';c.lineWidth=w*.008;
    for(let i=0;i<14;i++){const sd=i%2?1:-1,y0=(i/14-.5)*h*1.2;c.beginPath();c.moveTo(sd*w/2,y0*.3);
      c.bezierCurveTo(sd*w*.38,y0,sd*w*.3,y0*.4+Math.sin(i*7)*h*.2,sd*(w*.14+(i%3)*w*.02),y0*.35);c.stroke();}}
  const ix=look[0]*w*.07,iy=look[1]*h*.2,r=w*.205;
  let ig=c.createRadialGradient(ix,iy,r*.2,ix,iy,r);ig.addColorStop(0,opt.iris2||'#1b7fbf');ig.addColorStop(.7,opt.iris||'#35c3ff');ig.addColorStop(1,'#0d3b66');
  c.beginPath();c.arc(ix,iy,r,0,7);c.fillStyle=ig;c.fill();
  c.beginPath();c.arc(ix,iy,r*.42,0,7);c.fillStyle='#061426';c.fill();
  c.beginPath();c.arc(ix-r*.3,iy-r*.3,r*.18,0,7);c.fillStyle='rgba(255,255,255,.95)';c.fill();
  c.restore();
  path();c.lineWidth=w*.03;c.strokeStyle=opt.line||'#0b2a4a';c.lineJoin='round';c.stroke();
  if(open<.5){c.lineCap='round';c.strokeStyle=opt.line||'#0b2a4a';c.lineWidth=w*.02;
    for(let i=-3;i<=3;i++){const x=i*w*.12;c.beginPath();c.moveTo(x,h*.4);c.lineTo(x*1.06,h*.4+w*.05*(1-open*2));c.stroke();}}
  c.restore();}

// ---------- mood / warna latar ----------
const MOODS=[ // t, r,g,b, alpha
 [0,10,30,70,.50],[3.12,6,70,60,.50],[6.8,60,12,28,.55],[13.3,85,28,10,.52],[19.3,60,6,10,.62],[23.9,12,34,90,.52],[28.9,8,86,86,.42],[36,60,30,110,.46],[39.2,10,30,70,.4]];
function mood(t){for(let i=0;i<MOODS.length-1;i++){const a=MOODS[i],b=MOODS[i+1];if(t<=b[0]||i==MOODS.length-2){const k=E.inOut(P(t,b[0]-.6,.6));return a.slice(1).map((v,j)=>lerp(v,b[j+1],k));}}}
function backdrop(c,t){
  const [r,g,b,a]=mood(t);
  let gr=c.createRadialGradient(W/2,640,200,W/2,640,1250);
  gr.addColorStop(0,'rgba('+r+','+g+','+b+','+(a*.55)+')');gr.addColorStop(1,'rgba('+(r*.5|0)+','+(g*.5|0)+','+(b*.5|0)+','+Math.min(.85,a*1.45)+')');
  c.fillStyle=gr;c.fillRect(0,0,W,H);
  // heartbeat vignette (scene 5)
  const hv=P(t,19.3,.4)*(1-P(t,23.7,.4));
  if(hv>0){const ph=((t-19.3)%1.1)/1.1;const beat=Math.exp(-ph*7)+.6*Math.exp(-Math.pow((ph-.22)*8,2)*3);
    let v=c.createRadialGradient(W/2,800,350,W/2,800,1300);v.addColorStop(0,'rgba(255,0,20,0)');v.addColorStop(1,'rgba(255,0,20,'+(hv*(.25+.5*beat))+')');c.fillStyle=v;c.fillRect(0,0,W,H);}
  // flash impact 10.76
  const fl=Math.exp(-(t-10.76)*14);if(t>=10.76&&fl>.02){c.fillStyle='rgba(255,70,70,'+(fl*.55)+')';c.fillRect(0,0,W,H);}
  // light sweep on transitions
  for(const tt of [3.12,6.8,13.3,19.3,23.9,28.9]){const d=t-tt;if(d>=0&&d<.55){const x=lerp(-300,W+300,E.out(d/.55));let l=c.createLinearGradient(x-220,0,x+220,0);
    l.addColorStop(0,'rgba(255,255,255,0)');l.addColorStop(.5,'rgba(255,255,255,'+(.28*(1-d/.55))+')');l.addColorStop(1,'rgba(255,255,255,0)');c.fillStyle=l;c.fillRect(0,0,W,H);}}
}
// partikel halus sepanjang video
function particles(c,t,col,n,speed,alpha){c.save();for(let i=0;i<n;i++){const sd=i*97.13;const x=(Math.sin(sd)*.5+.5)*W;const per=H+200;
  const y=H+100-((t*speed*(0.6+((i*37)%10)/12)+(i*211)%per)%per);const r=3+((i*13)%9);c.globalAlpha=alpha*(.4+.6*Math.abs(Math.sin(t*1.3+i)));c.fillStyle=col;c.beginPath();c.arc(x+Math.sin(t*.8+i)*30,y,r,0,7);c.fill();}c.restore();}
function ring(c,x,y,r,col,lw,a){c.save();c.globalAlpha*=a;c.strokeStyle=col;c.lineWidth=lw;c.beginPath();c.arc(x,y,r,0,7);c.stroke();c.restore();}
function burst(c,x,y,t0,t,col,R=220){const d=t-t0;if(d<0||d>.7)return;const k=E.out(d/.7);ring(c,x,y,R*k,col,14*(1-k)+2,1-k);ring(c,x,y,R*.6*k,col,8*(1-k)+1,(1-k)*.7);}
function pill(c,x,y,w,h,fill,text,size,tc='#fff',icon){c.save();c.shadowColor=fill;c.shadowBlur=36;rr(c,x-w/2,y-h/2,w,h,h/2);c.fillStyle=fill;c.fill();c.shadowBlur=0;
  txt(c,text,x+(icon?h*.25:0),y+2,size,tc);c.restore();}
function sparkle(c,x,y,r,col,rot=0){c.save();c.translate(x,y);c.rotate(rot);c.fillStyle=col;c.beginPath();for(let i=0;i<8;i++){const a=i*Math.PI/4,rr_=i%2?r*.22:r;c.lineTo(Math.cos(a)*rr_,Math.sin(a)*rr_);}c.closePath();c.fill();c.restore();}
function heart(c,x,y,s,col){c.save();c.translate(x,y);c.scale(s,s);c.fillStyle=col;c.beginPath();c.moveTo(0,.35);c.bezierCurveTo(-1,-.3,-.5,-1,0,-.45);c.bezierCurveTo(.5,-1,1,-.3,0,.35);c.fill();c.restore();}

// ---------- adegan (lapisan belakang) ----------
function back(c,t){
  c.clearRect(0,0,W,H);backdrop(c,t);
  particles(c,t,t<28.9?'rgba(255,255,255,.55)':'rgba(190,255,245,.7)',t<28.9?14:30,t<28.9?45:70,.35);

  // S1 hook
  {const v=vis(t,.05,2.95,.5,.3);
   withT(c,540,175,v.s,v.a,()=>{c.translate(0,Math.sin(t*2)*6);eye(c,0,0,560,blinkOpen(t,[[1.0,.3],[1.45,.3]]),{look:[Math.sin(t*2.2),Math.sin(t*1.5)*.5]});});
   const q=vis(t,.6,2.95,.4,.25);
   withT(c,150,560+Math.sin(t*2.5)*14,q.s,q.a,()=>txt(c,'?',0,0,240,'#ffd23f',{glow:'#ff9f1c',stroke:'#08203a',sw:14}),-.2);
   withT(c,930,640+Math.cos(t*2.1)*12,vis(t,.9,2.95).s,vis(t,.9,2.95).a,()=>txt(c,'?',0,0,170,'#7ee0ff',{glow:'#2aa8ff',stroke:'#08203a',sw:12}),.25);
   const cl=vis(t,2.0,3.0,.35,.2); // jam 60s
   withT(c,905,470,cl.s,cl.a,()=>{c.beginPath();c.arc(0,0,105,0,7);c.fillStyle='rgba(8,32,58,.85)';c.fill();ring(c,0,0,105,'#7ee0ff',9,1);
     const ang=-Math.PI/2+E.inOut(P(t,2.1,.85))*Math.PI*2;c.strokeStyle='#ffd23f';c.lineWidth=10;c.lineCap='round';c.beginPath();c.moveTo(0,0);c.lineTo(Math.cos(ang)*78,Math.sin(ang)*78);c.stroke();
     txt(c,'1 MIN',0,40,26,'#fff',{w:800});});}

  // S2 normal 18
  {const vb=vis(t,3.2,6.85,.4,.3);
   withT(c,540,95,vb.s,vb.a,()=>pill(c,0,0,430,86,'#16c784','NORMAL',46));
   const vn=vis(t,4.0,6.85,.45,.35);
   const cnt=Math.round(18*E.out(P(t,4.3,1.1)));const land=P(t,5.4,.5);const pop=1+.14*Math.sin(Math.PI*land)*(t>5.4?1:0);
   withT(c,470,320,vn.s*pop,vn.a,()=>txt(c,String(cnt),0,0,440,'#ffffff',{glow:'#16c784',gb:70,stroke:'#0a5a45',sw:22}));
   withT(c,860,300,vn.s,vn.a,()=>{txt(c,'KALI',0,-40,74,'#b8ffe6',{stroke:'#0a5a45',sw:12});txt(c,'/ MINIT',0,40,62,'#16c784',{stroke:'#06382c',sw:10});});
   burst(c,470,320,5.4,t,'#16c784',300);
   // jam tick: titik berdenyut ikut kiraan
   const ticks=Math.floor(P(t,4.3,1.1)*18);for(let i=0;i<18;i++){const on=i<ticks;withT(c,160+i*43,470-(i%2)*0,vn.s,vn.a*.8,()=>{c.beginPath();c.arc(0,0,on?10:6,0,7);c.fillStyle=on?'#16c784':'rgba(255,255,255,.35)';c.fill();});}}

  // S3 kajian / phone / 3-4
  {const vk=vis(t,7.65,9.15,.35,.25);
   withT(c,540,115,vk.s,vk.a,()=>pill(c,0,0,420,90,'#3a86ff','KAJIAN',48));
   const vp=vis(t,9.15,10.7,.4,.08);
   withT(c,540,200,vp.s,vp.a,()=>{c.shadowColor='#5ab0ff';c.shadowBlur=60;rr(c,-80,-135,160,270,26);c.fillStyle='#0a1d33';c.fill();c.lineWidth=8;c.strokeStyle='#cfe8ff';c.stroke();c.shadowBlur=0;
     rr(c,-64,-115,128,230,14);c.fillStyle='#2f7bff';c.fill();c.save();rr(c,-64,-115,128,230,14);c.clip();
     for(let i=0;i<6;i++){const y=((t*120+i*50)%260)-130;c.fillStyle='rgba(255,255,255,.65)';rr(c,-48,y,96,22,6);c.fill();}c.restore();
     // sinaran biru
     for(let i=0;i<3;i++)ring(c,0,0,170+((t*60+i*40)%120),'rgba(90,176,255,.5)',4,.6*(1-((t*60+i*40)%120)/120));});
   // bar
   const bv=vis(t,9.9,12.85,.5,.3);const drop=E.out(P(t,10.76,.55));const hL=470,hR=lerp(470,470*3.5/18,drop);
   const shake=t>=10.76&&t<11.3?Math.sin((t-10.76)*70)*10*(1-(t-10.76)/.55):0;
   withT(c,0,0,1,bv.a,()=>{const by=870;
     rr(c,60,by-hL*bv.k,120,hL*bv.k,20);c.fillStyle='#16c784';c.shadowColor='#16c784';c.shadowBlur=30;c.fill();c.shadowBlur=0;
     txt(c,'18',120,by-hL*bv.k-45,84,'#fff',{stroke:'#06382c',sw:12});txt(c,'NORMAL',120,by+42,34,'#b8ffe6',{w:800});
     const col=drop>.2?'#ff3b4e':'#ffb703';rr(c,900+shake,by-hR*bv.k,120,hR*bv.k,20);c.fillStyle=col;c.shadowColor=col;c.shadowBlur=30;c.fill();c.shadowBlur=0;
     txt(c,drop>.5?'3-4':'18',960+shake,by-hR*bv.k-45,84,'#fff',{stroke:'#5a0a14',sw:12});txt(c,'PHONE',960+shake,by+42,30,'#ffd0d6',{w:800});});
   const vs=vis(t,10.76,12.9,.35,.3);const sh=t<11.2?Math.sin((t-10.76)*60)*9*(1-(t-10.76)/.45):0;
   withT(c,540+sh,205,vs.s*1.0,vs.a,()=>txt(c,'3-4×',0,0,330,'#ff3b4e',{glow:'#ff0033',gb:80,stroke:'#fff',sw:16}));
   burst(c,540,205,10.76,t,'#ff3b4e',380);}

  // S4 simptom
  {const tiles=[['KERING',15.38,'#ff9f1c',290,100],['PEDIH',15.98,'#ffd23f',790,100],['MERAH',16.8,'#ff3b4e',290,245],['KABUR',18.52,'#9b7bff',790,245]];
   for(const [name,t0,col,x,y] of tiles){const v=vis(t,t0,19.15,.4,.3);const act=Math.exp(-(t-t0)*4)*(t>t0?1:0);
     withT(c,x,y,v.s*(1+.1*act),v.a,()=>{c.shadowColor=col;c.shadowBlur=40;rr(c,-215,-58,430,116,58);c.fillStyle='rgba(10,12,28,.88)';c.fill();c.lineWidth=7;c.strokeStyle=col;c.stroke();c.shadowBlur=0;
       c.beginPath();c.arc(-150,0,32,0,7);c.fillStyle=col;c.fill();txt(c,'!',-150,3,44,'#0a0c1c');txt(c,name,32,4,64,'#fff');});}
   const ve=vis(t,14.6,19.2,.5,.3);const red=P(t,15.4,1.5);
   withT(c,185,640,ve.s,ve.a,()=>{c.save();if(t>18.5)c.filter='blur('+(6*E.out(P(t,18.5,.35))*(1-P(t,18.95,.4)))+'px)';eye(c,0,0,330,blinkOpen(t,[[15.0,.25]]),{red,glow:'rgba(255,60,60,.7)',look:[Math.sin(t*3),0]});c.restore();});
   const dry=vis(t,15.4,17,.3,.3); // titisan kering
   if(dry.a>0)for(let i=0;i<5;i++){const y=(t*70+i*55)%260;withT(c,100+i*60,700+y,1,dry.a*(1-y/260)*.8,()=>{c.fillStyle='#ffd23f';c.beginPath();c.arc(0,0,6,0,7);c.fill();});}
  }

  // S5 seram
  {const vt=vis(t,19.4,22.5,.4,.3);const beat=1+.1*Math.exp(-(((t-19.4)%1.1)/1.1)*6);
   withT(c,540,190,vt.s*beat,vt.a,()=>{c.shadowColor='#ff1030';c.shadowBlur=70;c.beginPath();c.moveTo(0,-135);c.lineTo(150,115);c.lineTo(-150,115);c.closePath();c.fillStyle='#ff3b4e';c.fill();c.lineWidth=22;c.strokeStyle='#fff';c.lineJoin='round';c.stroke();c.shadowBlur=0;txt(c,'!',0,20,170,'#fff');});
   const ve=vis(t,22.5,23.95,.35,.3);
   withT(c,540,150,ve.s,ve.a,()=>eye(c,0,0,560,1,{red:.9,glow:'rgba(255,40,60,.8)',look:[0,0]}));
   const vc=vis(t,22.9,23.95,.35,.3);const sec=Math.floor((t-22.9)*3);
   withT(c,540,310,vc.s,vc.a,()=>pill(c,0,0,520,76,'#ff3b4e','0 KELIP · 0:0'+Math.min(9,sec+1),40));}

  // S6 kelip perlahan
  {const v=vis(t,24.0,28.95,.5,.3);
   // nafas cincin
   const br=(Math.sin((t-24)*1.5)*.5+.5);
   withT(c,540,170,v.s,v.a,()=>{for(let i=0;i<3;i++)ring(c,0,0,330+((t*80+i*100)%300),'rgba(126,224,255,.5)',5,.55*(1-((t*80+i*100)%300)/300));
     eye(c,0,0,500,blinkOpen(t,[[25.6,.85],[26.7,.85]]),{look:[Math.sin(t),0]});});
   const vs=vis(t,26.3,28.0,.35,.25);
   withT(c,150,420,vs.s,vs.a,()=>{txt(c,'SLOW',0,-30,64,'#7ee0ff',{stroke:'#08203a',sw:10});txt(c,'SLOW',0,40,64,'#7ee0ff',{stroke:'#08203a',sw:10});},-.12);
   const vd=vis(t,27.5,29.0,.4,.35);const lit=Math.floor(P(t,27.7,.95)*10+.0001);
   withT(c,540,330,1,vd.a,()=>{for(let i=0;i<10;i++){const on=i<lit;c.beginPath();c.arc(-337+i*75,0,on?26:17,0,7);c.fillStyle=on?'#7ee0ff':'rgba(255,255,255,.35)';c.shadowColor='#7ee0ff';c.shadowBlur=on?30:0;c.fill();}});
   withT(c,905,500,vd.s,vd.a,()=>txt(c,'10×',0,0,170,'#fff',{glow:'#2aa8ff',gb:60,stroke:'#0b3a6b',sw:16}),.1);}

  // S7 segar sejuk tenang
  {const ve=vis(t,28.95,31.4,.4,.35);
   withT(c,540,175,ve.s,ve.a,()=>eye(c,0,0,520,.82,{look:[0,0],iris:'#7ee8c8',iris2:'#1b8f78',glow:'rgba(120,255,220,.8)'}));
   for(const [wd,t0,col] of [['SEGAR',31.46,'#7affd9'],['SEJUK',32.56,'#7ee0ff'],['TENANG',33.72,'#b9a6ff']]){
     const t1=t0==33.72?34.45:t0+1.1;const v=vis(t,t0,t1,.4,.3);const wob=Math.sin(t*3)*4;
     withT(c,540,205+wob,v.s,v.a,()=>txt(c,wd,0,0,wd=='TENANG'?210:230,'#fff',{glow:col,gb:80,stroke:col,sw:18}));
     burst(c,540,205,t0,t,col,360);}
   const sp=vis(t,31.4,34.5,.4,.3);if(sp.a>0)for(let i=0;i<7;i++){const x=[110,960,200,880,70,990,300][i],y=[420,380,640,690,300,560,150][i];sparkle(c,x,y+Math.sin(t*2+i)*14,22+(i%3)*8,'rgba(255,255,255,'+(sp.a*(.5+.5*Math.sin(t*4+i*2)))+')',t*.6);}}

  // S8/S9 CTA
  {const v=vis(t,35.7,38.6,.45,.3);
   withT(c,540,170,v.s,v.a,()=>{c.shadowColor='#ffd23f';c.shadowBlur=50;rr(c,-380,-115,760,230,50);c.fillStyle='rgba(255,255,255,.96)';c.fill();c.shadowBlur=0;
     c.beginPath();c.moveTo(-100,112);c.lineTo(-150,170);c.lineTo(-30,114);c.fillStyle='rgba(255,255,255,.96)';c.fill();
     if(t<36.05){for(let i=0;i<3;i++){c.beginPath();c.arc(-70+i*70,0,16+6*Math.max(0,Math.sin(t*12-i*1.2)),0,7);c.fillStyle='#8a94a6';c.fill();}}
     else{const k=E.back(P(t,36.05,.3));c.save();c.scale(k,k);txt(c,'TEST & KOMEN!',0,-28,92,'#0b1f3a');txt(c,'berapa kali kau kelip?',0,52,48,'#ff3b4e',{w:800});c.restore();}});
   const va=vis(t,36.9,38.6,.4,.3);
   withT(c,930,470+Math.abs(Math.sin(t*5))*40,va.s,va.a,()=>{c.fillStyle='#ffd23f';c.shadowColor='#ffb703';c.shadowBlur=30;c.beginPath();c.moveTo(-50,-60);c.lineTo(50,-60);c.lineTo(50,0);c.lineTo(90,0);c.lineTo(0,90);c.lineTo(-90,0);c.lineTo(-50,0);c.closePath();c.fill();});
   for(let i=0;i<8;i++){const t0=36.2+i*.22;const d=t-t0;if(d>0&&d<2.2){const y=1000-d*420;const x=[880,960,820,990,900,780,940,850][i]+Math.sin(d*3+i)*26;heart(c,x,y,40+(i%3)*14,'rgba(255,80,110,'+(1-d/2.2)*.9+')');}}
   if(t>34.4&&t<36){const d=t-34.9;const vv=vis(t,34.9,35.9,.3,.3);if(vv.a>0)for(let i=0;i<6;i++){sparkle(c,[120,980,200,900,70,1010][i],[420,420,600,620,250,330][i],26,'rgba(255,230,120,'+vv.a+')',t*1.5);}}}
}

// ---------- kapsyen ----------
const CAP=[
 [['Berapa',0,.48],['kali',.48,.84],['korang',.84,1.12]],
 [['kelip',1.12,1.5],['mata',1.5,1.8]],
 [['dalam',1.8,2.1],['semenit?',2.1,2.96]],
 [['Normal,',3.12,3.58]],
 [['kita',3.58,4.06],['kelip',4.06,4.32],['mata',4.32,4.52]],
 [['dalam',4.52,4.86],['18',4.86,5.56],['kali',5.56,6.08]],
 [['semenit.',6.08,6.8]],
 [['Tapi',6.8,7.32],['ada',7.32,7.68],['kajian',7.68,8.02]],
 [['jumpa',8.02,8.48],['bila',8.48,8.84],['main',8.84,9.2],['phone,',9.2,9.54]],
 [['boleh',9.54,10.1],['jatuh',10.1,10.48],['sampai',10.48,10.76]],
 [['3-4',10.76,11.92],['kali',11.92,12.34],['sahaja!',12.34,12.9]],
 [['Kurang',13.3,13.9],['kelip,',13.9,14.4]],
 [['mata',14.4,14.9],['jadi',14.9,15.38],['kering,',15.38,15.98]],
 [['pedih,',15.98,16.8],['merah,',16.8,17.12]],
 [['pandangan',17.12,17.76],['pun',17.76,18.1]],
 [['boleh',18.1,18.52],['kabur.',18.52,19.1]],
 [['Seramnya,',19.32,20.3]],
 [['kita',20.52,20.74],['langsung',20.74,21.44]],
 [['tak',21.44,21.68],['perasan',21.68,22.2]],
 [['yang',22.2,22.46],['kita',22.46,22.96],['dah',22.96,23.22]],
 [['tak',23.22,23.4],['berkelip.',23.4,24.1]],
 [['So,',23.86,24.9],['lepas',24.98,25.38]],
 [['video',25.38,25.74],['ini,',25.74,26.3]],
 [['kelip',26.42,26.8],['slow-slow',26.8,27.34]],
 [['korang',27.34,27.56],['10',27.56,28.26],['kali.',28.26,28.7]],
 [['Mata',28.88,29.26],['korang',29.26,29.66],['confirm',29.66,30.32]],
 [['akan',30.32,30.88],['rasa',30.88,31.18]],
 [['lebih',31.18,31.46],['segar,',31.46,32.1]],
 [['lebih',32.32,32.56],['sejuk',32.56,33.06]],
 [['dan',33.06,33.34],['lebih',33.34,33.72],['tenang.',33.72,34.3]],
 [['So,',34.44,34.9],['jumpa',34.97,35.31],['korang.',35.31,35.75]],
 [['Cuba',35.8,36.05],['test',36.05,36.31],['dan',36.31,36.61],['komen',36.61,37.0]],
 [['dekat',37.0,37.39],['ruang',37.39,37.63],['komen.',37.63,38.12]],
 [['Okay,',38.19,38.5],['bye',38.57,38.73],['bye!',38.73,39.0]],
];
function front(c,t){
  c.clearRect(0,0,W,H);
  let idx=-1;for(let i=0;i<CAP.length;i++){const s=CAP[i][0][1];const nxt=i+1<CAP.length?CAP[i+1][0][1]:99;const e=Math.min(CAP[i][CAP[i].length-1][2]+.25,nxt);if(t>=s&&t<e){idx=i;}}
  if(idx<0)return;const ch=CAP[idx];const s=ch[0][1];
  const k=E.back(P(t,s,.18));const fo=1-P(t,ch[ch.length-1][2]+.12,.13)*(idx+1<CAP.length&&CAP[idx+1][0][1]<ch[ch.length-1][2]+.25?0:1);
  const size=84;c.save();c.font='900 '+size+'px '+FONT;
  const gap=24;const ws=ch.map(w=>c.measureText(w[0]).width);const total=ws.reduce((a,b)=>a+b,0)+gap*(ch.length-1);
  const act=ch.findIndex((w,i)=>t>=w[1]&&t<w[2]);
  c.restore();
  c.save();c.globalAlpha=clamp(fo)*clamp(P(t,s,.08));c.translate(W/2,1600);const sc=.82+.18*k;c.scale(sc,sc);
  let x=-total/2;
  ch.forEach((w,i)=>{const on=t>=w[1];const cur=i===act;const pop=cur?1+.14*Math.sin(Math.PI*P(t,w[1],.2)):1;
    c.save();c.translate(x+ws[i]/2,0);c.scale(pop,pop);
    txt(c,w[0],0,0,size,cur?'#ffe14d':'#ffffff',{stroke:'#000000',sw:18,glow:'rgba(0,0,0,.5)',gb:18});
    c.restore();x+=ws[i]+gap;});
  c.restore();
}

window.render=(t)=>{back(B,t);front(F,t);};
window.grab=(id)=>document.getElementById(id).toDataURL('image/png');
</script></body></html>`;

(async () => {
  fs.mkdirSync(path.join(outDir, 'back'), { recursive: true });
  fs.mkdirSync(path.join(outDir, 'front'), { recursive: true });
  const br = await chromium.launch();
  const pg = await br.newPage({ viewport: { width: 1080, height: 1920 } });
  await pg.setContent(PAGE);
  await pg.evaluate(() => document.fonts.ready);
  for (let f = f0; f < f1; f++) {
    const t = f / FPS;
    await pg.evaluate((t) => window.render(t), t);
    for (const id of ['b', 'f']) {
      const d = await pg.evaluate((id) => window.grab(id), id);
      fs.writeFileSync(path.join(outDir, id === 'b' ? 'back' : 'front', String(f).padStart(5, '0') + '.png'), Buffer.from(d.split(',')[1], 'base64'));
    }
  }
  await br.close();
})();
