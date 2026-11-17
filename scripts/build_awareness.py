#!/usr/bin/env python3
"""Video awareness: overlay kad (atas kepala) + subtitle ASS + render. Guna: python3 scripts/build_awareness.py"""
import subprocess, re, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
U="/root/.claude/uploads/f6b10760-ddb2-572d-9c95-1df23dac6b88/"
IMG=dict(label_back=U+"22ade47d-image.jpg", label_front=U+"5e43e111-image.jpg", goji=U+"0384672c-image.webp",
         avocado=U+"604253c5-image.webp", carrot=U+"f49dedf6-image.webp", euph=U+"0cbb2955-image.jpg", study=U+"8e6a26b5-image.png")
W=1080; SS=2
F=lambda s,b="Bold":ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{b}.otf",s*SS)
NAVY=(14,20,56,235); TEAL=(94,209,181); PURP=(122,76,214); WHITE=(255,255,255); YEL=(255,210,63); GREY=(188,196,230)
T0,T1=1.2,34.0   # trim senyap awal/akhir

# ---------- masa perkataan (anggaran dari silencedetect + panjang aksara) ----------
SCRIPT="Kerja dalam ofis aircond, mata cepat kering? Satu kajian pekerja pejabat UiTM Puncak Alam jumpa, simptom mata kering paling ketara dalam bilik aircond. Tambah pulak menghadap skrin 8 jam. Patutlah mata penat! Ni DS Pharma Eye Care, tablet kunyah yang digunakan secara tradisional untuk kesihatan mata. Senang bawa dalam beg. Ada MAL dengan hologram KKM. Tekan beg kuning!"
RUNS=[(1.33,4.20),(4.64,8.77),(9.05,12.33),(12.67,14.91),(15.36,16.43),(16.81,22.74),(23.06,26.37),(27.34,33.64)]
words=SCRIPT.split(); wt=[len(w)+1 for w in words]; tot=sum(wt); spk=sum(b-a for a,b in RUNS)
def at(c):  # c = kedudukan kumulatif berat -> saat
    s=c/tot*spk
    for a,b in RUNS:
        if s<=b-a: return a+s
        s-=b-a
    return RUNS[-1][1]
starts=[];c=0
for w,x in zip(words,wt): starts.append(at(c)); c+=x
ends=[at(sum(wt[:i+1])) for i in range(len(words))]
import json
_w=json.load(open("work/words.json"))
_fix="Kerja dalam ofis aircond, mata cepat kering? Satu kajian pekerja pejabat UiTM Puncak Alam jumpa, simptom mata kering paling ketara dalam bilik aircond. Tambah pulak menghadap skrin 8 jam. Patutlah mata penat! Ni DS Pharma Eye Care, tablet kunyah yang digunakan secara tradisional untuk kesihatan mata. Senang bawa dalam beg. Ada MAL dengan hologram KKM. Tekan beg kuning! Sekarang untuk dapatkan stok. Dia terhad tau, tak banyak. Siapa cepat dia dapat. Bye bye!".split()
_st=[];_en=[]
for a,b,t in _w:
    if t.upper().startswith("NDS"): m=(a+b)/2 if b-a<0.5 else a+0.26; _st+= [a,m]; _en+=[m,b]
    else: _st.append(a); _en.append(b)
assert len(_st)==len(_fix),(len(_st),len(_fix))
_st[0]=1.33
words=_fix; starts=_st; ends=[min(e,_st[i+1]) if i+1<len(_st) else e for i,e in enumerate(_en)]
def widx(txt,after=0):
    t=txt.split(); n=[i for i in range(after,len(words)) if [re.sub(r'[^\w]','',x) for x in words[i:i+len(t)]]==[re.sub(r'[^\w]','',x) for x in t]]
    return n[0]
def span(a,b): # perkataan a..b (frasa) -> (mula,tamat) relatif trim
    i=widx(a); j=widx(b,i)+len(b.split())-1
    return starts[i]-T0, ends[j]-T0

# ---------- helper lukis ----------
def card(h,fill=NAVY):
    im=Image.new("RGBA",(960*SS,h*SS),(0,0,0,0)); d=ImageDraw.Draw(im)
    sh=Image.new("RGBA",im.size,(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle((8*SS,12*SS,952*SS,(h-2)*SS),36*SS,fill=(0,0,0,120))
    sh=sh.filter(ImageFilter.GaussianBlur(14*SS)); im.alpha_composite(sh)
    d=ImageDraw.Draw(im); d.rounded_rectangle((0,0,960*SS-1,h*SS-1),36*SS,fill=fill,outline=TEAL+(255,),width=3*SS)
    d.rounded_rectangle((0,0,14*SS,h*SS-1),6*SS,fill=PURP+(255,))
    return im,d
def fit(path,w,h,circle=False,box=None):
    im=Image.open(path).convert("RGB")
    if box: im=im.crop(box)
    r=max(w/im.width,h/im.height); im=im.resize((int(im.width*r)+1,int(im.height*r)+1),Image.LANCZOS)
    l=(im.width-w)//2; t=(im.height-h)//2; im=im.crop((l,t,l+w,t+h)).convert("RGBA")
    m=Image.new("L",im.size,0); ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),(w//2 if circle else 22*SS),fill=255); im.putalpha(m); return im
def text(d,xy,s,f,fill=WHITE,anchor="la"): d.text((xy[0]*SS,xy[1]*SS),s,font=f,fill=fill,anchor=anchor)
def save(im,name): im.resize((960,im.height//SS),Image.LANCZOS).save(f"work/ov/{name}.png")

# 1 Kajian UiTM
im,d=card(340)
st=fit(IMG["study"],440*SS,300*SS,box=(60,150,860,700)); im.alpha_composite(st,(34*SS,20*SS))
text(d,(500,36),"KAJIAN PEKERJA PEJABAT",F(25,"SemiBold"),TEAL)
text(d,(500,74),"UiTM Puncak Alam",F(46),WHITE)
text(d,(500,142),"Soal selidik OSDI · 43 pekerja",F(26,"Medium"),GREY)
text(d,(500,184),"Dr. Anis Asyiekin Zainudin",F(26,"Medium"),GREY)
d.rounded_rectangle((500*SS,246*SS,920*SS,300*SS),27*SS,fill=(34,48,110,255))
text(d,(520,273),"Sumber: ir.uitm.edu.my",F(27,"SemiBold"),YEL,"lm"); save(im,"study")

# 2 Stat 69.8%
im,d=card(340)
cx,cy,R=190,170,118; bb=((cx-R)*SS,(cy-R)*SS,(cx+R)*SS,(cy+R)*SS)
d.ellipse(bb,outline=(255,255,255,40),width=30*SS)
d.arc(bb,-90,-90+360*0.698,fill=TEAL+(255,),width=30*SS)
text(d,(cx,cy-8),"69.8%",F(54),WHITE,"mm"); text(d,(cx,cy+40),"7 dari 10",F(26,"SemiBold"),TEAL,"mm")
text(d,(400,40),"Pekerja pejabat dikesan",F(34,"SemiBold"),GREY); text(d,(400,86),"simptom mata kering",F(46),WHITE)
d.rounded_rectangle((400*SS,170*SS,920*SS,300*SS),26*SS,fill=(34,48,110,255),outline=TEAL+(255,),width=2*SS)
text(d,(424,198),"Paling ketara dalam",F(30,"SemiBold"),GREY); text(d,(424,240),"bilik berhawa dingin",F(40),YEL)
save(im,"stat")

# 3 Skrin 8 jam
im,d=card(220)
cx0,cy0=110,110; d.rounded_rectangle((52*SS,60*SS,170*SS,142*SS),12*SS,outline=TEAL+(255,),width=7*SS)
d.rectangle((100*SS,146*SS,122*SS,164*SS),fill=TEAL+(255,)); d.rounded_rectangle((78*SS,164*SS,144*SS,174*SS),4*SS,fill=TEAL+(255,))
text(d,(220,42),"Menghadap skrin",F(34,"SemiBold"),GREY); text(d,(220,88),"8 JAM",F(78),YEL)
text(d,(500,134),"sehari",F(40,"SemiBold"),WHITE); text(d,(220,178),"Mata penat, kering & pedih",F(28,"Medium"),GREY)
for i in range(8):
    x=640+i*34; d.rounded_rectangle((x*SS,60*SS,(x+24)*SS,100*SS),8*SS,fill=(YEL if i<8 else GREY)+(255,)) if False else None
save(im,"screen")

# 4 Produk + bahan
im,d=card(400)
text(d,(46,28),"DS PHARMA",F(27,"SemiBold"),TEAL); text(d,(46,64),"EYE CARE",F(60),WHITE)
text(d,(420,92),"Tablet kunyah 650mg · 10 biji",F(27,"Medium"),GREY)
ing=[("carrot","Lobak merah","60mg"),("avocado","Avokado","15mg"),("goji","Goji berry","50mg"),("euph","Eyebright","40mg")]
for i,(k,n,mg) in enumerate(ing):
    x=46+i*222; ph=fit(IMG[k],130*SS,130*SS,circle=True); im.alpha_composite(ph,(x*SS+24*SS,140*SS))
    d.ellipse((x*SS+24*SS,140*SS,x*SS+154*SS,270*SS),outline=TEAL+(255,),width=4*SS)
    text(d,(x+89,296),n,F(27,"SemiBold"),WHITE,"mm"); text(d,(x+89,336),mg,F(32),YEL,"mm")
text(d,(480,382),"Digunakan secara tradisional untuk kesihatan mata",F(20,"Medium"),GREY,"mm")
save(im,"product")

# 5 Mudah dibawa
im,d=card(200)
d.rounded_rectangle((50*SS,50*SS,170*SS,150*SS),18*SS,fill=PURP+(255,))
for i in range(5):
    for j in range(2): d.ellipse(((66+i*20)*SS,(72+j*40)*SS,(82+i*20)*SS,(88+j*40)*SS),fill=WHITE)
text(d,(210,48),"Senang dibawa",F(48),WHITE); text(d,(210,112),"Muat dalam beg · 10 tablet kunyah",F(29,"Medium"),GREY)
save(im,"carry")

# 6 MAL + hologram
im,d=card(330)
hl=fit(IMG["label_front"],400*SS,184*SS,box=(552,742,960,935)); im.alpha_composite(hl,(40*SS,40*SS))
d.rounded_rectangle((40*SS,40*SS,440*SS,224*SS),22*SS,outline=YEL+(255,),width=4*SS)
text(d,(240,262),"Hologram KKM pada kotak",F(24,"SemiBold"),GREY,"mm")
text(d,(480,44),"DIDAFTARKAN",F(25,"SemiBold"),TEAL); text(d,(480,86),"No. MAL",F(34,"SemiBold"),GREY)
text(d,(480,138),"MAL22076147T",F(52),WHITE)
d.rounded_rectangle((480*SS,230*SS,900*SS,290*SS),30*SS,fill=(34,48,110,255),outline=TEAL+(255,),width=2*SS)
text(d,(690,260),"Semak di NPRA / KKM",F(27,"SemiBold"),YEL,"mm")
save(im,"mal")

# 7 CTA
im,d=card(200,fill=(250,196,30,245)); d.rounded_rectangle((0,0,14*SS,200*SS),6*SS,fill=PURP+(255,))
text(d,(480,76),"TEKAN BEG KUNING!",F(66),(40,22,80),"mm"); text(d,(480,148),"Dapatkan DS Pharma Eye Care sekarang",F(30,"SemiBold"),(70,40,110),"mm")
save(im,"cta")

# 8 Stok terhad
im,d=card(220,fill=(122,76,214,245)); d.rounded_rectangle((0,0,14*SS,220*SS),6*SS,fill=TEAL+(255,))
text(d,(480,78),"STOK TERHAD",F(66),WHITE,"mm"); text(d,(480,152),"Siapa cepat, dia dapat!",F(40,"SemiBold"),YEL,"mm"); save(im,"stok")

# ---------- timeline overlay: (png, mula, tamat, y) ----------
def S(w,occ=0): return starts[widx(w)]-T0
def E(w,after_w): i=widx(after_w); return ends[widx(w,i)]-T0
TL=[("study",S("Satu kajian")-0.1,E("jumpa,","Satu kajian")+0.3,50),
    ("stat",S("simptom mata")-0.1,E("aircond.","simptom mata")+0.5,50),
    ("screen",S("Tambah pulak")-0.1,E("penat!","Patutlah")+0.5,90),
    ("product",S("Ni DS")-0.1,E("mata.","kesihatan")+0.4,30),
    ("carry",S("Senang bawa")-0.1,E("beg.","Senang bawa")+0.2,90),
    ("mal",S("Ada MAL")-0.1,E("KKM.","Ada MAL")+0.5,50),
    ("cta",S("Tekan beg")-0.1,E("kuning!","Tekan beg")+0.2,90),
    ("stok",S("Sekarang untuk")-0.1,E("dapat.","Siapa cepat")+0.8,90)]
TL=[(n,s0,(min(e0,TL[k+1][1]-0.1) if k+1<len(TL) else e0),y) for k,(n,s0,e0,y) in enumerate(TL)]
print(TL)

# ---------- ASS subtitle ----------
def ts(t): h=int(t//3600);m=int(t%3600//60);s=t%60; return f"{h}:{m:02d}:{s:05.2f}"
KEY={"stok.":1,"terhad":1,"terhad,":1,"aircond":1,"aircond,":1,"aircond.":1,"kering":1,"kering?":1,"UiTM":1,"8":1,"jam.":1,"KKM.":1,"MAL":1,"kuning!":1,"tradisional":1,"hologram":1}
ev=[];i=0
while i<len(words):
    j=i+1
    while j<len(words) and j-i<4 and not words[j-1][-1] in ",.?!" and sum(len(x) for x in words[i:j+1])<=24: j+=1
    if j<len(words) and len(words)-j==1 and not words[j-1][-1] in ",.?!": j+=1
    chunk=words[i:j]; s_=starts[i]-T0; e_=min(ends[j-1]-T0+0.15,starts[j]-T0 if j<len(words) else 1e9)
    txt=" ".join(("{\\c&H3FD2FF&}"+w+"{\\c&HFFFFFF&}") if w in KEY else w for w in chunk).upper()
    ev.append(f"Dialogue: 0,{ts(max(s_,0))},{ts(e_)},Main,,0,0,0,,{{\\fad(60,40)}}{txt}"); i=j
ass=f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Main,Inter,68,&H00FFFFFF,&H00FFFFFF,&H00301810,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,60,60,300,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""+"\n".join(ev)
open("work/main.ass","w").write(ass)
open("work/main_est.srt","w").write("".join(f"{k+1}\n{e.split(',')[1].replace('.',',')} --> {e.split(',')[2].replace('.',',')}\n{re.sub(r'{.*?}','',e.split(',,')[-1])}\n\n" for k,e in enumerate(ev)))

# ---------- ffmpeg ----------
inp=["-ss",str(T0),"-to",str(T1),"-i","work/main.mov"]; fc=["[0:v]eq=contrast=1.06:saturation=1.12,format=yuv420p[v0]"]
last="v0"
for n,(png,s,e,y) in enumerate(TL,1):
    inp+=["-loop","1","-framerate","30","-t",f"{T1-T0:.2f}","-i",f"work/ov/{png}.png"]
    fc.append(f"[{n}:v]format=rgba,fade=t=in:st={s:.2f}:d=0.35:alpha=1,fade=t=out:st={e-0.3:.2f}:d=0.3:alpha=1[o{n}]")
    fc.append(f"[{last}][o{n}]overlay=x=60:y='{y}-30*max(0,1-(t-{s:.2f})/0.35)':enable='between(t,{s:.2f},{e:.2f})':eval=frame[v{n}]"); last=f"v{n}"
fc.append(f"[{last}]ass=work/main.ass:fontsdir=/usr/share/fonts/opentype/inter[vout]")
fc.append("[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
cmd=["ffmpeg","-y","-hide_banner","-loglevel","error"]+inp+["-filter_complex",";".join(fc),"-map","[vout]","-map","[aout]",
 "-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart","output/eye-care-awareness.mp4"]
subprocess.run(cmd,check=True); print("OK")
