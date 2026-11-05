#!/usr/bin/env python3
"""Bina video TikTok Loafer Flat Premium: stabilize -> trim -> xfade -> popup + SFX + muzik."""
import subprocess as sp, numpy as np, os, wave, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,XD = 1080,1920,30,0.12
N="work/norm"; SEG="work/seg"; os.makedirs(SEG,exist_ok=True)
segs=[("hook","IMG_1288",0.0,3.3),("warna","IMG_1286",0.5,3.4),("pu","IMG_1289",0.3,3.5),
      ("tapak","IMG_1270",0.2,2.8),("grip","IMG_1285",2.0,1.9),("insole","IMG_1287",0.2,3.7),("end",None,0,4.8)]
def run(*a): sp.run(a,check=True,stdout=sp.DEVNULL,stderr=sp.DEVNULL)
# 1. stabilize + trim
for n,src,ss,d in segs:
    out=f"{SEG}/{n}.mp4"
    if src is None:
        run("ffmpeg","-y","-f","lavfi","-i",f"color=c=0xF3EEE6:s={W}x{H}:r={FPS}:d={d}","-c:v","libx264","-crf","14","-pix_fmt","yuv420p",out); continue
    trf=f"{SEG}/{n}.trf"
    run("ffmpeg","-y","-ss",str(ss),"-t",str(d),"-i",f"{N}/{src}.mp4","-vf",f"vidstabdetect=shakiness=5:accuracy=15:result={trf}","-f","null","-")
    run("ffmpeg","-y","-ss",str(ss),"-t",str(d),"-i",f"{N}/{src}.mp4","-vf",
        f"vidstabtransform=input={trf}:smoothing=12:zoom=3:optzoom=0,unsharp=5:5:0.5,fps={FPS},format=yuv420p",
        "-c:v","libx264","-crf","14","-preset","fast",out)
# 2. xfade chain
starts=[]; t=0.0
for i,(_,_,_,d) in enumerate(segs): starts.append(t); t+=d-XD
total=t+XD
ins=[x for n,*_ in segs for x in ("-i",f"{SEG}/{n}.mp4")]
fc="";prev="[0:v]";acc=segs[0][3]
for i in range(1,len(segs)):
    off=acc-XD; fc+=f"{prev}[{i}:v]xfade=transition=fade:duration={XD}:offset={off:.3f}[v{i}];"; prev=f"[v{i}]"; acc=off+segs[i][3]
run("ffmpeg","-y",*ins,"-filter_complex",fc.rstrip(";"),"-map",prev,"-c:v","libx264","-crf","14","-pix_fmt","yuv420p","work/base.mp4")
# 3. sprites
F=lambda w,s:ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{w}.otf",s)
INK=(28,28,30); CREAM=(255,255,255)
def pill(text,size=46,dot=None,tag=None,tagcol=INK,fill=(255,255,255,235),fg=INK,padx=44,h=None,weight="SemiBold"):
    f=F(weight,size); tw=int(f.getlength(text)); h=h or int(size*2.1)
    dw=(h*0.42+26) if dot else 0
    tf=F("Bold",int(size*0.56)); tgw=int(tf.getlength(tag))+36 if tag else 0
    w=int(padx*2+dw+tw+(tgw+22 if tag else 0)); pad=50
    im=Image.new("RGBA",(w+pad*2,h+pad*2),(0,0,0,0))
    sh=Image.new("RGBA",im.size,(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle((pad,pad+10,pad+w,pad+h+10),h//2,fill=(0,0,0,70))
    im=Image.alpha_composite(im,sh.filter(ImageFilter.GaussianBlur(16)))
    d=ImageDraw.Draw(im); d.rounded_rectangle((pad,pad,pad+w,pad+h),h//2,fill=fill)
    x=pad+padx
    if dot:
        r=int(h*0.21); cy=pad+h//2; d.ellipse((x,cy-r,x+2*r,cy+r),fill=dot,outline=(0,0,0,60),width=2); x+=2*r+26
    d.text((x,pad+h/2),text,font=f,fill=fg,anchor="lm"); x+=tw+22
    if tag:
        th=int(size*1.05); d.rounded_rectangle((x,pad+h/2-th/2,x+tgw,pad+h/2+th/2),th//2,fill=tagcol)
        d.text((x+tgw/2,pad+h/2),tag,font=tf,fill=(255,255,255),anchor="mm")
    return np.asarray(im).astype(np.float32)
def text(t,size,col=INK,weight="SemiBold"):
    f=F(weight,size); w=int(f.getlength(t))+20; im=Image.new("RGBA",(w,int(size*1.5)),(0,0,0,0))
    ImageDraw.Draw(im).text((w/2,size*.75),t,font=f,fill=col,anchor="mm"); return np.asarray(im).astype(np.float32)
def ease_back(x,c=1.7): x=min(max(x,0),1); return 1+(c+1)*(x-1)**3+c*(x-1)**2
events=[]  # (abs_start, abs_end, sprite, cx, cy, sfx)
def add(seg,t0,t1,spr,cx,cy,sfx="pop"):
    i=[s[0] for s in segs].index(seg); a=starts[i]+t0; b=starts[i]+(t1 if t1 else segs[i][3]-0.1)
    events.append((a,b,spr,cx,cy,sfx))
BEIGE=(199,178,139);LBEIGE=(229,216,190);APR=(233,183,147);BLK=(27,27,29);GOLD=(255,200,61)
add("hook",0.3,None,pill("Loafer Flat Premium",56,h=120,padx=56),W//2,330)
add("hook",0.9,None,pill("100% PU Leather",36,fill=(28,28,30,230),fg=(255,255,255),h=84),W//2,470)
add("warna",0.1,None,pill("4 PILIHAN WARNA",34,fill=(28,28,30,230),fg=(255,255,255),h=80),W//2,900)
for k,(lab,col,tag,tc,t0) in enumerate([("Hitam",BLK,None,INK,0.5),("Baege",BEIGE,None,INK,1.0),("Light Beige",LBEIGE,"BARU",(64,140,96),1.5),("Apricot",APR,"TOP SELLING",(214,110,60),2.0)]):
    add("warna",t0,None,pill(lab,46,dot=col,tag=tag,tagcol=tc),W//2,1040+k*135)
add("pu",0.3,None,pill("100% PU Leather",54,h=118,padx=54),W//2,1080)
add("pu",1.1,None,pill("Tak campur getah",42,fill=(28,28,30,230),fg=(255,255,255)),W//2,1230)
add("pu",1.8,None,pill("Tak campur plastik",42,fill=(28,28,30,230),fg=(255,255,255)),W//2,1360)
add("tapak",0.3,None,pill("Tapak Fully Getah",54,h=118,padx=54),W//2,1150)
add("grip",0.2,None,pill("Anti Slip",50,h=112),W//2,1050)
add("grip",0.8,None,pill("Extra Grip",50,h=112),W//2,1190)
add("insole",0.2,None,pill("Insole Extra Getah",54,h=118,padx=54),W//2,1080)
add("insole",1.2,None,pill("Berdiri lama tak ada masalah",38,fill=(28,28,30,230),fg=(255,255,255)),W//2,1230)
add("insole",2.2,None,pill("Jalan jauh tak sakit tumit",38,fill=(28,28,30,230),fg=(255,255,255)),W//2,1360)
add("end",0.1,None,text("Selesa untuk",46,(110,106,100),"Medium"),W//2,430,None)
for k,l in enumerate(["Daily use","Pejabat","Konvo","Jalan-jalan","Hadiah"]):
    add("end",0.35+k*0.32,None,text(l,76,INK,"SemiBold"),W//2,560+k*115)
add("end",2.2,None,text("Rasa kasut ni sesuai untuk anda?",38,(110,106,100),"Medium"),W//2,1235,None)
add("end",2.5,None,pill("Klik Beg Kuning Sekarang",46,fill=GOLD+(255,),h=124,padx=60,weight="Bold"),W//2,1345,"chime")
for i,col in enumerate([BLK,BEIGE,LBEIGE,APR]):
    s=np.zeros((90,90,4),np.float32); im=Image.new("RGBA",(90,90),(0,0,0,0)); ImageDraw.Draw(im).ellipse((15,15,75,75),fill=col+(255,),outline=(0,0,0,50),width=2)
    add("end",1.9+i*0.1,None,np.asarray(im).astype(np.float32),W//2-165+i*110,1130,None)
# 4. audio
SR=44100; T=total+0.3; n=int(SR*T); rng=np.random.default_rng(3); tt=np.arange(n)/SR
def lp(x,fc):
    a=math.exp(-2*math.pi*fc/SR); y=np.empty_like(x); s=0.0
    for i in range(len(x)): s=(1-a)*x[i]+a*s; y[i]=s
    return y
bpm=84; beat=60/bpm; mus=np.zeros(n,np.float32)
chords=[[48,55,59,64],[45,52,60,64],[41,48,55,64],[43,50,57,62]]  # Cmaj7 Am7 Fmaj7 G6
mf=lambda m:440*2**((m-69)/12)
bar=beat*4; 
for ci in range(int(T/(bar*1.0))+1):
    ch=chords[(ci//2)%4]; t0=ci*bar
    for m in ch:  # soft pad
        for det in (-.004,.004):
            f=mf(m)*(1+det); seg=np.sin(2*np.pi*f*tt)*np.clip((tt-t0)/0.4,0,1)*np.clip(1-(tt-t0-bar+0.3)/0.3,0,1)*(tt>=t0)*(tt<t0+bar)
            mus+=0.035*seg.astype(np.float32)
    # arpeggio pluck (rhodes-ish)
    for k,m in enumerate([ch[3]+12,ch[2]+12,ch[1]+24,ch[2]+12]*2):
        ts=t0+k*beat/2
        if ts>=T: break
        i0=int(ts*SR); L=int(SR*0.9); x=np.arange(L)/SR; f=mf(m)
        env=np.exp(-x*5.5); v=(np.sin(2*np.pi*f*x+1.2*env*np.sin(2*np.pi*f*x))+0.3*np.sin(2*np.pi*f*2*x)*np.exp(-x*9))*env
        e=min(i0+L,n); mus[i0:e]+=0.05*v[:e-i0].astype(np.float32)*(0.75 if k%2 else 1)
    for k in range(4):  # kick + hat
        ts=t0+k*beat
        if ts>=T: break
        i0=int(ts*SR)
        if k%2==0:
            L=int(SR*0.25); x=np.arange(L)/SR; v=np.sin(2*np.pi*(52+60*np.exp(-x*30))*x)*np.exp(-x*14); e=min(i0+L,n); mus[i0:e]+=0.16*v[:e-i0]
        for h in (0,0.5):
            j0=int((ts+h*beat)*SR); L=int(SR*0.05)
            if j0+L<n: nz=rng.standard_normal(L); nz=nz-np.convolve(nz,np.ones(6)/6,'same'); mus[j0:j0+L]+=0.012*nz*np.exp(-np.arange(L)/SR*70)*(1.6 if h==0 else 1)
mus=lp(mus.astype(np.float64),5500).astype(np.float32)
mus*=np.clip(tt/0.6,0,1)*np.clip((T-tt)/1.6,0,1)
sfx=np.zeros(n,np.float32)
def pop(t,g):
    L=int(SR*0.18); x=np.arange(L)/SR; v=np.sin(2*np.pi*(380+900*np.exp(-x*40))*x)*np.exp(-x*28)*g
    i0=int(t*SR); e=min(i0+L,n); sfx[i0:e]+=v[:e-i0]
def chime(t,g):
    L=int(SR*1.4); x=np.arange(L)/SR; v=sum(a*np.sin(2*np.pi*f*x)*np.exp(-x*d) for f,a,d in [(1318.5,1,3.2),(1975.5,.6,4),(2637,.25,6),(3951,.1,8)])*g*0.5
    i0=int(t*SR); e=min(i0+L,n); sfx[i0:e]+=v[:e-i0]
for a,b,_,_,_,s in events:
    if s=="pop": pop(a,0.5)
    elif s=="chime": chime(a,0.8)
aud=np.stack([mus*0.9+sfx,mus*0.9+sfx],1)
aud=np.clip(aud/np.max(np.abs(aud))*0.9,-1,1)
with wave.open("work/audio.wav","wb") as w: w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((aud*32767).astype(np.int16).tobytes())
# 5. composite
dec=sp.Popen(["ffmpeg","-loglevel","error","-i","work/base.mp4","-f","rawvideo","-pix_fmt","rgb24","-"],stdout=sp.PIPE)
os.makedirs("output",exist_ok=True)
enc=sp.Popen(["ffmpeg","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i","work/audio.wav",
 "-af","loudnorm=I=-14:TP=-1.5:LRA=11","-c:v","libx264","-crf","17","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart","-shortest","output/loafer_tiktok.mp4"],stdin=sp.PIPE)
fi=0
while True:
    raw=dec.stdout.read(W*H*3)
    if len(raw)<W*H*3: break
    fr=np.frombuffer(raw,np.uint8).reshape(H,W,3).copy(); t=fi/FPS
    for a,b,spr,cx,cy,_ in events:
        if not(a<=t<b): continue
        k=ease_back((t-a)/0.28); al=min((t-a)/0.15,1)*min((b-t)/0.2,1); sc=0.82+0.18*k
        if sc<=0 or al<=0: continue
        h0,w0=spr.shape[:2]; sw,sh=max(int(w0*sc),1),max(int(h0*sc),1)
        s=np.asarray(Image.fromarray(spr.astype(np.uint8),"RGBA").resize((sw,sh),Image.BILINEAR)).astype(np.float32)
        x0,y0=int(cx-sw/2),int(cy-sh/2+(1-min((t-a)/0.28,1))*24)
        xa,ya,xb,yb=max(x0,0),max(y0,0),min(x0+sw,W),min(y0+sh,H)
        if xb<=xa or yb<=ya: continue
        s=s[ya-y0:yb-y0,xa-x0:xb-x0]; A=(s[...,3:4]/255)*al
        fr[ya:yb,xa:xb]=(fr[ya:yb,xa:xb]*(1-A)+s[...,:3]*A).astype(np.uint8)
    enc.stdin.write(fr.tobytes()); fi+=1
enc.stdin.close(); enc.wait(); print("frames",fi,"durasi",fi/FPS)
