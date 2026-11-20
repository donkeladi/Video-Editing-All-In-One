#!/usr/bin/env python3
"""Edit video Eyebright: buang senyap, transisi xfade, zoom in/out beransur, subtitle ASS, -14 LUFS.
Guna: python3 scripts/edit_eyebright.py"""
import subprocess, os
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
ass=["[Script Info]","ScriptType: v4.00+","PlayResX: 1080","PlayResY: 1920","WrapStyle: 0","",
"[V4+ Styles]","Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
"Style: Default,Inter,70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,2,2,70,70,430,1","",
"[Events]","Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
cs=[]
for a,b,t in CH:
    s_,e_=nt(a,True),nt(b,False); cs.append((s_,e_))
    ass.append(f"Dialogue: 0,{ts(s_)},{ts(e_)},Default,,0,0,0,,{{\\fad(80,80)}}{t}")
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
# B-roll cutaway (masa video asal): (fail, mula, tamat)
BR=[("input/broll/flower.jpg",2.2,5.0),
    ("input/broll/poster_box.jpg",43.56,45.4),
    ("input/broll/poster_ingredients.jpg",45.4,47.4),
    ("input/broll/box_back_crop.jpg",47.5,49.2),
    ("input/broll/box_front.jpg",49.3,52.8)]
BR=[(f,nt(a,True),nt(b,False)) for f,a,b in BR]
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
f.append(f"[{pv}]scale=w='1080*{zz}':h='1920*{zz}':eval=frame:flags=bicubic,crop=w=1080:h=1920:x='(iw-ow)/2':y='(ih-oh)*(0.5-0.25*clip(({zz}-1.13)/0.37,0,1))',setsar=1,format=yuv420p[zc]")
cur="zc"
for j,(fn,a,b) in enumerate(BR):
    d=b-a; k=j+1
    f.append(f"[{k}:v]split[bg{k}][fg{k}]")
    f.append(f"[bg{k}]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:5,eq=brightness=-0.08[bb{k}]")
    f.append(f"[fg{k}]scale=w='1000*(1+0.05*t/{d:.3f})':h='1200*(1+0.05*t/{d:.3f})':force_original_aspect_ratio=decrease:eval=frame:flags=bicubic[ff{k}]")
    f.append(f"[bb{k}][ff{k}]overlay=x='(W-w)/2':y='H*0.40-h/2':eval=frame,format=yuva420p,fade=t=in:st=0:d=0.15:alpha=1,fade=t=out:st={d-0.15:.3f}:d=0.15:alpha=1,setpts=PTS+{a:.3f}/TB[L{k}]")
    f.append(f"[{cur}][L{k}]overlay=eof_action=pass:format=auto[o{k}]")
    cur=f"o{k}"
f.append(f"[{cur}]ass=work/eyebright.ass[vout]")
f.append(f"[{pa}]loudnorm=I=-13:TP=-1.5:LRA=11[aout]")
open("work/filter.txt","w").write(";\n".join(f))
subprocess.run(["ffmpeg","-y","-i",SRC]+sum([["-loop","1","-framerate","30","-t",f"{b-a:.3f}","-i",fn] for fn,a,b in BR],[])+["-filter_complex_script","work/filter.txt","-map","[vout]","-map","[aout]",
 "-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-ar","44100","-movflags","+faststart",OUT],check=True)
print(OUT,total)
