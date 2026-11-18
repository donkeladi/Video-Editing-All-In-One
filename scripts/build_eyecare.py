#!/usr/bin/env python3
"""Render akhir video DS Pharma Eye Care: overlay grafik animasi + subtitle (ASS) + grade + audio -14 LUFS.
Guna: python3 scripts/build_eyecare.py work/rough.mp4 output/eyecare_awareness.mp4
Masa semua relatif kepada work/rough.mp4 (hasil rough_cut_eyecare.py)."""
import subprocess, sys, math, re, os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 1080, 1920
BAND_Y, BAND_H = 64, 640          # jalur overlay atas
FPS = 30
FD = "/usr/share/fonts/opentype/inter/"
def font(w, size): return ImageFont.truetype(FD + f"Inter-{w}.otf", size)
TEAL, PURPLE, WHITE, GREY = (79, 209, 197), (124, 77, 255), (255, 255, 255), (200, 205, 225)

dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",SRC]).decode())

# ---------- kad overlay ----------
# (mula, tamat, spec)
CARDS = [
 (0.15, 4.35, dict(kind="hook")),
 (6.90, 16.90, dict(kicker="TAHUKAH ANDA?", big="8/10", count=(7.9, 9.4, 8, "{}/10"),
      cap="rakyat Malaysia tak sedar atau tak pasti tentang penyakit retina",
      src="Sumber: Tinjauan Kolej Oftalmologi")),
 (16.90, 21.95, dict(kicker="RAMAI TERLEWAT", big="Berminggu – berbulan", bigsize=78,
      cap="tempoh ramai orang menunggu sebelum memeriksa mata")),
 (22.10, 29.70, dict(kicker="BANCIAN MATA KEBANGSAAN 2014", big="63,000", count=(24.9, 26.5, 63000, "{:,}"),
      cap="rakyat Malaysia berumur 50 tahun ke atas buta",
      src="Sumber: Bancian Mata Kebangsaan 2014")),
 (29.70, 35.25, dict(kicker="DAN HAMPIR SEMUANYA…", big="60%", count=(29.85, 30.9, 60, "{}%"),
      cap="daripadanya boleh dirawat. Tapi tak sempat.",
      src="Sumber: Bancian Mata Kebangsaan 2014")),
 (35.25, 40.95, dict(kicker="KENCING MANIS", big="~10%", count=(36.4, 37.6, 10, "~{}%"),
      cap="kes kebutaan di Malaysia berpunca daripada penyakit mata diabetik",
      src="Sumber: Bancian Mata Kebangsaan 2014")),
 (41.05, 44.45, dict(kicker="JANGAN TERPEDAYA", big="“Saya masih nampak.”", bigsize=70,
      cap="Alasan yang salah. Kebanyakan masalah mata senyap pada peringkat awal.")),
 (44.45, 48.95, dict(kicker="TINDAKAN", big="Periksa mata sekarang", bigsize=72,
      cap="Jangan tunggu sampai terlambat.")),
 (48.95, dur + 1, dict(kind="product")),
]
CARDS[6][2]["cap"] = "Alasan yang salah."   # kekal ringkas, tak tambah dakwaan di luar skrip

# ---------- subtitle (teks ikut skrip, masa ikut audio) ----------
SUBS = [
 (0.00, 2.35, "Korang tunggu mata sakit baru nak jumpa doktor?"),
 (2.56, 4.20, "Itu silap besar."),
 (4.58, 6.85, "Menurut Tinjauan Kolej Oftalmologi,"),
 (7.00, 10.55, "dapati lebih 8 daripada 10"),
 (10.60, 12.45, "rakyat Malaysia tak sedar"),
 (12.50, 14.95, "atau tak pasti tentang penyakit retina"),
 (15.05, 16.62, "yang boleh buat hilang penglihatan"),
 (16.64, 18.75, "dan ramai tunggu berminggu,"),
 (18.76, 20.36, "malah berbulan-bulan"),
 (20.38, 21.85, "sebelum pemeriksaan mata."),
 (22.18, 24.80, "Bancian Mata Kebangsaan 2014,"),
 (25.12, 26.78, "63 ribu rakyat Malaysia"),
 (26.80, 29.60, "berumur 50 tahun ke atas buta."),
 (29.80, 32.70, "60 peratus daripadanya boleh dirawat."),
 (32.88, 35.10, "Boleh dirawat, tapi tak sempat."),
 (35.26, 37.62, "Kencing manis pun satu punca utama kebutaan,"),
 (37.66, 40.80, "daripada kira-kira 10 peratus kes."),
 (41.10, 42.80, "Ramai kata, “saya masih nampak.”"),
 (42.84, 44.35, "Alasan itu salah."),
 (44.52, 46.10, "Jangan tunggu sampai terlambat."),
 (46.36, 48.85, "Lakukan pemeriksaan mata sekarang."),
 (49.00, 50.12, "Untuk sokongan harian,"),
 (50.30, 52.15, "kita ada DS Pharma Eye Care,"),
 (52.24, 53.70, "berdaftar dengan MAL22076147T,"),
 (53.72, 55.60, "digunakan secara tradisional"),
 (55.62, 57.34, "untuk kesihatan mata."),
 (57.36, 59.52, "Bukan rawatan penyakit mata"),
 (59.54, dur, "dan bukan ganti pemeriksaan."),
]
HILITE = ["DS Pharma Eye Care","MAL22076147T","63 ribu","60 peratus","10 peratus","8 daripada 10","sekarang","terlambat"]

def ts(t):
    h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"
def ass_text(t):
    for k in HILITE:
        t = t.replace(k, "{\\c&HC5D14F&}"+k+"{\\c&HFFFFFF&}")
    # pecah 2 baris jika panjang
    return t
ass = ["[Script Info]","ScriptType: v4.00+",f"PlayResX: {W}",f"PlayResY: {H}","WrapStyle: 0","",
 "[V4+ Styles]","Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
 "Style: Sub,Inter,66,&H00FFFFFF,&H00FFFFFF,&H00201008,&H80000000,1,0,0,0,100,100,0,0,1,5,2,2,70,70,560,1","",
 "[Events]","Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
for a,b,t in SUBS:
    ass.append(f"Dialogue: 0,{ts(a)},{ts(b)},Sub,,0,0,0,,{ass_text(t)}")
os.makedirs("work", exist_ok=True)
open("work/eyecare.ass","w").write("\n".join(ass))

# ---------- render kad ----------
SS = 2
CW = 980
def wrap(draw, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur+" "+w).strip()
        if draw.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def rrect(img, box, r, fill, outline=None, width=0):
    d = ImageDraw.Draw(img); d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)

def render_card(spec, bigtext=None):
    pad = 44*SS; inner = (CW-0)*SS - 2*pad - 16*SS
    tmp = Image.new("RGBA",(10,10)); d0 = ImageDraw.Draw(tmp)
    kf, bf = font("ExtraBold", 28*SS), font("Black", spec.get("bigsize",124)*SS)
    cf, sf = font("SemiBold", 44*SS), font("Medium", 28*SS)
    big = bigtext if bigtext is not None else spec["big"]
    caplines = wrap(d0, spec["cap"], cf, inner)
    bh = bf.getbbox("Ag8")[3]
    h = pad + 34*SS + 14*SS + bh + 10*SS + len(caplines)*56*SS + (46*SS if spec.get("src") else 0) + pad - 16*SS
    img = Image.new("RGBA",(CW*SS,h),(0,0,0,0))
    rrect(img,(0,0,CW*SS-1,h-1),40*SS,(22,14,56,225),(255,255,255,40),2*SS)
    rrect(img,(0,36*SS,12*SS,h-36*SS),6*SS,TEAL+(255,))
    d = ImageDraw.Draw(img); x = pad+16*SS; y = pad - 8*SS
    d.text((x,y),spec["kicker"],font=kf,fill=TEAL+(255,)); y += 34*SS+14*SS
    d.text((x,y-bf.getbbox("A")[1]*0 ),big,font=bf,fill=WHITE+(255,)); y += bh+10*SS
    for l in caplines:
        d.text((x,y),l,font=cf,fill=WHITE+(235,)); y += 56*SS
    if spec.get("src"):
        d.text((x,y+4*SS),spec["src"],font=sf,fill=GREY+(220,))
    return img.resize((CW,h//SS),Image.LANCZOS)

def render_hook():
    img = Image.new("RGBA",(W,330),(0,0,0,0)); d = ImageDraw.Draw(img)
    f1, f2 = font("Black",62), font("Black",62)
    for txt,col,y in (("TUNGGU MATA SAKIT",WHITE,20),("BARU NAK JUMPA DOKTOR?",TEAL,112)):
        w = d.textlength(txt,font=f1); x=(W-w)/2
        d.text((x+3,y+5),txt,font=f1,fill=(0,0,0,150))
        d.text((x,y),txt,font=f1,fill=col+(255,))
    return img

_box = Image.open("assets/logo/eyecare_box.png").convert("RGBA")
def render_product():
    CH = 412; img = Image.new("RGBA",(CW*SS,CH*SS),(0,0,0,0))
    rrect(img,(0,0,CW*SS-1,CH*SS-1),40*SS,(22,14,56,230),(255,255,255,40),2*SS)
    rrect(img,(0,36*SS,12*SS,(CH-36)*SS),6*SS,TEAL+(255,))
    bw = 400*SS; bh = int(bw*_box.height/_box.width)
    bx = _box.resize((bw,bh),Image.LANCZOS)
    m = Image.new("L",bx.size,0); ImageDraw.Draw(m).rounded_rectangle((0,0,bw-1,bh-1),18*SS,fill=255)
    img.paste(bx,(40*SS,48*SS),m)
    d = ImageDraw.Draw(img); x = 40*SS+bw+36*SS
    d.text((x,44*SS),"DS PHARMA",font=font("ExtraBold",28*SS),fill=TEAL+(255,))
    d.text((x,84*SS),"Eye Care",font=font("Black",74*SS),fill=WHITE+(255,))
    d.text((x,176*SS),"Tablet kunyah 650mg",font=font("SemiBold",34*SS),fill=WHITE+(235,))
    d.text((x,222*SS),"MAL22076147T",font=font("Bold",32*SS),fill=TEAL+(255,))
    d.text((40*SS,48*SS+bh+26*SS),"Digunakan secara tradisional untuk kesihatan mata.",font=font("SemiBold",30*SS),fill=WHITE+(240,))
    d.text((40*SS,48*SS+bh+68*SS),"Bukan rawatan penyakit mata dan bukan ganti pemeriksaan.",font=font("SemiBold",29*SS),fill=(225,230,245,255))
    return img.resize((CW,CH),Image.LANCZOS)

def ease(x): x=min(max(x,0),1); return 1-(1-x)**3

_cache = {}
def card_img(i, spec, t):
    key = (i,)
    if spec.get("kind")=="hook":
        if key not in _cache: _cache[key]=render_hook()
        return _cache[key]
    if spec.get("kind")=="product":
        if key not in _cache: _cache[key]=render_product()
        return _cache[key]
    if "count" in spec:
        a,b,target,fmt = spec["count"]; v = round(target*ease((t-a)/(b-a))); key=(i,v)
        if key not in _cache: _cache[key]=render_card(spec, fmt.format(v))
        return _cache[key]
    if key not in _cache: _cache[key]=render_card(spec)
    return _cache[key]

def frame(t):
    band = Image.new("RGBA",(W,BAND_H),(0,0,0,0))
    for i,(a,b,spec) in enumerate(CARDS):
        if not (a-0.01 <= t <= b+0.3): continue
        fin = ease((t-a)/0.35); fout = 1-ease((t-b)/0.25) if t>b else 1
        al = fin*fout
        if al <= 0.004: continue
        im = card_img(i,spec,t)
        dy = int((1-fin)*34 - (1-fout)*12)
        if spec.get("kind")=="hook": pos = (0, 10+dy)
        else: pos = ((W-im.width)//2, 20+dy)
        if al < 0.999:
            im = im.copy(); arr = np.array(im); arr[...,3] = (arr[...,3]*al).astype(np.uint8); im = Image.fromarray(arr)
        band.alpha_composite(im, pos) if pos[1]>=0 else band.alpha_composite(im.crop((0,-pos[1],im.width,im.height)),(pos[0],0))
    return band.tobytes()

# gradien bawah supaya subtitle jelas
g = np.zeros((H,W,4),np.uint8); y0=1050
for y in range(y0,H): g[y,:,3] = int(150*((y-y0)/(H-y0))**1.5)
Image.fromarray(g).save("work/grad.png")


# ---------- zoom in/out licin pada video utama (kekunci: masa, skala) ----------
ZK = [(0,1.00),(4.2,1.08),(8.0,1.00),(13.0,1.07),(17.0,1.01),(21.8,1.08),(26.0,1.00),(30.0,1.08),
      (35.2,1.01),(40.8,1.07),(44.4,1.00),(48.9,1.09),(53.0,1.02),(57.4,1.09),(dur,1.05)]
def zexpr():
    e = f"{ZK[-1][1]}"
    for (a,za),(b,zb) in reversed(list(zip(ZK,ZK[1:]))):
        e = f"if(lt(T,{b}),{za}+({zb}-{za})*(0.5-0.5*cos(PI*(T-{a})/({b}-{a}))),{e})"
    return e.replace("T","(on/30)")
ZOOM = ("scale=2160:3840:flags=bicubic,zoompan=z='%s':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30," % zexpr())
vf = ("[0:v]"+ZOOM+"eq=contrast=1.05:saturation=1.08:gamma=0.98,unsharp=5:5:0.4[b];"
      "[b][1:v]overlay=0:0[c];[c][2:v]overlay=0:%d:eof_action=pass[d];"
      "[d]subtitles=work/eyecare.ass:fontsdir=/usr/share/fonts/opentype/inter,fade=t=out:st=%.2f:d=0.35[v]" % (BAND_Y, dur-0.35))
af = f"[0:a]highpass=f=80,acompressor=threshold=-21dB:ratio=3:attack=5:release=90,loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st={dur-0.3:.2f}:d=0.3[a]"
cmd = ["ffmpeg","-y","-v","error","-i",SRC,"-loop","1","-framerate",str(FPS),"-i","work/grad.png",
       "-f","rawvideo","-pix_fmt","rgba","-s",f"{W}x{BAND_H}","-r",str(FPS),"-i","-",
       "-filter_complex",vf+";"+af,"-map","[v]","-map","[a]","-t",f"{dur:.3f}",
       "-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",OUT]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
n = int(dur*FPS)+2
for k in range(n):
    p.stdin.write(frame(k/FPS))
p.stdin.close(); p.wait()
print("siap", OUT, p.returncode)
