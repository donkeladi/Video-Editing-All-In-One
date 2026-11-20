#!/usr/bin/env python3
"""Edit video Eyebright: buang senyap, transisi xfade, zoom in/out beransur, subtitle ASS, -14 LUFS.
Guna: python3 scripts/make_cards.py && python3 scripts/edit_eyebright.py"""
import subprocess, os, re
SRC="input/eyebright.mov"; OUT="output/eyebright_final.mp4"
PAD=0.2; OV=0.2
# segmen ucapan (saat, video asal)
SEG=[(0.44,14.44),(16.22,28.12),(30.72,41.95),(43.36,58.0)]
# (mula, tamat, teks) ikut masa video asal; teks dibetulkan mengikut skrip
CH=[
(0.64,3.4,"Ada satu bunga, nama dia Eyebright."),
(3.5,6.0,"Orang Eropah dah guna berabad-abad."),
(6.2,8.2,"Dia digunakan secara tradisional"),
(8.3,10.4,"untuk mata yang merah dan radang."),
(10.5,14.2,"Sebab itu dinamakan Eyebright."),
(16.42,18.9,"Secara tradisional, orang guna juga"),
(18.9,21.9,"untuk hidung berair dan alahan bermusim."),
(22.1,24.4,"Kajian makmal pula jumpa ekstraknya"),
(24.5,27.9,"ada aktiviti antioksidan dan anti-radang."),
(30.92,32.0,"Tapi saya nak jujur,"),
(32.0,34.9,"kajian ke atas manusia masih terhad."),
(35.0,36.5,"Sebab itu, kita sebut"),
(36.5,38.9,"'digunakan secara tradisional',"),
(38.9,41.3,"bukan 'terbukti'."),
(43.56,47.4,"Tapi DS Pharma Eye Care ada ekstrak Eyebright."),
(47.5,49.2,"Berdaftar MAL22076147T,"),
(49.3,52.8,"digunakan secara tradisional untuk kesihatan mata."),
(52.9,54.6,"Jadi kalau nak dapatkan ni,"),
(54.5,57.9,"boleh cek bio sekarang. Bye bye!"),
]
# potongan kecil dalam segmen (jeda 0.2-0.5s) dibuang dengan jump-cut
GAPS=[(12.886,13.134),(20.07,20.354),(21.775,22.152),(35.519,35.845),(38.4445,38.872),(40.046,40.25),(40.461,40.741),(52.672,53.005)]
CP=0.06; DC=0.04  # pad & tempoh crossfade untuk jump-cut
P=[]  # (mula,tamat,durasi_transisi_sebelum)
for si,(a,b) in enumerate(SEG):
    cur=a; first=True
    for gs,ge in GAPS:
        if a<gs<b:
            P.append([cur,gs+CP,OV if (first and si>0) else DC]); first=False; cur=ge-CP
    P.append([cur,b,OV if (first and si>0) else DC])
P[0][2]=0
offs=[];prev_end=0
for i,(a,b,d) in enumerate(P):
    o=0 if i==0 else prev_end-d
    offs.append(o); prev_end=o+(b-a)
total=prev_end
def nt(t,start=True):
    for (a,b,d),o in zip(P,offs):
        if a-0.01<=t<=b+0.01: return o+t-a
    # jatuh dalam jurang yang dibuang
    if start:
        for (a,b,d),o in zip(P,offs):
            if a>t: return o
    else:
        for (a,b,d),o in reversed(list(zip(P,offs))):
            if b<t: return o+b-a
    raise ValueError(t)
def ts(t):
    h=int(t//3600);m=int(t%3600//60);s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"
os.makedirs("work",exist_ok=True); os.makedirs("output",exist_ok=True)
import json
# Palet Blueprint: latar #123361, teks #edf5ff, aksen #9be8ff (ASS = BGR)
ACC=r"{\1c&HFFE89B&}"; TXT=r"{\1c&HFFF5ED&}"; Y=ACC; W=TXT
MONO="DejaVu Sans Mono"; FONT="Inter"
KEYS={"eyebright","tradisional","terhad","terbukti","antioksidan","anti-radang","mal22076147t"}
def hl(w):
    k=re.sub(r"[^\w-]","",w).lower()
    return f"{ACC}{w}{TXT}" if k in KEYS else w
cs=[(nt(a,True),nt(b,False)) for a,b,t in CH]
ev=[]; TICKS=[]   # ev: (layer,start,end,style,text); TICKS: (masa,jenis)
# 1) sari kata kecil, perkataan demi perkataan
for (s_,e_),(a,b,t) in zip(cs,CH):
    ws=t.split(); L_=[len(w)+1 for w in ws]; tot=sum(L_); cum=0; ts_=[]
    for l in L_: ts_.append(s_+(e_-s_)*0.8*cum/tot); cum+=l
    for i in range(len(ws)):
        end=ts_[i+1] if i+1<len(ws) else e_
        shown=" ".join(hl(w) for w in ws[:i+1]); hid=" ".join(ws[i+1:])
        ev.append((0,ts_[i],end,"Cap",shown+(" {\\alpha&HFF&}"+hid if hid else "")))
# 2) kad bahagian ala blueprint, tajuk ditaip
CARDS=[(cs[5][0],"FAKTA 01",["Kegunaan","Tradisional"]),
       (cs[9][0],"FAKTA 02",["Kajian Manusia","Masih Terhad"]),
       (cs[14][0],"FAKTA 03",["Produk","Berdaftar"])]
CARD_D=1.7; CPS=0.035
LBL=r"{\fn"+MONO+r"\fs46\1c&HFFE89B&}"; TTL=r"{\fn"+FONT+r"\fs84\1c&HFFF5ED&}"
for t0,lab,lines in CARDS:
    full=[lab]+lines; n=sum(len(x) for x in full); TICKS.append((t0,"thunk"))
    for k in range(1,n+1):
        rem=k; out=[]
        for li,x in enumerate(full):
            take=x[:rem]; rem-=len(take)
            out.append((LBL+take+TTL) if li==0 else take)
            if rem<=0: break
        txt="\\N".join(out)+("\u2588" if k<n else "")
        st=t0+0.15+(k-1)*CPS; en=t0+0.15+k*CPS if k<n else t0+CARD_D
        ev.append((1,st,en,"Card",txt))
        if k%2==0 and k<n: TICKS.append((st,"tick"))
# 3) hook
ev.append((1,0.2,1.75,"Hook",r"{\fscx70\fscy70\t(0,180,\fscx108\fscy108)\t(180,300,\fscx100\fscy100)}EYEBRIGHT")); TICKS.append((0.2,"tick"))
ev.append((1,0.45,1.75,"HookSub",r"{\fad(150,0)}Bunga yang digunakan berabad-abad"))
# 4) frasa kunci (atas)
def pop(a,b,txt,y=130):
    TICKS.append((a,"tick"))
    ev.append((1,a,b,"Pop",r"{\an8\pos(540,%d)\fscx80\fscy80\t(0,160,\fscx106\fscy106)\t(160,260,\fscx100\fscy100)\fad(0,120)}"%y+txt))
pop(cs[6][0],cs[6][1],"Hidung berair &"+r"\N"+ACC+"alahan bermusim")
pop(cs[8][0],cs[8][1],ACC+"Antioksidan"+TXT+" &"+r"\N"+ACC+"Anti-radang")
pop(cs[12][0],cs[13][1],"Digunakan secara "+ACC+"tradisional"+TXT+r"\N"+"bukan "+ACC+"terbukti",y=110)
# 5) panel rajah pop-up (kad blueprint) + penanda bernombor
ing0=cs[14][0]+CARD_D+0.1
BR=[("flower",nt(2.2,True),nt(5.0,False),850,640,1.0),
    ("ingredients",ing0,nt(47.4,False),862,640,0.88),
    ("box_back",nt(47.5,True),nt(49.3,False),862,620,0.88),
    ("box_front",nt(49.3,True),nt(52.8,False),862,620,0.88)]
M=json.load(open("work/cards/cards.json"))
for name,a,b,cx,cy,kk in BR:
    m=M[name]; ox=cx-m["W"]*kk/2; oy=cy-m["H"]*kk/2; d=b-a; n=len(m["marks"]); sp=min(0.5,(d-1.0)/n)
    TICKS.append((a,"thunk"))
    for i,mk in enumerate(m["marks"]):
        t=a+0.5+i*sp; x0,y0,x1,y1=[mk["rect"][0]*kk+ox,mk["rect"][1]*kk+oy,mk["rect"][2]*kk+ox,mk["rect"][3]*kk+oy]
        TICKS.append((t,"tick2"))
        ev.append((3,t,b-0.12,"Draw",r"{\an7\pos(0,0)\p1\clip(%d,%d,%d,%d)\t(0,220,\clip(%d,%d,%d,%d))\fad(0,100)}m %d %d l %d %d %d %d %d %d %d %d"%(x0-4,y0-4,x0-4,y1+4,x0-4,y0-4,x1+4,y1+4,x0,y0,x1,y0,x1,y1,x0,y1,x0,y0)))
        ev.append((4,t+0.05,b-0.12,"Tag",r"{\an1\pos(%d,%d)\fad(60,100)}%02d"%(x0-2,y0-3,i+1)))
        ev.append((4,t+0.15,b-0.12,"Leg",r"{\an7\fs%d\pos(%d,%d)\fad(120,100)}"%(round(20*kk),ox+16*kk,oy+(m["legend_y"]+6)*kk+i*34*kk)+ACC+"%02d"%(i+1)+TXT+"  "+mk["label"]))
# ASS
ass=["[Script Info]","ScriptType: v4.00+","PlayResX: 1080","PlayResY: 1920","WrapStyle: 0","",
"[V4+ Styles]","Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
f"Style: Cap,{FONT},58,&H00FFF5ED,&H00FFF5ED,&H00331200,&H90000000,1,0,0,0,100,100,0,0,1,5,2,2,80,80,430,1",
f"Style: Card,{FONT},84,&H00FFF5ED,&H00FFF5ED,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,4,110,60,720,1",
f"Style: Hook,{FONT},120,&H00FFE89B,&H00FFE89B,&H00331200,&H90000000,1,0,0,0,100,100,2,0,1,6,3,8,60,60,150,1",
f"Style: HookSub,{FONT},46,&H00FFF5ED,&H00FFF5ED,&H00331200,&H90000000,1,0,0,0,100,100,0,0,1,4,2,8,60,60,300,1",
f"Style: Pop,{FONT},68,&H00FFF5ED,&H00FFF5ED,&H00331200,&H90000000,1,0,0,0,100,100,0,0,1,6,2,8,60,60,110,1",
f"Style: Draw,{FONT},20,&HFF000000,&HFF000000,&H00FFE89B,&H00000000,0,0,0,0,100,100,0,0,1,3,0,7,0,0,0,1",
f"Style: Tag,{MONO},24,&H00613312,&H00613312,&H00FFE89B,&H00000000,1,0,0,0,100,100,0,0,3,5,0,1,0,0,0,1",
f"Style: Leg,{MONO},20,&H00FFF5ED,&H00FFF5ED,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1","",
"[Events]","Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
for ly,a,b,st,tx in ev:
    ass.append(f"Dialogue: {ly},{ts(a)},{ts(b)},{st},,0,0,0,,{tx}")
open("work/eyebright.ass","w").write("\n".join(ass)+"\n")
# zoom: keyframe (masa,zoom) linear. Segmen duduk (C, chunk 9-13) zoom besar, anchor atas supaya riba/seluar tak nampak
ZO=1.13; ZC0,ZC1=1.5,1.62
def alt(idx, z):  # blok 2 chunk, zoom bergilir
    kf=[]
    for k in range(0,len(idx),2):
        grp=idx[k:k+2]; end=cs[grp[-1]][1] if k+2<len(idx) else None
        z=ZO if z==1.0 else 1.0
        if end is not None: kf.append((end,z))
    return kf,z
kf=[(0,1.0)]
k1,_=alt(list(range(0,9)),1.0)  # mula 1.0 -> 1.13 -> 1.0 ...
kf+= [(cs[8][0],kf[-1][1]) ] if False else k1
tC0=cs[9][0]; tC1=cs[13][1]; tD0=cs[14][0]
zprev=kf[-1][1]
kf+=[(tC0-0.15,zprev),(tC0+0.3,ZC0),(tC1,ZC1),(tD0-0.1,ZC1),(tD0+0.5,1.0)]
k2,_=alt(list(range(14,len(CH))),1.0)
kf+=k2+[(total+1,kf[-1][1] if k2 else 1.0)]
kf=sorted(set(kf))
expr=str(kf[-1][1])
for (t0,z0),(t1,z1) in reversed(list(zip(kf,kf[1:]))):
    if t1<=t0: continue
    expr=f"if(lt(t,{t1:.3f}),{z0}+({z1-z0:.3f})*(t-{t0:.3f})/{t1-t0:.3f},{expr})"
# filter graph
f=[]
for i,(a,b,d) in enumerate(P):
    f.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,fps=30[v{i}]")
    f.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[a{i}]")
pv,pa="v0","a0"
for i in range(1,len(P)):
    d=P[i][2]
    f.append(f"[{pv}][v{i}]xfade=transition=fade:duration={d}:offset={offs[i]:.3f}[x{i}]")
    f.append(f"[{pa}][a{i}]acrossfade=d={d}[c{i}]")
    pv,pa=f"x{i}",f"c{i}"
zz=f"({expr})"
f.append(f"[{pv}]scale=w='1080*{zz}':h='1920*{zz}':eval=frame:flags=bicubic,crop=w=1080:h=1920:x='(iw-ow)/2':y='(ih-oh)*(0.5-0.25*clip(({zz}-1.13)/0.37,0,1))',setsar=1,eq=contrast=1.06:saturation=1.04:brightness=0.01,colorbalance=bs=0.03:bm=0.02,vignette=PI/6.5,unsharp=5:5:0.5:5:5:0,format=yuv420p[zc]")
cur="zc"
for j,(name,a,b,cx,cy,kk) in enumerate(BR):
    d=b-a; k=j+1; wd=M[name]["W"]*kk
    f.append(f"[{k}:v]format=rgba,fade=t=in:st=0:d=0.3:alpha=1,fade=t=out:st={d-0.2:.3f}:d=0.2:alpha=1,scale=w='{wd}*(0.9+0.1*min(t/0.35,1))':h=-1:eval=frame:flags=bicubic,setpts=PTS+{a:.3f}/TB[L{k}]")
    f.append(f"[{cur}][L{k}]overlay=x='{cx}-w/2':y='{cy}-h/2':eval=frame:eof_action=pass:format=auto[o{k}]")
    cur=f"o{k}"
nb=len(BR)+1
en="+".join(f"between(t,{t0:.3f},{t0+CARD_D:.3f})" for t0,_,_ in CARDS)
f.append(f"[{cur}][{nb}:v]overlay=enable='{en}':format=auto[bg]")      # latar grid blueprint semasa kad Fakta
f.append(f"[bg][{nb+1}:v]overlay=format=auto[hud]")                      # grid halus + sudut HUD
f.append(f"[hud]ass=work/eyebright.ass[vout]")
f.append(f"[{pa}][{nb+2}:a]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-13:TP=-1.5:LRA=11[aout]")
open("work/filter.txt","w").write(";\n".join(f))
# SFX kod: bunyi tik mekanikal + bed sintetik perlahan (tiada audio berbayar)
import numpy as np, wave
sr=44100; n=int((total+1)*sr); au=np.zeros(n,dtype=np.float64); rng=np.random.default_rng(7)
tt=np.arange(n)/sr
bed=sum(np.sin(2*np.pi*fq*tt+ph) for fq,ph in [(110,0),(164.81,1.3),(220,2.1),(329.63,0.4)])
bed*=(0.6+0.4*np.sin(2*np.pi*0.11*tt))*10**(-44/20)/4
au+=bed
def add(t,x,g):
    i=int(t*sr)
    if i<n: x=x[:n-i]; au[i:i+len(x)]+=x*g
def mk_tick(f0,dur,noise):
    m=int(dur*sr); u=np.arange(m)/sr; e=np.exp(-u*(5/dur))
    return (np.sin(2*np.pi*f0*u)*0.7+rng.standard_normal(m)*noise)*e
tick=mk_tick(2600,0.012,0.4); thunk=mk_tick(140,0.09,0.05); tick2=np.concatenate([tick,np.zeros(int(0.045*sr)),tick*0.7])
for t,k in TICKS: add(t,{"tick":tick,"tick2":tick2,"thunk":thunk}[k],{"tick":0.10,"tick2":0.12,"thunk":0.35}[k])
au=np.clip(au,-1,1)
with wave.open("work/sfx.wav","wb") as w_:
    w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(sr); w_.writeframes((au*32767).astype("<i2").tobytes())
inp=["-i",SRC]
for name,a,b,*_ in BR: inp+=["-loop","1","-framerate","30","-t",f"{b-a:.3f}","-i",f"work/cards/{name}.png"]
for im in ("bg_grid","hud"): inp+=["-loop","1","-framerate","30","-t",f"{total+1:.2f}","-i",f"work/cards/{im}.png"]
inp+=["-i","work/sfx.wav"]
subprocess.run(["ffmpeg","-y"]+inp+["-filter_complex_script","work/filter.txt","-map","[vout]","-map","[aout]","-t",f"{total:.3f}",
 "-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-ar","44100","-movflags","+faststart",OUT],check=True)
print(OUT,total)
