#!/usr/bin/env python3
"""Edit korporat optometri: subtitle (ASS) + overlay sumber (PNG) + ffmpeg render.
Guna: build_optometry.py input.mov output.mp4 [--preview]"""
import re, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 1080, 1920
NAVY, TEAL, WHITE = (11, 37, 69), (25, 181, 196), (255, 255, 255)
F = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
T0, T1 = 0.70, 59.40           # trim senyap awal/akhir
WORK = os.path.join(os.path.dirname(os.path.abspath(OUT)), "..", "work")
OV = os.path.join(WORK, "ov"); os.makedirs(OV, exist_ok=True)

CHUNKS = [
 "Korang ingat rabun tua ni", "masalah orang 40 tahun ke atas je?",
 "Pakar oftalmologi KPJ, Dr Helen Tan,", "cakap dalam Berita Harian,",
 "sekarang 10 hingga 12 peratus orang umur 30-an", "dah boleh kena presbiopia pramatang.",
 "Selalunya mula umur 36.", "Salah satu faktornya, kerap guna gajet.",
 "Mayo Clinic pulak cakap,", "tanda awal dia ialah kena pegang bacaan",
 "jauh-jauh baru nampak jelas.", "Kalau dah perasan tanda ni,", "pergi check mata.",
 "Untuk penjagaan harian,", "saya amalkan DS Pharma Eye Care.",
 "Tablet kunyah yang digunakan secara tradisional", "untuk kesihatan mata.",
]
# 1) selang pertuturan dari silencedetect
log = subprocess.run(["ffmpeg","-hide_banner","-i",SRC,"-vn","-af","silencedetect=noise=-32dB:d=0.28","-f","null","-"],
                     capture_output=True,text=True).stderr
st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
dur = T1
segs, cur = [], 0.0
for s, e in zip(st, en):
    if s - cur > 0.15: segs.append((cur, s))
    cur = e
if dur - cur > 0.15: segs.append((cur, dur))
segs = [(max(a,T0), min(b,T1)) for a,b in segs if b > T0]
total = sum(b-a for a,b in segs)
# 2) agih chunk ikut bilangan aksara pada garis masa pertuturan
chars = [len(c) for c in CHUNKS]; tot_c = sum(chars)
def at(speech_t):
    for a,b in segs:
        d=b-a
        if speech_t <= d: return a+speech_t
        speech_t -= d
    return segs[-1][1]
cues, acc = [], 0
for c, n in zip(CHUNKS, chars):
    s = at(total*acc/tot_c); acc += n; e = at(total*acc/tot_c)
    cues.append((s, e, c))
for c in cues: print("%6.2f-%6.2f %s" % ((c[0]-T0), (c[1]-T0), c[2]))
cue_pr = next(c for c in cues if c[2].startswith("saya amalkan"))[0]
ts = lambda t: "%d:%02d:%05.2f" % (int(t//3600), int(t%3600//60), t%60)
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,Inter,50,&H00FFFFFF,&H00FFFFFF,&H0045250B,&H00452500,1,0,0,0,100,100,0,0,3,16,0,2,70,70,300,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
for s,e,c in cues:
    mv = 370 if s >= cue_pr - 0.3 else 0
    ass += f"Dialogue: 0,{ts(s)},{ts(e)},Sub,,0,0,{mv},,{{\\fad(120,100)}}{c}\n"
open(os.path.join(WORK,"main.ass"),"w").write(ass)

# 3) overlay PNG
def rr(d, box, r, fill): d.rounded_rectangle(box, r, fill=fill)
def chip(name, label, title, sub):
    f1, f2, f3 = (ImageFont.truetype(F%"Bold",22), ImageFont.truetype(F%"Bold",34), ImageFont.truetype(F%"Medium",25))
    w = max(f2.getlength(title), f3.getlength(sub)) + 150
    im = Image.new("RGBA", (int(w)+20, 150), (0,0,0,0)); d = ImageDraw.Draw(im)
    rr(d,(0,0,w,130),18,NAVY+(232,)); rr(d,(0,0,12,130),6,TEAL+(255,))
    d.text((40,20),label,font=f1,fill=TEAL+(255,)); d.text((40,50),title,font=f2,fill=WHITE+(255,))
    d.text((40,92),sub,font=f3,fill=(190,208,230,255)); im.save(os.path.join(OV,name+".png"))
chip("bh","SUMBER","Berita Harian","Pakar Oftalmologi KPJ · Mac 2024")
chip("mayo","SUMBER","Mayo Clinic","Presbyopia: Symptoms & causes")
# kad produk (lower third) hujung
im = Image.new("RGBA",(960,170),(0,0,0,0)); d=ImageDraw.Draw(im)
rr(d,(0,0,960,170),22,NAVY+(238,)); rr(d,(0,0,14,170),7,TEAL+(255,))
d.text((44,22),"DS PHARMA",font=ImageFont.truetype(F%"Bold",24),fill=TEAL+(255,))
d.text((44,54),"Eye Care Chewable Tablet 650mg",font=ImageFont.truetype(F%"Bold",40),fill=WHITE+(255,))
d.text((44,108),"Digunakan secara tradisional untuk kesihatan mata · MAL22076147T",font=ImageFont.truetype(F%"Medium",23),fill=(190,208,230,255))
im.save(os.path.join(OV,"prod.png"))
# disclaimer nipis
im = Image.new("RGBA",(960,50),(0,0,0,0)); d=ImageDraw.Draw(im)
rr(d,(0,0,960,50),12,NAVY+(215,))
d.text((18,12),"Ini ubat tradisional. Sila rujuk ahli farmasi / doktor sebelum mengambil produk ini.",font=ImageFont.truetype(F%"Medium",21),fill=(255,255,255,235))
im.save(os.path.join(OV,"warn.png"))

def tm(t): return t-T0
def cue(txt): return next(c for c in cues if c[2].startswith(txt))
bh_s, bh_e = cue("cakap dalam Berita")[0]-0.1, cue("Salah satu")[1]+0.3
my_s, my_e = cue("Mayo Clinic")[0]-0.1, cue("jauh-jauh")[1]+0.6
pr_s, pr_e = cue("saya amalkan")[0]-0.2, T1
def en_(a,b): return f"enable='between(t,{a-T0:.2f},{b-T0:.2f})'"
def fadeimg(i, a, b):  # fade alpha in/out
    return f"[{i}:v]format=rgba,fade=t=in:st={a-T0:.2f}:d=0.3:alpha=1,fade=t=out:st={b-T0-0.3:.2f}:d=0.3:alpha=1[o{i}]"
fg = ";".join([
 f"[0:v]trim={T0}:{T1},setpts=PTS-STARTPTS,eq=contrast=1.04:saturation=1.06,unsharp=5:5:0.4,"
 f"drawbox=x=0:y=0:w='iw*t/{T1-T0:.2f}':h=7:color=0x19B5C4@1:t=fill,"
 f"drawbox=x=0:y=0:w=iw:h=7:color=0x0B2545@0.35:t=fill[v0]",
 fadeimg(1,bh_s,bh_e), fadeimg(2,my_s,my_e), fadeimg(3,pr_s,pr_e), fadeimg(4,pr_s,pr_e),
 f"[v0][o1]overlay=x=48:y=118:{en_(bh_s,bh_e)}[v1]",
 f"[v1][o2]overlay=x=48:y=118:{en_(my_s,my_e)}[v2]",
 f"[v2][o3]overlay=x=60:y=1590:{en_(pr_s,pr_e)}[v3]",
 f"[v3][o4]overlay=x=60:y=1775:{en_(pr_s,pr_e)}[v4]",
 f"[v4]subtitles={os.path.join(WORK,'main.ass')}:fontsdir=/usr/share/fonts/opentype/inter[vout]",
])
# subtitle naik bila kad produk muncul -> pindah subtitle ke atas semasa kad (margin berbeza dikendali di ASS di bawah)
af = f"atrim={T0}:{T1},asetpts=PTS-STARTPTS,highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=11"
cmd = ["ffmpeg","-y","-i",SRC]
for n in ["bh","mayo","prod","warn"]: cmd += ["-loop","1","-i",os.path.join(OV,n+".png")]
cmd += ["-filter_complex",fg,"-af",af,"-map","[vout]","-map","0:a","-shortest",
        "-c:v","libx264","-crf","18" if "--preview" not in sys.argv else "26","-preset","medium","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","192k","-movflags","+faststart",OUT]
subprocess.run(cmd, check=True)
