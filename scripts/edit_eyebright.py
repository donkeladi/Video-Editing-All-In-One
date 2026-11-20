#!/usr/bin/env python3
"""Edit video Eyebright: buang senyap, transisi xfade, zoom in/out beransur, subtitle ASS, -14 LUFS.
Guna: python3 scripts/edit_eyebright.py"""
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
Y=r"{\1c&H1EC8FF&}"; W=r"{\1c&HFFFFFF&}"
KEYS={"eyebright","tradisional","terhad","terbukti","antioksidan","anti-radang","mal22076147t"}
def hl(w):
    k=re.sub(r"[^\w-]","",w).lower()
    return f"{Y}{w}{W}" if k in KEYS else w
cs=[(nt(a,True),nt(b,False)) for a,b,t in CH]
ev=[]  # (layer,start,end,style,text)
# 1) sari kata kecil, muncul perkataan demi perkataan
for (s_,e_),(a,b,t) in zip(cs,CH):
    ws=t.split(); L=[len(w)+1 for w in ws]; tot=sum(L); cum=0
    ts_=[]
    for l in L: ts_.append(s_+(e_-s_)*0.8*cum/tot); cum+=l
    for i in range(len(ws)):
        end=ts_[i+1] if i+1<len(ws) else e_
        shown=" ".join(hl(w) for w in ws[:i+1]); hid=" ".join(ws[i+1:])
        txt=shown+(" {\\alpha&HFF&}"+hid if hid else "")
        ev.append((0,ts_[i],end,"Cap",txt))
# 2) kad tajuk "Fakta #n" ala typewriter
CARDS=[(cs[5][0],"Fakta #1",["Kegunaan","Tradisional"]),
       (cs[9][0],"Fakta #2",["Kajian Manusia","Masih Terhad"]),
       (cs[14][0],"Fakta #3",["Produk","Berdaftar"])]
CARD_D=1.7; CPS=0.035
for t0,lab,lines in CARDS:
    full=[lab]+lines; n=sum(len(x) for x in full)
    for k in range(1,n+1):
        rem=k; out=[]
        for li,x in enumerate(full):
            take=x[:rem]; rem-=len(take)
            out.append((Y+take+W) if li==0 else take)
            if rem<=0: break
        txt="\\N".join(out)+("{\\alpha&HFF&}"+"" if False else "")
        if k<n: txt+="\u2588"
        st=t0+0.15+(k-1)*CPS; en=t0+0.15+k*CPS if k<n else t0+CARD_D
        ev.append((1,st,en,"Card",txt))
# 3) teks hook atas
ev.append((1,0.2,1.75,"Hook",r"{\fscx70\fscy70\t(0,180,\fscx108\fscy108)\t(180,300,\fscx100\fscy100)}EYEBRIGHT"))
ev.append((1,0.45,1.75,"HookSub",r"{\fad(150,0)}Bunga yang digunakan berabad-abad"))
# 4) pop-up frasa kunci (atas)
def pop(a,b,txt,y=130):
    ev.append((1,a,b,"Pop",r"{\an8\pos(540,%d)\fscx80\fscy80\t(0,160,\fscx106\fscy106)\t(160,260,\fscx100\fscy100)\fad(0,120)}"%y+txt))
pop(cs[6][0],cs[6][1],"Hidung berair &"+r"\N"+Y+"alahan bermusim")
pop(cs[8][0],cs[8][1],Y+"Antioksidan"+W+" &"+r"\N"+Y+"Anti-radang")
pop(cs[12][0],cs[13][1],"Digunakan secara "+Y+"tradisional"+W+r"\N"+"bukan "+Y+"terbukti",y=110)
# 5) B-roll (masa akhir) + pill pop-up bahan
ing0=cs[14][0]+CARD_D+0.1
BR=[("input/broll/flower.jpg",nt(2.2,True),nt(5.0,False)),
    ("input/broll/poster_ingredients.jpg",ing0,nt(47.4,False)),
    ("input/broll/box_back_crop.jpg",nt(47.5,True),nt(49.2,False)),
    ("input/broll/box_front.jpg",nt(49.3,True),nt(52.8,False))]
def pill(a,b,txt,y):
    ev.append((2,a,b,"Pill",r"{\an5\pos(540,%d)\fscx50\fscy50\t(0,150,\fscx112\fscy112)\t(150,260,\fscx100\fscy100)\fad(0,120)}"%y+txt))
pill(ing0+0.5,BR[1][2],"Ekstrak Eyebright 40mg",1330)
pill(BR[2][1]+0.2,BR[2][2],"Berdaftar: MAL22076147T",1090)
# ASS
FONT="Inter"
ass=["[Script Info]","ScriptType: v4.00+","PlayResX: 1080","PlayResY: 1920","WrapStyle: 0","",
"[V4+ Styles]","Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
f"Style: Cap,{FONT},58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,5,2,2,80,80,430,1",
f"Style: Card,{FONT},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,4,110,60,720,1",
f"Style: Hook,{FONT},120,&H001EC8FF,&H001EC8FF,&H00000000,&H90000000,1,0,0,0,100,100,2,0,1,6,3,8,60,60,150,1",
f"Style: HookSub,{FONT},46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,4,2,8,60,60,300,1",
f"Style: Pop,{FONT},68,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,0,0,1,6,2,8,60,60,110,1",
f"Style: Pill,{FONT},54,&H00101010,&H00101010,&H001EC8FF,&H00000000,1,0,0,0,100,100,0,0,3,20,0,5,60,60,0,1","",
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
f.append(f"[{pv}]scale=w='1080*{zz}':h='1920*{zz}':eval=frame:flags=bicubic,crop=w=1080:h=1920:x='(iw-ow)/2':y='(ih-oh)*(0.5-0.25*clip(({zz}-1.13)/0.37,0,1))',setsar=1,eq=contrast=1.07:saturation=1.12:gamma=0.97,colorbalance=rs=0.04:rm=0.03:bm=-0.03:bs=-0.04,vignette=PI/5.5,unsharp=5:5:0.5:5:5:0,format=yuv420p[zc]")
cur="zc"
for j,(fn,a,b) in enumerate(BR):
    d=b-a; k=j+1
    f.append(f"[{k}:v]split[bg{k}][fg{k}]")
    f.append(f"[bg{k}]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:5,eq=brightness=-0.08[bb{k}]")
    f.append(f"[fg{k}]scale=w='1000*(1+0.05*t/{d:.3f})':h='1200*(1+0.05*t/{d:.3f})':force_original_aspect_ratio=decrease:eval=frame:flags=bicubic[ff{k}]")
    f.append(f"[bb{k}][ff{k}]overlay=x='(W-w)/2':y='H*0.40-h/2':eval=frame,format=yuva420p,fade=t=in:st=0:d=0.15:alpha=1,fade=t=out:st={d-0.15:.3f}:d=0.15:alpha=1,setpts=PTS+{a:.3f}/TB[L{k}]")
    f.append(f"[{cur}][L{k}]overlay=eof_action=pass:format=auto[o{k}]")
    cur=f"o{k}"
# kad hitam + grain semasa kad tajuk
for ci,(t0,_,_) in enumerate(CARDS):
    en=f"between(t,{t0:.3f},{t0+CARD_D:.3f})"
    f.append(f"[{cur}]format=yuv420p,drawbox=x=0:y=0:w=iw:h=ih:color=black@1:t=fill:enable='{en}',noise=alls=16:allf=t:enable='{en}'[cd{ci}]")
    cur=f"cd{ci}"
# light leak: oren/merah di mula kad, biru-putih di hujung kad
LK=[]
for t0,_,_ in CARDS:
    LK.append((t0-0.05,"0xffb040","0x701000",1.0)); LK.append((t0+CARD_D-0.1,"0xb0d0ff","0x101840",0.7))
for m,(a,c0,c1,op) in enumerate(LK):
    k=len(BR)+1+m; a=max(a,0)
    env=f"if(between(T,{a:.3f},{a+0.12:.3f}),(T-{a:.3f})/0.12,if(between(T,{a+0.12:.3f},{a+0.57:.3f}),1-(T-{a+0.12:.3f})/0.45,0))"
    f.append(f"[{k}:v]scale=1080:1920,format=gbrp[lk{m}]")
    f.append(f"[{cur}]format=gbrp[ba{m}]")
    f.append(f"[ba{m}][lk{m}]blend=all_expr='A+(255-A)*(B/255)*{op}*{env}',format=yuv420p[lb{m}]")
    cur=f"lb{m}"
f.append(f"[{cur}]ass=work/eyebright.ass[vout]")
f.append(f"[{pa}]loudnorm=I=-13:TP=-1.5:LRA=11[aout]")
open("work/filter.txt","w").write(";\n".join(f))
subprocess.run(["ffmpeg","-y","-i",SRC]+sum([["-loop","1","-framerate","30","-t",f"{b-a:.3f}","-i",fn] for fn,a,b in BR],[])+sum([["-f","lavfi","-i",f"gradients=s=270x480:r=30:d={total+1:.2f}:c0={c0}:c1={c1}:x0=230:y0=60:x1=20:y1=420:type=1"] for a,c0,c1,op in LK],[])+["-filter_complex_script","work/filter.txt","-map","[vout]","-map","[aout]","-t",f"{total:.3f}",
 "-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-ar","44100","-movflags","+faststart",OUT],check=True)
print(OUT,total)
