#!/usr/bin/env node
// v2 (klinikal): kad maklumat bersih + kapsyen, satu lapisan sahaja (tiada matte, tiada tint latar).
// Guna: node blink_graphics_v2.js <outDir> <fStart> <fEnd>   -> <outDir>/front/%05d.png
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [outDir, f0, f1] = [process.argv[2], +process.argv[3], +process.argv[4]];
const PAGE = `<html><body style="margin:0;background:transparent"><canvas id=f width=1080 height=1920></canvas><script>
const W=1080,H=1920,F=document.getElementById('f').getContext('2d');
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)),P=(t,a,d)=>clamp((t-a)/d),lerp=(a,b,k)=>a+(b-a)*k;
const out=t=>1-Math.pow(1-t,3),inout=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
const FONT='Inter, sans-serif';
const NAVY='#0F2A43',TEAL='#0E7C86',GRAY='#5B6B7B',GREEN='#2E8B6A',RED='#C0392B',LINE='#D8E1E8';
function vis(t,a,b,din=.4,dout=.3){return {a:out(P(t,a,din))*(1-inout(P(t,b,dout))),y:(1-out(P(t,a,din)))*16,on:t>=a&&t<b+dout};}
function rr(c,x,y,w,h,r){c.beginPath();c.moveTo(x+r,y);c.arcTo(x+w,y,x+w,y+h,r);c.arcTo(x+w,y+h,x,y+h,r);c.arcTo(x,y+h,x,y,r);c.arcTo(x,y,x+w,y,r);c.closePath();}
function T(c,s,x,y,size,col,w=600,al='left'){c.font=w+' '+size+'px '+FONT;c.textAlign=al;c.textBaseline='middle';c.fillStyle=col;c.fillText(s,x,y);}
function card(c,x,y,w,h,accent=TEAL){c.save();c.shadowColor='rgba(10,30,50,.22)';c.shadowBlur=28;c.shadowOffsetY=8;rr(c,x,y,w,h,20);c.fillStyle='rgba(255,255,255,.95)';c.fill();c.restore();
  c.save();rr(c,x,y,w,h,20);c.clip();c.fillStyle=accent;c.fillRect(x,y,8,h);c.restore();}
function lineEye(c,cx,cy,w,open,col=NAVY){const h=w*.3*Math.max(open,.04);c.save();c.translate(cx,cy);c.lineWidth=w*.055;c.strokeStyle=col;c.lineCap='round';c.lineJoin='round';
  c.beginPath();c.moveTo(-w/2,0);c.bezierCurveTo(-w*.25,-h*1.45,w*.25,-h*1.45,w/2,0);c.bezierCurveTo(w*.25,h*1.45,-w*.25,h*1.45,-w/2,0);c.stroke();
  if(open>.25){c.beginPath();c.arc(0,0,w*.15*Math.min(1,open*1.2),0,7);c.fillStyle=TEAL;c.fill();c.beginPath();c.arc(0,0,w*.06,0,7);c.fillStyle=NAVY;c.fill();}c.restore();}
function blink(t,l){let o=1;for(const [a,d] of l)if(t>a&&t<a+d)o=Math.min(o,1-Math.sin(Math.PI*(t-a)/d)*.97);return o;}
function bar(c,x,y,w,h,k,col){rr(c,x,y,w,h,h/2);c.fillStyle='#E6EDF2';c.fill();if(k>0){rr(c,x,y,Math.max(h,w*k),h,h/2);c.fillStyle=col;c.fill();}}
function chip(c,x,y,s,col,a,dy){c.save();c.globalAlpha*=a;c.translate(0,dy);c.font='600 40px '+FONT;const w=c.measureText(s).width+78;rr(c,x,y-34,w,68,34);c.fillStyle='#F2F6F9';c.fill();c.lineWidth=2;c.strokeStyle=LINE;c.stroke();
  c.beginPath();c.arc(x+34,y,9,0,7);c.fillStyle=col;c.fill();T(c,s,x+56,y+1,40,NAVY,600);c.restore();return w;}
const X=90,Y=56,CW=900;
function cardAt(c,t,a,b,h,accent,draw){const v=vis(t,a,b);if(v.a<=.003)return;c.save();c.globalAlpha=v.a;c.translate(0,v.y);card(c,X,Y,CW,h,accent);draw(c,t,v);c.restore();}
function scene(c,t){
 // S1
 cardAt(c,t,.05,2.95,170,TEAL,(c)=>{lineEye(c,X+110,Y+85,120,blink(t,[[1.0,.3],[1.45,.3]]));T(c,'KELIPAN MATA',X+210,Y+55,30,TEAL,700);T(c,'Berapa kali dalam 1 minit?',X+210,Y+105,44,NAVY,700);
   if(t>2.0){const cx=X+CW-80,cy=Y+85;c.lineWidth=7;c.strokeStyle=LINE;c.beginPath();c.arc(cx,cy,36,0,7);c.stroke();c.strokeStyle=TEAL;c.beginPath();c.arc(cx,cy,36,-Math.PI/2,-Math.PI/2+inout(P(t,2.05,.9))*Math.PI*2);c.stroke();T(c,'60s',cx,cy+1,22,NAVY,700,'center');}});
 // S2
 cardAt(c,t,3.12,6.85,200,GREEN,(c)=>{T(c,'KADAR NORMAL',X+40,Y+42,30,GREEN,700);const n=Math.round(18*out(P(t,4.3,1.1)));T(c,String(n),X+40,Y+112,110,NAVY,800);
   T(c,'kali / minit',X+40+(n>9?170:100),Y+128,40,GRAY,500);bar(c,X+40,Y+172,CW-80,12,out(P(t,4.3,1.1)),GREEN);});
 // S3
 cardAt(c,t,6.85,12.95,250,TEAL,(c)=>{T(c,'KELIPAN MATA SEMINIT',X+40,Y+40,30,TEAL,700);
   const k1=out(P(t,7.7,.8));T(c,'Normal',X+40,Y+105,36,NAVY,600);bar(c,X+300,Y+90,420,30,k1*18/18,GREEN);T(c,k1>0?'18':'',X+CW-60,Y+105,44,NAVY,800,'right');
   const on=vis(t,9.2,99,.4,.1).a;c.save();c.globalAlpha*=on;const d=out(P(t,10.76,.7));const val=lerp(18,3.5,d);
   T(c,'Main phone',X+40,Y+185,36,NAVY,600);bar(c,X+300,Y+170,420,30,out(P(t,9.2,.7))*val/18,d>0?RED:GREEN);
   T(c,d>.6?'3-4':String(Math.round(val)),X+CW-60,Y+185,44,d>.6?RED:NAVY,800,'right');c.restore();});
 // S4
 cardAt(c,t,13.3,19.15,170,'#D68910',(c)=>{T(c,'KESAN KURANG BERKELIP',X+40,Y+40,30,'#B9770E',700);let x=X+40;
   for(const [s,t0,col] of [['Kering',15.38,'#D68910'],['Pedih',15.98,'#E67E22'],['Merah',16.8,RED],['Kabur',18.52,'#7D5BA6']]){const k=out(P(t,t0,.35));
     if(k>0){x+=chip(c,x,Y+112,s,col,k,(1-k)*10)+14;}else x+=0;}});
 // S5
 cardAt(c,t,19.4,24,170,RED,(c)=>{const s=t>22.9;lineEye(c,X+110,Y+85,120,1,s?RED:NAVY);
   T(c,s?'TIADA KELIPAN':'AMARAN',X+210,Y+55,30,RED,700);
   if(!s)T(c,'Kita tak perasan bila berhenti',X+210,Y+105,40,NAVY,700);
   else{T(c,'0 kelip',X+210,Y+110,56,NAVY,800);T(c,'0:0'+Math.min(9,Math.floor(t-22.9)+1)+'s',X+CW-40,Y+110,40,RED,700,'right');}});
 // S6
 cardAt(c,t,24.0,28.95,190,TEAL,(c)=>{lineEye(c,X+110,Y+90,120,blink(t,[[25.6,.9],[26.7,.9]]));T(c,'KELIP PERLAHAN',X+210,Y+50,30,TEAL,700);T(c,'10 kali',X+210,Y+100,56,NAVY,800);
   const lit=Math.floor(P(t,27.7,.95)*10+.0001);for(let i=0;i<10;i++){c.beginPath();c.arc(X+216+i*46,Y+155,11,0,7);c.fillStyle=i<lit?TEAL:'#DCE5EC';c.fill();}});
 // S7
 cardAt(c,t,28.95,34.5,170,GREEN,(c)=>{T(c,'SELEPAS BERKELIP PERLAHAN',X+40,Y+40,30,GREEN,700);let x=X+40;
   for(const [s,t0,col] of [['Segar',31.46,TEAL],['Sejuk',32.56,'#2F80C1'],['Tenang',33.72,GREEN]]){const k=out(P(t,t0,.35));if(k>0)x+=chip(c,x,Y+112,s,col,k,(1-k)*10)+14;}
   if(t<31.4)T(c,'Mata rasa lebih…',X+40,Y+112,42,NAVY,700);});
 // S9
 cardAt(c,t,35.8,38.6,170,TEAL,(c)=>{T(c,'CUBA SENDIRI',X+40,Y+45,30,TEAL,700);T(c,'Test & komen',X+40,Y+92,56,NAVY,800);T(c,'Berapa kali anda berkelip?',X+40,Y+140,32,GRAY,600);});
}
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
];function caps(c,t){
  let idx=-1;for(let i=0;i<CAP.length;i++){const s=CAP[i][0][1],nx=i+1<CAP.length?CAP[i+1][0][1]:99,e=Math.min(CAP[i][CAP[i].length-1][2]+.25,nx);if(t>=s&&t<e)idx=i;}
  if(idx<0)return;const ch=CAP[idx],s=ch[0][1];const a=P(t,s,.1);if(a<=0)return;
  const size=58;c.font='700 '+size+'px '+FONT;const gap=16;const ws=ch.map(w=>c.measureText(w[0]).width);const tot=ws.reduce((x,y)=>x+y,0)+gap*(ch.length-1);
  c.save();c.globalAlpha=a;c.translate(0,(1-out(a))*8);rr(c,W/2-tot/2-34,1600-52,tot+68,104,26);c.fillStyle='rgba(15,42,67,.72)';c.fill();
  let x=W/2-tot/2;ch.forEach((w,i)=>{const cur=t>=w[1]&&t<w[2];T(c,w[0],x,1601,size,cur?'#8FE3E8':'#FFFFFF',700);x+=ws[i]+gap;});c.restore();}
window.render=t=>{F.clearRect(0,0,W,H);scene(F,t);caps(F,t);};
window.grab=()=>document.getElementById('f').toDataURL('image/png');
</script></body></html>`;
(async()=>{fs.mkdirSync(path.join(outDir,'front'),{recursive:true});const br=await chromium.launch(),pg=await br.newPage({viewport:{width:1080,height:1920}});
 await pg.setContent(PAGE);await pg.evaluate(()=>document.fonts.ready);
 for(let f=f0;f<f1;f++){await pg.evaluate(t=>window.render(t),f/30);const d=await pg.evaluate(()=>window.grab());fs.writeFileSync(path.join(outDir,'front',String(f).padStart(5,'0')+'.png'),Buffer.from(d.split(',')[1],'base64'));}
 await br.close();})();
