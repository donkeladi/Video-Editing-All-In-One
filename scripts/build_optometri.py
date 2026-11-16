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
KEEP = [(a - 0.08, b + 0.14) for a, b in KEEP]
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
    oa, ob = omap(a), omap(b) + 0.12
    if i < len(SUBS):
        na = omap(SUBS[i][1])
        if 0 < na - ob < 0.6: ob = na
    ob = min(ob, TOTAL)
    plain = re.sub(r"\{[^}]*\}", "", txt)
    srt.append(f"{i}\n{ts(oa)} --> {ts(ob)}\n{plain}\n")
    ass.append(f"Dialogue: 0,{ts(oa,True)},{ts(ob,True)},Sub,,0,0,0,,{{\\fad(140,120)}}{txt}")
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

# ---- overlay beranimasi (dilukis frame demi frame, dihantar ke ffmpeg) ----
import math
FPS = 30
def rr(d, box, r, fill, outline=None, w=0):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=w)
def eye(d, cx, cy, s, col):
    d.ellipse((cx - s, cy - s * .55, cx + s, cy + s * .55), outline=col, width=max(3, int(s // 7)))
    d.ellipse((cx - s * .32, cy - s * .32, cx + s * .32, cy + s * .32), fill=col)
def ctr(d, xy, txt, font, fill): d.text(xy, txt, font=font, fill=fill, anchor="mm")
def clamp(x): return max(0.0, min(1.0, x))
def prog(t, a, d): return clamp((t - a) / d)
def out3(x): return 1 - (1 - x) ** 3
def back(x, k=1.5):
    x = clamp(x) - 1; return 1 + (k + 1) * x ** 3 + k * x ** 2
_fc = {}
def F(p, sz):
    if (p, sz) not in _fc: _fc[(p, sz)] = ImageFont.truetype(p, sz)
    return _fc[(p, sz)]
DJ = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def card_stat(d, t, t0, t1, t2):
    """t0 muncul, t1 mula bar 7%, t2 mula bar 30%"""
    y0 = 720
    rr(d, (50, y0, 1030, y0 + 520), 36, WHITE + (255,), TEAL, 6)
    d.text((90, y0 + 50), "RABUN JAUH DALAM KALANGAN KANAK-KANAK", font=F(FX, 30), fill=TEAL, anchor="lm")
    track = (90, 940)
    # Darjah 1
    d.text((90, y0 + 130), "Darjah 1", font=F(FB, 38), fill=NAVY, anchor="lm")
    rr(d, (90, y0 + 165, 930, y0 + 225), 18, MINT)
    p1 = out3(prog(t, t1, 0.9))
    if p1 > 0: rr(d, (90, y0 + 165, 90 + max(36, 840 * 0.07 / 0.30 * p1), y0 + 225), 18, AQUA)
    d.text((90 + 840 * 0.07 / 0.30 + 24, y0 + 195), f"{7 * p1:.0f}%", font=F(FX, 56), fill=AQUA, anchor="lm")
    # Form 1
    d.text((90, y0 + 305), "Sekolah menengah (Form 1)", font=F(FB, 38), fill=NAVY, anchor="lm")
    rr(d, (90, y0 + 340, 930, y0 + 410), 18, MINT)
    p2 = out3(prog(t, t2, 1.2))
    if p2 > 0: rr(d, (90, y0 + 340, 90 + max(36, 840 * p2), y0 + 410), 18, RED)
    if p2 > 0.02:
        x = 90 + 840 * p2
        d.text((min(x - 20, 920), y0 + 375), f"{30 * p2:.0f}%", font=F(FX, 56), fill=WHITE, anchor="rm")
    if t > t2 + 1.2:
        k = back(prog(t, t2 + 1.2, 0.45))
        ctr(d, (540, y0 + 468), "Rabun jauh makin meningkat", F(FB, int(30 * max(k, .01))), TEAL)

def card_punca(d, t, t0):
    rr(d, (50, 800, 1030, 1060), 36, NAVY + (255,), AQUA, 5)
    d.text((90, 850), "PUNCA UTAMA", font=F(FX, 30), fill=AQUA, anchor="lm")
    d.text((90, 925), "Skrin melampau", font=F(FX, 60), fill=WHITE, anchor="lm")
    d.text((90, 1000), "+ kurang main di luar", font=F(FB, 46), fill=(170, 225, 232), anchor="lm")
    eye(d, 900, 925, 70, AQUA)
    p = out3(prog(t, t0 + 0.5, 0.5))
    d.line((830, 880, 830 + 140 * p, 880 + 90 * p), fill=RED, width=10)

def card_tahun(d, t, t0):
    rr(d, (290, 820, 790, 990), 36, WHITE + (255,), TEAL, 6)
    ctr(d, (540, 875), "DALAM", F(FB, 28), TEAL)
    ctr(d, (540, 935), "6 TAHUN SAHAJA", F(FX, 50), NAVY)

def card_x4(d, t, t0):
    rr(d, (170, 760, 910, 1060), 40, RED + (255,), WHITE, 6)
    v = 1 + 3 * out3(prog(t, t0 + 0.1, 0.8))
    ctr(d, (540, 890), f"{v:.0f}×", F(FX, 150), WHITE)
    ctr(d, (540, 1005), "BILANGAN BUDAK RABUN", F(FB, 36), WHITE)

TIPS = ["Rehat dari skrin", "Bawa main di luar", "Check mata setahun sekali"]
def card_tips(d, t, t0, ts_):
    rr(d, (50, 720, 1030, 810), 30, TEAL + (255,))
    ctr(d, (540, 765), "3 PERKARA IBU BAPA BOLEH BUAT", F(FX, 38), WHITE)
    for i in range(3):
        y = 830 + i * 130
        p = out3(prog(t, ts_[i], 0.5))
        if p <= 0: continue
        dx = (1 - p) * -300
        rr(d, (50 + dx, y, 1030 + dx, y + 112), 28, WHITE + (int(255 * min(1, p * 2)),), AQUA, 5)
        rr(d, (75 + dx, y + 18, 150 + dx, y + 93), 37, TEAL)
        ctr(d, (112 + dx, y + 56), str(i + 1), F(FX, 44), WHITE)
        d.text((180 + dx, y + 56), TIPS[i], font=F(FX, 50 if i < 2 else 44), fill=NAVY, anchor="lm")
        c = clamp((t - ts_[i] - 0.3) / 0.35)
        if c > 0:
            pts = [(930, y + 56), (950, y + 76), (985, y + 36)]
            seg = [pts[0], pts[1]] if c < .5 else pts
            if c < .5:
                m = c / .5; seg = [pts[0], (pts[0][0] + (pts[1][0] - pts[0][0]) * m, pts[0][1] + (pts[1][1] - pts[0][1]) * m)]
            else:
                m = (c - .5) / .5; seg = [pts[0], pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * m, pts[1][1] + (pts[2][1] - pts[1][1]) * m)]
            d.line([(x + dx, y_) for x, y_ in seg], fill=AQUA, width=11, joint="curve")

o = omap
# (nama, mula, tamat, fungsi) -- satu kad pada satu masa, tiada bertindih
CARDS = [
 (o(7.5), o(14.14) + 0.1, lambda d, t, a: card_stat(d, t, a, o(8.0), o(10.86))),
 (o(14.9), o(19.84) + 0.1, lambda d, t, a: card_punca(d, t, a)),
 (o(21.14), o(25.2) - 0.05, lambda d, t, a: card_tahun(d, t, a)),
 (o(25.2), o(27.22) + 0.2, lambda d, t, a: card_x4(d, t, a)),
 (o(30.39), TOTAL, lambda d, t, a: card_tips(d, t, a, [o(32.47), o(34.63), o(35.88)])),
]
IN, OUTD = 0.5, 0.35

def frames():
    n = int(math.ceil(TOTAL * FPS))
    for i in range(n):
        t = i / FPS
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for a, b, fn in CARDS:
            if a <= t <= b:
                layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
                fn(d, t, a)
                pin = prog(t, a, IN); pout = prog(t, b - OUTD, OUTD) if b < TOTAL else 0
                al = out3(pin) * (1 - pout)
                dy = 80 + int(70 * (1 - back(pin, 0.9))) + int(30 * pout ** 2)
                layer.putalpha(layer.getchannel("A").point(lambda v, al=al: int(v * al)))
                canvas.alpha_composite(layer, (0, 0)) if dy == 0 else canvas.alpha_composite(layer.crop((0, 0, W, H - dy)) if dy > 0 else layer, (0, dy) if dy > 0 else (0, 0))
        yield canvas.tobytes()

# ---- ffmpeg ----
fc, vparts, aparts = [], "", ""
for i, (a, b) in enumerate(KEEP):
    fc.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]")
    fc.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={b-a-0.03:.3f}:d=0.03[a{i}]")
    vparts += f"[v{i}]"; aparts += f"[a{i}]"
n = len(KEEP)
fc.append(f"{vparts}concat=n={n}:v=1:a=0[vc]")
fc.append(f"{aparts}concat=n={n}:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
fc.append("[vc][1:v]overlay=0:0:format=auto:shortest=1[vo]")
fc.append(f"[vo]subtitles=work/video.ass:fontsdir=/usr/share/fonts/opentype/inter,fade=t=out:st={TOTAL-0.3:.2f}:d=0.3[vout]")
cmd = ["ffmpeg", "-y", "-v", "error", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
       "-t", f"{TOTAL:.2f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT]
pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for fr in frames():
    pr.stdin.write(fr)
pr.stdin.close(); pr.wait()
print(OUT, f"{TOTAL:.2f}s", "rc", pr.returncode)
