#!/usr/bin/env node
// v2 (klinikal): kad maklumat bersih + kapsyen, satu lapisan sahaja (tiada matte, tiada tint latar).
// Guna: node blink_graphics_v2.js <outDir> <fStart> <fEnd>   -> <outDir>/front/%05d.png
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [outDir, f0, f1] = [process.argv[2], +process.argv[3], +process.argv[4]];
const PAGE = `<html><body style="margin:0;background:transparent"><canvas id=f width=1080 height=1920></canvas><script>
const IM={};const W=1080,H=1920,F=document.getElementById('f').getContext('2d');
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

function slide(c,t,a,b,label,col,draw){const al=out(P(t,a,.3))*(1-P(t,b,.3));if(al<=.003)return;c.save();c.globalAlpha=al;
  c.fillStyle='#F3F7FA';c.fillRect(0,0,W,H);c.fillStyle='#FFFFFF';c.fillRect(0,0,W,H);
  let g=c.createLinearGradient(0,0,0,H);g.addColorStop(0,'#EAF2F7');g.addColorStop(1,'#FFFFFF');c.fillStyle=g;c.fillRect(0,0,W,H);
  c.fillStyle=col;c.fillRect(70,262,8,44);T(c,label,98,284,34,col,700);c.fillStyle=LINE;c.fillRect(70,322,880,2);
  c.translate(0,(1-out(P(t,a,.4)))*14);draw(c,t);c.restore();}
function wrap(c,s,x,y,maxw,lh,size,col,w=700){c.font=w+' '+size+'px '+FONT;const words=s.split(' ');let line='',yy=y;for(const wd of words){const tt=line?line+' '+wd:wd;if(c.measureText(tt).width>maxw&&line){T(c,line,x,yy,size,col,w);yy+=lh;line=wd;}else line=tt;}T(c,line,x,yy,size,col,w);}
function img(c,name,x,y,w,a=1){const im=IM[name];if(!im)return 0;const h=im.height*w/im.width;c.save();c.globalAlpha*=a;c.drawImage(im,x,y,w,h);c.restore();return h;}
function scene(c,t){
 // A: kadar normal
 slide(c,t,3.12,6.95,'KADAR KELIPAN NORMAL',GREEN,(c)=>{lineEye(c,540,470,280,blink(t,[[3.9,.3],[5.7,.3]]));
   const k=out(P(t,4.3,1.1));const n=Math.round(18*k);const pop=1+.05*Math.sin(Math.PI*P(t,5.4,.4))*(t>5.4?1:0);
   c.save();c.translate(540,820);c.scale(pop,pop);T(c,String(n),0,0,340,NAVY,800,'center');c.restore();
   T(c,'kali / minit',540,1030,64,GRAY,600,'center');bar(c,160,1130,760,18,k,GREEN);T(c,'0',160,1180,28,GRAY,600);T(c,'18',920,1180,28,GRAY,600,'right');});
 // B: kajian + rujukan
 slide(c,t,7.65,13.1,'KAJIAN: KELIPAN MENURUN',TEAL,(c)=>{
   const k1=out(P(t,7.9,.8));T(c,'Normal',70,420,40,NAVY,600);bar(c,330,398,470,44,k1,GREEN);if(k1>.5)T(c,'18',950,420,52,NAVY,800,'right');
   const on=out(P(t,9.2,.4));c.save();c.globalAlpha*=on;const d=out(P(t,10.76,.7));const val=lerp(18,3.5,d);
   T(c,'Main phone',70,520,40,NAVY,600);bar(c,330,498,470,44,out(P(t,9.2,.7))*val/18,d>0?RED:GREEN);T(c,d>.6?'3-4':String(Math.round(val)),950,520,52,d>.6?RED:NAVY,800,'right');c.restore();
   T(c,'RUJUKAN',70,650,30,TEAL,700);c.fillStyle=LINE;c.fillRect(220,650,730,2);
   [['springer',8.3,"Kadar kelip menurun ketika membaca pada semua paparan digital","Talens-Estarelles et al., Graefe's Arch Clin Exp Ophthalmol, 2022"],
    ['insight',9.5,"Main game di telefon kurangkan kadar kelip kanak-kanak dengan cepat","Insight (UNSW), Jun 2022"],
    ['pubmed',11.6,"Corak kelip: membaca di skrin komputer vs bahan bercetak","Chu et al., Optom Vis Sci, 2014 (PubMed)"]].forEach(([nm,t0,txt,src],i)=>{
     const a=out(P(t,t0,.4));if(a<=0)return;const y=700+i*205;c.save();c.globalAlpha*=a;c.translate(0,(1-a)*12);
     rr(c,70,y,370,180,14);c.fillStyle='#fff';c.fill();c.lineWidth=2;c.strokeStyle=LINE;c.stroke();
     c.save();rr(c,70,y,370,180,14);c.clip();const im=IM[nm];const w=350,h=im.height*w/im.width;c.drawImage(im,80,y+(180-h)/2,w,h);c.restore();
     wrap(c,txt,470,y+34,480,36,30,NAVY,700);wrap(c,src,470,y+138,480,28,24,GRAY,500);c.restore();});});
 // C: simptom
 slide(c,t,13.0,19.2,'KESAN KURANG BERKELIP','#B9770E',(c)=>{
   [['Kering',15.38,'#D68910'],['Pedih',15.98,'#E67E22'],['Merah',16.8,RED],['Kabur',18.52,'#7D5BA6']].forEach(([s,t0,col],i)=>{const a=out(P(t,t0,.35));if(a<=0)return;
     c.save();c.globalAlpha*=a;c.translate((1-a)*-24,0);c.beginPath();c.arc(100,430+i*120,20,0,7);c.fillStyle=col;c.fill();T(c,s,150,432+i*120,84,NAVY,700);c.restore();});
   const a=out(P(t,13.4,.6));if(a>0){c.save();c.globalAlpha*=a;rr(c,150,930,780,300,18);c.clip();img(c,'kkm',150,930+(300-780*325/900)/2,780);c.restore();
     c.save();c.globalAlpha*=a;T(c,'Sumber: Kementerian Kesihatan Malaysia (KKM)',150,1262,26,GRAY,500);c.restore();}});
 // D: kelip perlahan
 slide(c,t,26.3,29.05,'KELIP PERLAHAN',TEAL,(c)=>{lineEye(c,540,560,520,blink(t,[[26.45,.9],[27.45,.9]]));T(c,'10 kali',540,900,150,NAVY,800,'center');
   const lit=Math.floor(P(t,27.7,.95)*10+.0001);for(let i=0;i<10;i++){c.beginPath();c.arc(150+i*86,1080,22,0,7);c.fillStyle=i<lit?TEAL:'#DCE5EC';c.fill();}});
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
  c.save();c.globalAlpha=a;c.translate(0,(1-out(a))*8);rr(c,W/2-tot/2-34,1380-52,tot+68,104,26);c.fillStyle='rgba(15,42,67,.72)';c.fill();
  let x=W/2-tot/2;ch.forEach((w,i)=>{const cur=t>=w[1]&&t<w[2];T(c,w[0],x,1381,size,cur?'#8FE3E8':'#FFFFFF',700);x+=ws[i]+gap;});c.restore();}
window.render=t=>{F.clearRect(0,0,W,H);scene(F,t);caps(F,t);};
window.grab=()=>document.getElementById('f').toDataURL('image/png');
</script></body></html>`;
(async()=>{fs.mkdirSync(path.join(outDir,'front'),{recursive:true});const br=await chromium.launch(),pg=await br.newPage({viewport:{width:1080,height:1920}});
 await pg.setContent(PAGE);const imgs={};for(const n of ['springer','insight','pubmed','kkm'])imgs[n]='data:image/png;base64,'+fs.readFileSync(path.join(__dirname,'..','work','blink','img',(n=='kkm'?'kkm_eyes':n)+'.png')).toString('base64');
 await pg.evaluate(async(imgs)=>{for(const n in imgs){const im=new Image();im.src=imgs[n];await im.decode();IM[n]=im;}await document.fonts.ready;},imgs);
 for(let f=f0;f<f1;f++){await pg.evaluate(t=>window.render(t),f/30);const d=await pg.evaluate(()=>window.grab());fs.writeFileSync(path.join(outDir,'front',String(f).padStart(5,'0')+'.png'),Buffer.from(d.split(',')[1],'base64'));}
 await br.close();})();
