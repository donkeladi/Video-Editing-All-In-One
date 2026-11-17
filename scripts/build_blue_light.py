#!/usr/bin/env python3
"""Video informative awareness: Blue light & mata.
Overlay (kad, carta, tip) + subtitle + SFX + muzik latar (ducking) + punch-in zoom.
Guna:  python3 scripts/build_blue_light.py [--preview t1,t2,...]
Timeline di bawah ialah masa dalam video ASAL (input/main.mov); OFF dibuang di depan.
"""
import subprocess as sp, numpy as np, os, wave, math, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = "input/main.mov"; OUT = "output/blue_light_awareness.mp4"
W, H, FPS = 1080, 1920, 30
OFF = 0.45; DUR = 68.3          # trim awal & panjang
SS = 2                           # supersample sprite
os.makedirs("work", exist_ok=True); os.makedirs("output", exist_ok=True)

# ---------- palet ----------
NAVY=(11,26,52); NAVY2=(22,44,84); CYAN=(56,200,248); AMBER=(251,191,36)
RED=(244,92,92); GREEN=(52,211,153); WHITE=(255,255,255); MUTE=(170,190,220)
FD="/usr/share/fonts/opentype/inter/Inter-%s.otf"
def F(w,s): return ImageFont.truetype(FD % w, int(s*SS))

# ---------- ucapan: segmen speech (dari silencedetect) + teks ----------
REGIONS = [
 ([(0.76,3.99)], "Ramai ingat blue light dari phone yang rosakkan mata kan?"),
 ([(4.33,9.86),(10.05,11.04)], "Menurut American Academy of Ophthalmology, tak ada bukti saintifik yang blue light dari gajet rosakkan mata."),
 ([(11.42,13.35)], "Masalah sebenar, kita lupa berkelip."),
 ([(13.54,17.79)], "Satu kajian dalam jurnal Clinical and Experimental Optometry"),
 ([(18.17,22.49)], "jumpa kelip mata jatuh dari 18 kali ke lebih kurang 4 kali seminit masa guna gajet."),
 ([(22.84,26.43),(27.29,30.62),(31.25,31.70),(32.45,34.51)], "Tapi Harvard Health cakap blue light memang paling mengganggu waktu malam, sebab dia kacau jam badan dan tidur kita."),
 ([(34.86,39.92),(40.67,45.15),(45.54,47.30)], "So rajin berkelip, rehat setiap 20 minit, letak phone sebelum tidur."),
 ([(48.04,49.28),(49.76,50.95),(51.17,53.15)], "Saya tambah satu rutin, DS Pharma Eye Care. Ada lobak merah,"),
 ([(53.48,58.59),(58.79,63.91)], "goji, avokado dan Eyebright, digunakan secara tradisional"),
 ([(64.36,65.34),(66.10,67.63)], "untuk kesihatan mata."),
]
NUMSYL={"18":4,"20":4,"4":2}
def syl(w):
    c=re.sub(r"[^\w]","",w).lower()
    if c in NUMSYL: return NUMSYL[c]
    return max(1,len(re.findall(r"[aeiou]+",c)))
def word_times():
    out=[]
    for segs,text in REGIONS:
        ws=text.split(); wt=[syl(w) for w in ws]; tot=sum(wt)
        total=sum(b-a for a,b in segs); acc=0.0
        def at(x):   # x dalam saat-pertuturan -> masa mutlak
            for a,b in segs:
                if x<=b-a+1e-9: return a+x
                x-=b-a
            return segs[-1][1]
        for w,s in zip(ws,wt):
            a=at(acc/tot*total); acc+=s; b=at(acc/tot*total); out.append((w,a,b))
    return out
WORDS=word_times()
def chunks():
    res=[];cur=[]
    def flush():
        if cur: res.append((cur[0][1],cur[-1][2],[c[0] for c in cur]))
    for w,a,b in WORDS:
        if cur and (a-cur[-1][2]>0.3 or len(cur)>=4 or sum(len(x[0])+1 for x in cur)+len(w)>26):
            flush(); cur.clear()
        cur.append((w,a,b))
        if re.search(r"[.,?]$",w): flush(); cur.clear()
    flush(); return res
CHUNKS=chunks()
def srt(path):
    ts=lambda t:"%02d:%02d:%02d,%03d"%(t//3600,t%3600//60,t%60,int(t%1*1000))
    with open(path,"w") as f:
        for i,(a,b,ws) in enumerate(CHUNKS,1):
            a=max(a-OFF,0);b=b-OFF+0.08
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{' '.join(ws)}\n\n")

# ---------- sprite helpers ----------
def canvas(w,h): return Image.new("RGBA",(int(w*SS),int(h*SS)),(0,0,0,0))
def rr(d,box,r,fill,outline=None,width=0):
    d.rounded_rectangle([int(v*SS) for v in box],int(r*SS),fill=fill,outline=outline,width=int(width*SS))
def tw(font,t): return font.getlength(t)/SS
def card_bg(w,h,r=34,fill=NAVY+(235,),pad=44,accent=None):
    im=canvas(w+pad*2,h+pad*2)
    sh=canvas(w+pad*2,h+pad*2); rr(ImageDraw.Draw(sh),(pad,pad+12,pad+w,pad+h+12),r,(0,0,0,110))
    im=Image.alpha_composite(im,sh.filter(ImageFilter.GaussianBlur(18*SS)))
    d=ImageDraw.Draw(im); rr(d,(pad,pad,pad+w,pad+h),r,fill,outline=(255,255,255,40),width=1.5)
    if accent: rr(d,(pad,pad+r*0.6,pad+9,pad+h-r*0.6),4,accent+(255,))
    return im,d,pad
def finish(im): return np.asarray(im.resize((im.width//SS,im.height//SS),Image.LANCZOS)).astype(np.float32)
# ikon
def ic_eye(d,cx,cy,s,col):
    cx*=SS;cy*=SS;s*=SS
    d.ellipse((cx-s,cy-s*0.55,cx+s,cy+s*0.55),outline=col,width=int(s*0.14))
    d.ellipse((cx-s*0.3,cy-s*0.3,cx+s*0.3,cy+s*0.3),fill=col)
def ic_clock(d,cx,cy,s,col):
    cx*=SS;cy*=SS;s*=SS
    d.ellipse((cx-s*0.8,cy-s*0.8,cx+s*0.8,cy+s*0.8),outline=col,width=int(s*0.14))
    d.line((cx,cy,cx,cy-s*0.5),fill=col,width=int(s*0.13)); d.line((cx,cy,cx+s*0.36,cy+s*0.2),fill=col,width=int(s*0.13))
def ic_moon(d,cx,cy,s,col,bg):
    cx*=SS;cy*=SS;s*=SS
    d.ellipse((cx-s*0.8,cy-s*0.8,cx+s*0.8,cy+s*0.8),fill=col); d.ellipse((cx-s*0.2,cy-s*1.0,cx+s*1.2,cy+s*0.5),fill=bg)
def ic_phone(d,cx,cy,s,col):
    cx*=SS;cy*=SS;s*=SS
    d.rounded_rectangle((cx-s*0.5,cy-s*0.85,cx+s*0.5,cy+s*0.85),int(s*0.16),outline=col,width=int(s*0.13))
    d.line((cx-s*0.14,cy+s*0.6,cx+s*0.14,cy+s*0.6),fill=col,width=int(s*0.1))
def ic_check(d,cx,cy,s,col):
    cx*=SS;cy*=SS;s*=SS
    d.line((cx-s*0.5,cy+s*0.02,cx-s*0.12,cy+s*0.4,cx+s*0.55,cy-s*0.4),fill=col,width=int(s*0.22),joint="curve")
def ic_cross(d,cx,cy,s,col):
    cx*=SS;cy*=SS;s*=SS
    d.line((cx-s*0.45,cy-s*0.45,cx+s*0.45,cy+s*0.45),fill=col,width=int(s*0.22)); d.line((cx-s*0.45,cy+s*0.45,cx+s*0.45,cy-s*0.45),fill=col,width=int(s*0.22))
def ic_badge(d,cx,cy,r,col,fn,ic_col=WHITE):
    d.ellipse(((cx-r)*SS,(cy-r)*SS,(cx+r)*SS,(cy+r)*SS),fill=col+(255,)); fn(d,cx,cy,r*0.62,ic_col)

# ---------- sprite generator ----------
def chip(text,col=AMBER,fg=NAVY,size=34):
    f=F("ExtraBold",size); w=tw(f,text)+size*1.9; h=size*2.0
    im,d,p=card_bg(w,h,h/2,col+(255,),pad=30)
    d.text(((p+w/2)*SS,(p+h/2)*SS),text,font=f,fill=fg,anchor="mm"); return finish(im)
def headline(lines,chipt=None,size=58,col=NAVY):
    f=F("ExtraBold",size); w=max(tw(f,l) for l in lines)+size*1.5; h=size*1.38*len(lines)+size*0.7
    im,d,p=card_bg(w,h,36,col+(238,),accent=CYAN)
    for i,l in enumerate(lines):
        d.text(((p+w/2+4)*SS,(p+size*0.35+size*1.38*(i+0.5))*SS),l,font=f,fill=WHITE,anchor="mm")
    return finish(im)
def source(label,name,sub=None,icon=None):
    fl=F("Bold",24); fn=F("ExtraBold",40); fs=F("Medium",28)
    w=max(tw(fn,name),tw(fs,sub or ""))+(130 if icon else 70)+30; h=118+(34 if sub else 0)
    im,d,p=card_bg(w,h,30,NAVY+(238,),accent=CYAN)
    x=p+36
    if icon: ic_badge(d,x+34,p+h/2,34,NAVY2,icon,CYAN); x+=88
    d.text((x*SS,(p+30)*SS),label,font=fl,fill=CYAN,anchor="lm")
    d.text((x*SS,(p+68)*SS),name,font=fn,fill=WHITE,anchor="lm")
    if sub: d.text((x*SS,(p+108)*SS),sub,font=fs,fill=MUTE,anchor="lm")
    return finish(im)
def myth(prog):   # kad "mitos" dgn garis coret + silang
    f=F("ExtraBold",46); t="Blue light gajet rosakkan mata"; w=tw(f,t)+200; h=190
    im,d,p=card_bg(w,h,34,NAVY+(238,),accent=RED)
    d.text(((p+44)*SS,(p+52)*SS),"ANGGAPAN RAMAI",font=F("Bold",24),fill=MUTE,anchor="lm")
    d.text(((p+44)*SS,(p+100)*SS),t,font=f,fill=WHITE,anchor="lm")
    L=tw(f,t); pr=min(prog/0.5,1)
    if pr>0: d.line(((p+44)*SS,(p+100)*SS,(p+44+L*pr)*SS,(p+100)*SS),fill=RED+(255,),width=int(7*SS))
    if prog>0.5:
        k=min((prog-0.5)/0.3,1); ic_badge(d,p+w-62,p+h/2,int(40*(0.6+0.4*k)),RED,ic_cross)
    d.text(((p+44)*SS,(p+152)*SS),"Tiada bukti saintifik",font=F("ExtraBold",34),fill=(*AMBER,255) if prog>0.5 else (0,0,0,0),anchor="lm")
    return finish(im)
def chart(prog):  # 18 -> ~4 kali seminit
    w,h=860,400; im,d,p=card_bg(w,h,38,NAVY+(240,),accent=CYAN)
    d.text(((p+46)*SS,(p+50)*SS),"KELIP MATA SEMINIT",font=F("Bold",28),fill=CYAN,anchor="lm")
    d.text(((p+w-46)*SS,(p+50)*SS),"Clin Exp Optom",font=F("Medium",24),fill=MUTE,anchor="rm")
    e=lambda x:1-(1-min(max(x,0),1))**3
    rows=[("Biasa",18,GREEN,0.0),("Guna gajet",4,AMBER,0.45)]
    for i,(lab,v,col,dl) in enumerate(rows):
        y=p+150+i*120; k=e((prog-dl)/0.45); x0=p+46
        d.text((x0*SS,(y-40)*SS),lab,font=F("SemiBold",28),fill=WHITE,anchor="lm")
        rr(d,(x0,y-12,x0+w-92-150,y+26),19,NAVY2+(255,))
        bw=(w-92-150)*(v/18)*k
        if bw>10: rr(d,(x0,y-12,x0+bw,y+26),19,col+(255,))
        num=int(round(v*k)) if i==0 else int(round(18-(18-v)*k)) if k>0 else 18
        if i==1: num=int(round(v*k)) if k>0 else 0
        d.text(((p+w-46)*SS,(y+6)*SS),("~" if i==1 and k>0.99 else "")+str(num),font=F("ExtraBold",64),fill=col,anchor="rm")
    return finish(im)
def tip(n,text,icon,col):
    f=F("ExtraBold",44); w=max(tw(f,text)+200,700); h=112
    im,d,p=card_bg(w,h,34,NAVY+(240,),accent=col)
    ic_badge(d,p+78,p+h/2,36,col,icon,NAVY if col!=CYAN else NAVY)
    d.text(((p+140)*SS,(p+h/2-2)*SS),text,font=f,fill=WHITE,anchor="lm")
    d.text(((p+w-40)*SS,(p+h/2)*SS),str(n),font=F("ExtraBold",56),fill=(255,255,255,60),anchor="rm")
    return finish(im)
def lowerthird(top,main):
    f=F("ExtraBold",56); fl=F("Bold",26); w=tw(f,main)+110; h=150
    im,d,p=card_bg(w,h,36,NAVY+(240,),accent=AMBER)
    d.text(((p+46)*SS,(p+42)*SS),top,font=fl,fill=AMBER,anchor="lm"); d.text(((p+46)*SS,(p+98)*SS),main,font=f,fill=WHITE,anchor="lm")
    return finish(im)
def pill(text,dot):
    f=F("Bold",38); w=tw(f,text)+120; h=84
    im,d,p=card_bg(w,h,h/2,(255,255,255,240),pad=26)
    r=17*SS; cy=(p+h/2)*SS; d.ellipse(((p+34)*SS-r,cy-r,(p+34)*SS+r,cy+r),fill=dot+(255,))
    d.text(((p+66)*SS,cy),text,font=f,fill=NAVY,anchor="lm"); return finish(im)
def footer(t):
    f=F("SemiBold",29); w=tw(f,t)+70; h=70
    im,d,p=card_bg(w,h,h/2,(0,0,0,150),pad=20)
    d.text(((p+w/2)*SS,(p+h/2)*SS),t,font=f,fill=WHITE,anchor="mm"); return finish(im)
ACC={"18","4","berkelip","harvard","health","ds","pharma","eye","care","eyebright","goji","avokado","lobak"}
def subtitle(ws):
    f=F("ExtraBold",56); sp=14
    ww=[tw(f,w) for w in ws]; w=sum(ww)+sp*(len(ws)-1)+40; h=100
    im=canvas(w+40,h+40); d=ImageDraw.Draw(im); x=40
    for t,l in zip(ws,ww):
        c=CYAN if re.sub(r"[^\w]","",t).lower() in ACC else WHITE
        d.text(((x)*SS,(20+h/2)*SS),t,font=f,fill=c,anchor="lm",stroke_width=int(7*SS),stroke_fill=(8,16,34,255)); x+=l+sp
    return finish(im)

# ---------- event (masa asal) ----------
EV=[]  # dict(a,b,sprite|fn,cx,cy,anim,sfx)
def ev(a,b,spr,cx,cy,anim="up",sfx=None,dyn=False): EV.append(dict(a=a,b=b,spr=spr,cx=cx,cy=cy,anim=anim,sfx=sfx,dyn=dyn))
TOP1,TOP2,LOW=150,300,1090
ev(0.95,3.95,chip("MITOS ATAU FAKTA?"),W//2,170,"pop","pop")
ev(1.15,3.95,headline(["Blue light rosakkan mata?"],size=56),W//2,300,"up","whoosh")
ev(4.4,9.8,source("SUMBER","American Academy of Ophthalmology",None,ic_eye),W//2,255,"up","whoosh")
ev(9.9,13.3,myth,W//2,1120,"up","thunk",dyn=True)
ev(11.5,17.9,chip("MASALAH SEBENAR",CYAN),W//2,170,"pop","pop")
ev(11.7,17.9,headline(["Kita lupa berkelip"],size=62),W//2,300,"up","impact")
ev(13.7,18.0,source("KAJIAN","Clin Exp Optom · 2019","Clinical and Experimental Optometry",ic_eye),W//2,LOW+30,"up","tick")
ev(18.2,22.6,chart,W//2,1180,"up","count",dyn=True)
ev(22.9,34.5,chip("HARVARD HEALTH",CYAN),W//2,170,"pop","whoosh")
ev(23.1,34.5,headline(["Blue light paling mengganggu","waktu malam"],size=48),W//2,320,"up","pop")
ev(27.4,34.5,tip("","Kacau jam badan & tidur",lambda d,x,y,s,c:ic_moon(d,x,y,s,c,AMBER),AMBER),W//2,LOW+30,"up","shimmer")
ev(34.9,47.4,chip("3 TIP MUDAH",GREEN),W//2,170,"pop","pop")
ev(35.0,47.4,tip(1,"Rajin berkelip",ic_eye,GREEN),W//2,1000,"up","ding1")
ev(40.7,47.4,tip(2,"Rehat setiap 20 minit",ic_clock,CYAN),W//2,1140,"up","ding2")
ev(45.6,47.4,tip(3,"Letak phone sebelum tidur",ic_phone,AMBER),W//2,1280,"up","ding3")
ev(48.1,49.7,chip("SAYA TAMBAH SATU RUTIN",AMBER),W//2,170,"pop","pop")
ev(49.8,64.0,lowerthird("RUTIN TAMBAHAN","DS Pharma Eye Care"),W//2,300,"up","whoosh")
for t,(lab,col) in zip([51.2,53.5,55.4,57.2],[("Lobak merah",(255,138,61)),("Goji",RED),("Avokado",(132,204,22)),("Eyebright",(168,130,255))]):
    ev(t,64.0,pill(lab,col),230,1070+[51.2,53.5,55.4,57.2].index(t)*100,"left","pop2")
ev(58.9,64.2,chip("DIGUNAKAN SECARA TRADISIONAL",CYAN,size=29),W//2,450,"pop","tick")
ev(64.4,68.7,footer("Sumber: AAO · Clin Exp Optom 2019 · Harvard Health"),W//2,1450,"up","chime")
SUBS=[dict(a=a,b=b+0.1,spr=subtitle(ws)) for a,b,ws in CHUNKS]

# ---------- animasi ----------
def back(x,c=1.6): x=min(max(x,0),1); return 1+(c+1)*(x-1)**3+c*(x-1)**2
def zoom(t):
    beats=[0.95,4.4,11.5,18.2,22.9,34.9,49.8]; z=0
    for b in beats:
        x=t-b
        if x<0 or x>3.6: continue
        v=min(x/0.5,1); v=v*v*(3-2*v)
        if x>2.4: u=(x-2.4)/1.2; v*=1-u*u*(3-2*u)
        z=max(z,v)
    return 1+0.055*z
def blit(fr,s,cx,cy,al):
    h0,w0=s.shape[:2]; x0,y0=int(cx-w0/2),int(cy-h0/2)
    xa,ya,xb,yb=max(x0,0),max(y0,0),min(x0+w0,W),min(y0+h0,H)
    if xb<=xa or yb<=ya or al<=0: return
    s=s[ya-y0:yb-y0,xa-x0:xb-x0]; A=(s[...,3:4]/255)*al
    fr[ya:yb,xa:xb]=(fr[ya:yb,xa:xb]*(1-A)+s[...,:3]*A).astype(np.uint8)
def scale(s,k):
    if abs(k-1)<0.004: return s
    im=Image.fromarray(s.astype(np.uint8),"RGBA"); return np.asarray(im.resize((max(int(im.width*k),1),max(int(im.height*k),1)),Image.BILINEAR)).astype(np.float32)

# ---------- audio ----------
SR=44100; N=int(SR*(DUR+0.4)); rng=np.random.default_rng(7)
def place(buf,t,x,g=1.0):
    i=int((t-OFF)*SR)
    if i<0: return
    e=min(i+len(x),len(buf)); buf[i:e]+=x[:e-i]*g
def env(L,a=0.003,d=10): x=np.arange(L)/SR; return np.minimum(x/a,1)*np.exp(-x*d)
def s_pop(f=700):
    L=int(SR*.16); x=np.arange(L)/SR; return np.sin(2*np.pi*(f*0.55+f*np.exp(-x*38))*x)*env(L,.002,26)*0.55
def s_whoosh():
    L=int(SR*.45); x=np.arange(L)/SR; n=rng.standard_normal(L)
    k=np.exp(-((x-.18)/.11)**2)  # bell
    # bandpass kasar: beza dua low-pass
    def lp(a,c):
        al=math.exp(-2*math.pi*c/SR); y=np.empty_like(a); s=0.
        for i in range(len(a)): s=(1-al)*a[i]+al*s; y[i]=s
        return y
    y=lp(n,2500)-lp(n,400); y/=np.max(np.abs(y))+1e-9
    return y*k*0.5
def s_tick(): L=int(SR*.05); return np.sin(2*np.pi*1900*np.arange(L)/SR)*env(L,.001,70)*0.4
def s_thunk():
    L=int(SR*.5); x=np.arange(L)/SR
    return (np.sin(2*np.pi*(60+90*np.exp(-x*20))*x)*env(L,.002,9)+0.4*np.sin(2*np.pi*190*x)*env(L,.002,16)*(x<.2))*0.9
def s_impact():
    L=int(SR*.7); x=np.arange(L)/SR
    n=rng.standard_normal(L)*np.exp(-x*30)*0.25
    return (np.sin(2*np.pi*(48+80*np.exp(-x*25))*x)*env(L,.002,6)+n)*0.85
def s_ding(f):
    L=int(SR*1.1); x=np.arange(L)/SR
    return (np.sin(2*np.pi*f*x)+0.35*np.sin(2*np.pi*2*f*x)*np.exp(-x*6)+0.15*np.sin(2*np.pi*3*f*x)*np.exp(-x*9))*env(L,.003,4.2)*0.45
def s_chime():
    L=int(SR*1.6); x=np.arange(L)/SR
    return sum(a*np.sin(2*np.pi*f*x)*np.exp(-x*d) for f,a,d in [(1318.5,1,3),(1975.5,.55,4),(2637,.25,6)])*0.28*np.minimum(x/.003,1)
def s_shimmer():
    L=int(SR*1.2); x=np.arange(L)/SR
    return sum(np.sin(2*np.pi*f*x)*env(L,.02,3.5)*0.2 for f in (880,1174.7,1568))*0.8
def s_count():   # tik cepat semasa kiraan + ding hujung
    out=np.zeros(int(SR*2.6))
    for k in range(10):
        t=0.15+k*0.075; i=int(t*SR); x=s_tick()*0.5*(0.8+0.04*k); out[i:i+len(x)]+=x
    d=s_ding(1046.5)*0.6; i=int(1.25*SR); out[i:i+len(d)]+=d[:len(out)-i]
    return out
SFX={"pop":lambda:s_pop(700),"pop2":lambda:s_pop(900),"whoosh":s_whoosh,"tick":s_tick,"thunk":s_thunk,"impact":s_impact,
     "ding1":lambda:s_ding(784),"ding2":lambda:s_ding(988),"ding3":lambda:s_ding(1175),"chime":s_chime,"shimmer":s_shimmer,"count":s_count}
def make_audio():
    cache={k:v() for k,v in SFX.items()}
    sfx=np.zeros(N)
    for e in EV:
        if not e["sfx"]: continue
        t=e["a"]
        if e["sfx"] in("whoosh",): place(sfx,t-0.05,cache["whoosh"],0.55)
        elif e["sfx"]=="count": place(sfx,t+0.2,cache["count"],0.9)
        else: place(sfx,t,cache[e["sfx"]],0.8)
    # muzik: pad lembut + pluck, 72 bpm, Cmaj7-Am7-Fmaj7-G6
    bpm=72; beat=60/bpm; bar=beat*4; tt=np.arange(N)/SR; mus=np.zeros(N)
    mf=lambda m:440*2**((m-69)/12)
    chords=[[48,55,59,64],[45,52,60,64],[41,48,55,64],[43,50,57,62]]
    for ci in range(int(DUR/bar)+2):
        ch=chords[ci%4]; t0=ci*bar
        for m in ch:
            for det in(-.003,.003):
                a=np.clip((tt-t0)/0.8,0,1)*np.clip(1-(tt-t0-bar+0.6)/0.6,0,1)*((tt>=t0)&(tt<t0+bar))
                mus+=0.05*np.sin(2*np.pi*mf(m)*(1+det)*tt)*a
        for k,m in enumerate([ch[3]+12,ch[2]+12,ch[1]+24,ch[2]+12,ch[3]+12,ch[1]+24,ch[2]+12,ch[1]+12]):
            ts=t0+k*beat/2; i0=int(ts*SR)
            if i0>=N: break
            L=int(SR*1.0); x=np.arange(L)/SR; f=mf(m); ev_=np.exp(-x*5)
            v=(np.sin(2*np.pi*f*x+1.0*ev_*np.sin(2*np.pi*f*x)))*ev_; e=min(i0+L,N); mus[i0:e]+=0.06*v[:e-i0]
    mus*=np.clip(tt/1.5,0,1)*np.clip((DUR-tt)/2.0,0,1)
    def wav(p,x):
        x=np.clip(x,-1,1); st=np.stack([x,x],1)
        with wave.open(p,"wb") as w: w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((st*32767).astype(np.int16).tobytes())
    wav("work/bl_music.wav",mus/np.max(np.abs(mus))*0.8); wav("work/bl_sfx.wav",sfx/max(np.max(np.abs(sfx)),1e-6)*0.9)

# ---------- composite ----------
def render_frame(fr,t):   # t = masa asal
    z=zoom(t)
    if z>1.001:
        cw,ch=W/z,H/z; x0=(W-cw)/2; y0=(H-ch)*0.35
        fr=np.asarray(Image.fromarray(fr).resize((W,H),Image.BICUBIC,box=(x0,y0,x0+cw,y0+ch)))
    fr=fr.copy()
    for e in EV:
        if not(e["a"]<=t<e["b"]): continue
        lt=t-e["a"]; k=back(lt/0.32); al=min(lt/0.18,1)*min((e["b"]-t)/0.22,1)
        s=e["spr"](min(lt/0.9,1)) if e["dyn"] else e["spr"]
        if e["dyn"] and e["spr"] is chart: s=chart(min(lt/1.0,1))
        sc=0.88+0.12*k if e["anim"]!="left" else 1.0
        s=scale(s,sc); dy=(1-min(lt/0.32,1))**2*40 if e["anim"]!="left" else 0
        dx=-(1-min(lt/0.3,1))**2*260 if e["anim"]=="left" else 0
        blit(fr,s,e["cx"]+dx,e["cy"]+dy,al)
    for c in SUBS:
        if c["a"]<=t<c["b"]:
            lt=t-c["a"]; blit(fr,c["spr"],W//2,1560+(1-min(lt/0.12,1))*14,min(lt/0.08,1)*min((c["b"]-t)/0.08,1)); break
    return fr
def main():
    srt("work/blue_light.srt")
    if len(sys.argv)>2 and sys.argv[1]=="--preview":
        for tt_ in sys.argv[2].split(","):
            t=float(tt_)
            raw=sp.run(["ffmpeg","-loglevel","error","-ss",str(t),"-i",SRC,"-frames:v","1","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
            fr=np.frombuffer(raw,np.uint8).reshape(H,W,3)
            Image.fromarray(render_frame(fr,t)).save(f"work/pv_{t:05.1f}.png")
        return
    make_audio()
    dec=sp.Popen(["ffmpeg","-loglevel","error","-ss",str(OFF),"-t",str(DUR),"-i",SRC,"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=sp.PIPE)
    af=("[1:a]highpass=f=70,acompressor=threshold=-22dB:ratio=3:attack=5:release=150,aformat=channel_layouts=stereo,asplit[v][vs];"
        "[2:a]lowpass=f=5200,volume=0.5[m];[m][vs]sidechaincompress=threshold=0.015:ratio=8:attack=20:release=500[md];"
        "[3:a]volume=1.0[s];[v][md][s]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    enc=sp.Popen(["ffmpeg","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
        "-ss",str(OFF),"-t",str(DUR),"-i",SRC,"-i","work/bl_music.wav","-i","work/bl_sfx.wav",
        "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","192k","-movflags","+faststart","-shortest",OUT],stdin=sp.PIPE)
    fi=0
    while True:
        raw=dec.stdout.read(W*H*3)
        if len(raw)<W*H*3: break
        fr=np.frombuffer(raw,np.uint8).reshape(H,W,3)
        enc.stdin.write(render_frame(fr,OFF+fi/FPS).tobytes()); fi+=1
    enc.stdin.close(); enc.wait(); print("frames",fi,"durasi",fi/FPS)
main()
