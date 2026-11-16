#!/usr/bin/env python3
"""Edit video kesihatan mata (tema klinik optometris).
Guna: python3 scripts/build_optometri.py input/video.mov
Hasil: work/video.srt, work/video.ass, output/video_optometri.mp4
"""
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont

SRC = sys.argv[1] if len(sys.argv) > 1 else "input/video.mov"
OUT = "output/video_optometri.mp4"
W, H = 1080, 1920
os.makedirs("work/ov", exist_ok=True); os.makedirs("output", exist_ok=True)

# ---- palet klinik optometris ----
NAVY = (10, 47, 68); TEAL = (14, 138, 156); AQUA = (18, 181, 176)
MINT = (230, 247, 249); WHITE = (255, 255, 255); RED = (214, 69, 80)
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FX = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
f = lambda p, s: ImageFont.truetype(p, s)

# ---- bahagian yang dikekalkan (saat dalam video asal) ----
KEEP = [(1.95, 4.95), (5.30, 14.14), (14.76, 16.48), (17.01, 22.61),
        (23.12, 27.22), (30.39, 32.08), (32.47, 34.08), (34.63, 37.30)]
starts, t = [], 0.0
for a, b in KEEP:
    starts.append(t); t += b - a
TOTAL = t

def omap(s):  # masa asal -> masa output
    for (a, b), o in zip(KEEP, starts):
        if a - 1e-6 <= s <= b + 1e-6:
            return o + (s - a)
    raise ValueError(s)

# ---- subtitle (teks ikut audio + skrip, ejaan dibetulkan) ----
SUBS = [
 ("Mak ayah, ni fakta yang buat saya terdiam.", 1.95, 4.95),
 ("Pakar cakap budak rabun jauh", 5.30, 7.28),
 ("naik daripada {\\c&HB0B512&}7%{\\c&HFFFFFF&} masa Darjah 1,", 7.28, 11.0),
 ("jadi {\\c&HB0B512&}30%{\\c&HFFFFFF&} bila masuk sekolah menengah.", 11.24, 14.14),
 ("Salah satu punca besar:", 14.76, 16.48),
 ("Skrin melampau, kurang main di luar.", 17.01, 19.84),
 ("Maksudnya, dalam 6 tahun ni je,", 20.05, 22.61),
 ("bilangan budak rabun boleh naik", 23.12, 25.2),
 ("sehingga {\\c&HB0B512&}4 kali ganda.{\\c&HFFFFFF&}", 25.2, 27.22),
 ("Tiga benda yang Mak ayah boleh buat:", 30.39, 32.08),
 ("Bagi anak rehat daripada skrin,", 32.47, 34.08),
 ("Bawa main di luar,", 34.63, 35.8),
 ("cek mata setahun sekali.", 35.88, 37.30),
]
def ts(x, ass=False):
    h, m, s = int(x // 3600), int(x % 3600 // 60), x % 60
    return f"{h}:{m:02d}:{s:05.2f}" if ass else f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s%1)*1000)):03d}"
import re
srt, ass = [], []
for i, (txt, a, b) in enumerate(SUBS, 1):
    oa, ob = omap(a), omap(b)
    plain = re.sub(r"\{[^}]*\}", "", txt)
    srt.append(f"{i}\n{ts(oa)} --> {ts(ob)}\n{plain}\n")
    ass.append(f"Dialogue: 0,{ts(oa,True)},{ts(ob,True)},Sub,,0,0,0,,{txt}")
open("work/video.srt", "w").write("\n".join(srt))
open("work/video.ass", "w").write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,Inter,58,&H00FFFFFF,&H00FFFFFF,&H00442F0A,&H00000000,1,0,0,0,100,100,0,0,3,16,0,2,60,60,400,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
""" + "\n".join(ass) + "\n")

# ---- overlay PNG ----
def rr(d, box, r, fill, outline=None, w=0):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=w)

def eye(d, cx, cy, s, col):
    d.ellipse((cx - s, cy - s * .55, cx + s, cy + s * .55), outline=col, width=max(3, s // 7))
    d.ellipse((cx - s * .32, cy - s * .32, cx + s * .32, cy + s * .32), fill=col)

def cross(d, cx, cy, s, col):
    d.rectangle((cx - s, cy - s // 3, cx + s, cy + s // 3), fill=col)
    d.rectangle((cx - s // 3, cy - s, cx + s // 3, cy + s), fill=col)

def center(d, xy, txt, font, fill):
    d.text(xy, txt, font=font, fill=fill, anchor="mm")

def new():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)

# header sentiasa ada
im, d = new()
rr(d, (0, 0, W, 150), 0, NAVY + (235,))
d.rectangle((0, 150, W, 158), fill=AQUA)
rr(d, (40, 30, 130, 120), 45, WHITE); eye(d, 85, 75, 32, TEAL)
d.text((155, 55), "KESIHATAN MATA ANAK", font=f(FX, 42), fill=WHITE, anchor="lm")
d.text((155, 100), "Panduan klinik optometri untuk ibu bapa", font=f(FM, 26), fill=(170, 225, 232), anchor="lm")
cross(d, 985, 75, 26, AQUA)
im.save("work/ov/header.png")

# kad statistik 7% -> 30%
def stat(stage):
    im, d = new()
    y0 = 690
    rr(d, (50, y0, 1030, y0 + 530), 36, WHITE + (245,), TEAL, 6)
    d.text((90, y0 + 50), "RABUN JAUH DALAM KALANGAN KANAK-KANAK", font=f(FX, 30), fill=TEAL, anchor="lm")
    # baris Darjah 1
    d.text((90, y0 + 135), "Darjah 1", font=f(FB, 38), fill=NAVY, anchor="lm")
    rr(d, (90, y0 + 165, 90 + int(840 * .07 / .30 * 1), y0 + 225), 18, AQUA)
    d.text((90 + int(840 * .07 / .30) + 20, y0 + 195), "~7%", font=f(FX, 54), fill=AQUA, anchor="lm")
    if stage >= 2:
        d.text((90, y0 + 305), "Sekolah menengah (Form 1)", font=f(FB, 38), fill=NAVY, anchor="lm")
        rr(d, (90, y0 + 335, 90 + 650, y0 + 405), 18, RED)
        d.text((90 + 650 + 20, y0 + 370), "30%", font=f(FX, 64), fill=RED, anchor="lm")
        d.text((540, y0 + 470), "▲ naik hampir 4 kali ganda", font=f(FB, 32), fill=NAVY, anchor="mm") if False else None
        center(d, (540, y0 + 475), "Rabun jauh makin meningkat", f(FB, 30), TEAL)
    im.save(f"work/ov/stat{stage}.png")
stat(1); stat(2)

# punca
im, d = new()
rr(d, (50, 900, 1030, 1160), 36, NAVY + (240,), AQUA, 5)
d.text((90, 950), "PUNCA UTAMA", font=f(FX, 30), fill=AQUA, anchor="lm")
d.text((90, 1030), "Skrin melampau", font=f(FX, 60), fill=WHITE, anchor="lm")
d.text((90, 1105), "+ kurang main di luar", font=f(FB, 46), fill=(170, 225, 232), anchor="lm")
eye(d, 900, 1030, 70, AQUA)
d.line((820, 975, 980, 1085), fill=RED, width=10)
im.save("work/ov/punca.png")

# 6 tahun
im, d = new()
rr(d, (300, 900, 780, 1060), 36, WHITE + (245,), TEAL, 6)
center(d, (540, 955), "DALAM", f(FB, 28), TEAL)
center(d, (540, 1015), "6 TAHUN SAHAJA", f(FX, 50), NAVY)
im.save("work/ov/tahun.png")

# 4x
im, d = new()
rr(d, (180, 880, 900, 1180), 40, RED + (245,), WHITE, 6)
center(d, (540, 1000), "4×", f(FX, 150), WHITE)
center(d, (540, 1120), "BILANGAN BUDAK RABUN", f(FB, 36), WHITE)
im.save("work/ov/x4.png")

# 3 tips
TIPS = [("1", "Rehat dari skrin"), ("2", "Bawa main di luar"), ("3", "Check mata setahun sekali")]
def tips(n):
    im, d = new()
    rr(d, (50, 790, 1030, 1000 - 0 + 330), 36, WHITE + (0,))
    rr(d, (50, 790, 1030, 880), 30, TEAL + (245,))
    center(d, (540, 835), "3 PERKARA IBU BAPA BOLEH BUAT", f(FX, 38), WHITE)
    for i in range(n):
        y = 900 + i * 135
        rr(d, (50, y, 1030, y + 115), 28, WHITE + (245,), AQUA, 5)
        rr(d, (75, y + 20, 150, y + 95), 37, TEAL)
        center(d, (112, y + 58), TIPS[i][0], f(FX, 44), WHITE)
        d.text((180, y + 58), TIPS[i][1], font=f(FX, 50 if i < 2 else 44), fill=NAVY, anchor="lm")
        d.text((985, y + 58), "✓", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54), fill=AQUA, anchor="mm")
    im.save(f"work/ov/tips{n}.png")
for n in (1, 2, 3): tips(n)

# ---- jadual overlay (masa output) ----
o = omap
OVS = [
 ("header", 0, TOTAL),
 ("stat1", o(8.0), o(10.86)),
 ("stat2", o(10.86), o(14.14)),
 ("punca", o(14.9), o(19.84)),
 ("tahun", o(21.14), o(25.2)),
 ("x4", o(25.2), o(27.22)),
 ("tips1", o(30.39), o(34.08)),
 ("tips2", o(34.63), o(35.88)),
 ("tips3", o(35.88), TOTAL),
]
# tips1 hingga akhir segmen, tips2 dari "main di luar"
OVS[6] = ("tips1", o(30.39), o(34.63))
OVS[7] = ("tips2", o(34.63), o(35.88))

# ---- ffmpeg ----
fc, vparts, aparts = [], "", ""
for i, ((a, b), ) in enumerate(zip(KEEP)):
    zoom = 1.07 if i % 2 else 1.0
    zf = f",scale={int(W*zoom)}:{int(H*zoom)},crop={W}:{H}" if zoom != 1 else ""
    fc.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS{zf}[v{i}]")
    fc.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={b-a-0.03:.3f}:d=0.03[a{i}]")
    vparts += f"[v{i}]"; aparts += f"[a{i}]"
n = len(KEEP)
fc.append(f"{vparts}concat=n={n}:v=1:a=0[vc]")
fc.append(f"{aparts}concat=n={n}:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
inputs = ["-i", SRC]
cur = "vc"
for k, (name, a, b) in enumerate(OVS):
    inputs += ["-loop", "1", "-i", f"work/ov/{name}.png"]
    nxt = f"o{k}"
    fc.append(f"[{k+1}:v]format=rgba,fade=t=in:st={a:.2f}:d=0.2:alpha=1[p{k}]")
    fc.append(f"[{cur}][p{k}]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})':shortest=1[{nxt}]")
    cur = nxt
fc.append(f"[{cur}]subtitles=work/video.ass:fontsdir=/usr/share/fonts/opentype/inter,fade=t=out:st={TOTAL-0.3:.2f}:d=0.3[vout]")
cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
       "-t", f"{TOTAL:.2f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT]
subprocess.run(cmd, check=True)
print(OUT, f"{TOTAL:.2f}s")
