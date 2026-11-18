#!/usr/bin/env python3
"""Bina video awareness retina: jump-cut, subtitle ASS, overlay grafik, normalize -14 LUFS.
Guna: python3 -I scripts/build_awareness.py   (perlu work/words.json dari faster-whisper)
"""
import json, os, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_, H_ = 1080, 1920
SRC = f"{ROOT}/input/awareness.mov"
WORK = f"{ROOT}/work/ov"
os.makedirs(WORK, exist_ok=True)
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FX = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FR = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
if not os.path.exists(FX): FX = FB

# ---------- 1. segmen yang dikekalkan (masa sumber) ----------
KEEP = [(0.60, 2.80), (2.92, 11.70), (11.88, 20.75), (20.92, 40.75),
        (40.90, 43.45), (44.82, 47.98)]
END_HOLD = 2.0   # end card selepas ayat terakhir

def mp(t):
    """masa sumber -> masa output (None jika dipotong)"""
    acc = 0.0
    for a, b in KEEP:
        if a <= t <= b: return acc + (t - a)
        acc += b - a
    return None
def mp_near(t):
    acc = 0.0
    for a, b in KEEP:
        if t < a: return acc
        if t <= b: return acc + (t - a)
        acc += b - a
    return acc
MAIN_DUR = sum(b - a for a, b in KEEP)
TOTAL = MAIN_DUR + END_HOLD

# ---------- 2. subtitle ----------
FIX = {"keota.": "otak.", "menghebut": "menyebut", "menyebut": "menyebut"}
DROP = {"pun", "ataupun", "sekarang."}
words = []
for seg in json.load(open(f"{ROOT}/work/words.json")):
    for w, s, e in seg["w"]:
        w = w.strip(); w = FIX.get(w, w)
        if w.lower() in DROP: continue
        if w == "-tiba": words[-1][0] += "-tiba"; words[-1][2] = e; continue
        if w == "-labah": words[-1][0] += "-labah"; words[-1][2] = e; continue
        words.append([w, s, e])
# "labah" "-labah" digabung; "Tiba" "-tiba" digabung
words[0][1] = max(words[0][1], 0.78)  # ucapan sebenar bermula ~0.8s

KEY = ("kilat", "bintik", "benang", "labah", "esok", "retina", "tertanggal", "koyak", "kecemasan", "sakit",
       "24", "jam", "hospital", "tirai", "bayang", "segera", "hari", "ini", "otak")
YEL = r"{\c&H0AD6FF&}"; WHT = r"{\c&HFFFFFF&}"

def build_chunks():
    chunks, cur = [], []
    for w in words:
        if mp(w[1] + 0.02) is None and mp(w[2] - 0.02) is None: continue
        cur.append(w)
        txt = " ".join(x[0] for x in cur)
        if w[0][-1] in ".?!," or len(cur) >= 4 or len(txt) >= 19:
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    return chunks

def tc(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def build_ass(path):
    chunks = build_chunks()
    ev = []
    for i, ch in enumerate(chunks):
        a = mp_near(ch[0][1]) - 0.03
        b = mp_near(ch[-1][2]) + 0.18
        if i + 1 < len(chunks):
            b = min(b, mp_near(chunks[i + 1][0][1]) - 0.02)
        a = max(a, 0); b = min(b, MAIN_DUR)
        if b - a < 0.25: b = a + 0.25
        parts = []
        for w in ch:
            clean = w[0].strip(".,?!").lower()
            hl = any(clean.startswith(k) for k in KEY)
            parts.append((YEL if hl else WHT) + w[0].upper())
        ev.append(f"Dialogue: 0,{tc(a)},{tc(b)},Sub,,0,0,0,,{' '.join(parts)}")
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W_}
PlayResY: {H_}
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,Inter,64,&H00FFFFFF,&H000000FF,&H00201008,&H80000000,1,0,0,0,100,100,0,0,1,7,2,2,60,60,520,1

[Events]
Format: Layer,Start,End,Style,Name,Text,MarginL,MarginR,MarginV,Effect
"""
    hdr = hdr.replace("Name,Text,MarginL,MarginR,MarginV,Effect", "Name,MarginL,MarginR,MarginV,Effect,Text")
    open(path, "w", encoding="utf-8").write(hdr + "\n".join(ev) + "\n")
    return chunks

# ---------- 3. grafik overlay (PNG RGBA) ----------
def font(p, s): return ImageFont.truetype(p, s)
NAVY = (12, 24, 56, 228); TEAL = (45, 212, 191, 255); RED = (239, 68, 68, 255)
AMBER = (251, 191, 36, 255); WHITE = (255, 255, 255, 255); SOFT = (203, 213, 225, 255)

def card(w, h, fill=NAVY, accent=TEAL, r=36):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill)
    d.rounded_rectangle((0, 0, 14, h - 1), 7, fill=accent)
    return im, d

def center_text(d, cx, y, txt, f, fill=WHITE):
    b = d.textbbox((0, 0), txt, font=f); d.text((cx - (b[2] - b[0]) / 2, y), txt, font=f, fill=fill)

def warn_icon(d, x, y, s, col=AMBER):
    d.polygon([(x + s / 2, y), (x + s, y + s * .9), (x, y + s * .9)], fill=col)
    d.rectangle((x + s / 2 - s * .05, y + s * .3, x + s / 2 + s * .05, y + s * .62), fill=NAVY)
    d.ellipse((x + s / 2 - s * .06, y + s * .68, x + s / 2 + s * .06, y + s * .8), fill=NAVY)

def bolt(d, x, y, s, col=AMBER):
    p = [(.55, 0), (.15, .55), (.45, .55), (.3, 1), (.85, .4), (.52, .4), (.7, 0)]
    d.polygon([(x + a * s, y + b * s) for a, b in p], fill=col)

def dots(d, x, y, s, col=WHITE):
    import random; rnd = random.Random(3)
    for _ in range(7):
        r = rnd.randint(4, 9); cx = x + rnd.random() * s; cy = y + rnd.random() * s
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)

def web(d, x, y, s, col=WHITE):
    c = (x + s / 2, y + s / 2)
    import math
    for k in range(8):
        a = k * math.pi / 4
        d.line((c[0], c[1], c[0] + math.cos(a) * s / 2, c[1] + math.sin(a) * s / 2), fill=col, width=3)
    for rr in (.2, .35, .5):
        pts = [(c[0] + math.cos(k * math.pi / 4) * s * rr, c[1] + math.sin(k * math.pi / 4) * s * rr) for k in range(9)]
        d.line(pts, fill=col, width=3)

def chip(name, icon, line1, line2=None, accent=AMBER):
    w, h = 900, 190
    im, d = card(w, h, accent=accent)
    icon(d, 50, 40, 110)
    fs = 58
    while d.textbbox((0, 0), line1, font=font(FX, fs))[2] > 660: fs -= 2
    d.text((200, 38 if line2 else 60), line1, font=font(FX, fs), fill=WHITE)
    if line2: d.text((200, 112), line2, font=font(FR, 38), fill=SOFT)
    im.save(f"{WORK}/{name}.png"); return name

def banner(name, big, small=None, col=RED, h=170, bigsize=76):
    w = 900
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 34, fill=col)
    if small:
        center_text(d, w / 2, 20, big, font(FX, bigsize), WHITE)
        center_text(d, w / 2, h - 60, small, font(FR, 36), (255, 235, 235, 255))
    else:
        center_text(d, w / 2, (h - bigsize) / 2 - 12, big, font(FX, bigsize), WHITE)
    im.save(f"{WORK}/{name}.png"); return name

def eye_diagram(name):
    w, h = 900, 380
    im, d = card(w, h, accent=TEAL)
    # bola mata (sisi) di kiri
    cx, cy, R = 250, 190, 120
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(240, 244, 250, 255))
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=(148, 163, 184, 255), width=5)
    d.pieslice((cx - R + 10, cy - R + 10, cx + R - 10, cy + R - 10), 295, 65, fill=None, outline=RED, width=14)  # retina (belakang)
    d.ellipse((cx - R - 20, cy - 38, cx - R + 40, cy + 38), fill=(125, 211, 252, 255))     # kornea/depan
    d.ellipse((cx - R + 20, cy - 28, cx - R + 70, cy + 28), fill=(30, 41, 59, 255))        # kanta
    # label retina
    d.line((cx + R + 5, cy - 40, 470, 95), fill=RED, width=4)
    d.text((478, 68), "RETINA", font=font(FX, 50), fill=(252, 165, 165, 255))
    d.text((478, 130), "lapisan di belakang mata", font=font(FR, 30), fill=SOFT)
    # anak panah ke otak
    d.line((cx + R + 10, cy + 40, 560, 270), fill=TEAL, width=6)
    d.polygon([(572, 276), (545, 285), (556, 258)], fill=TEAL)
    d.rounded_rectangle((590, 240, 860, 320), 30, fill=(30, 58, 110, 255))
    center_text(d, 725, 262, "OTAK", font(FX, 40), WHITE)
    d.text((478, 188), "hantar gambar ke otak", font=font(FB, 32), fill=WHITE)
    im.save(f"{WORK}/{name}.png"); return name

def stat24(name):
    w, h = 900, 300
    im, d = card(w, h, accent=AMBER)
    d.text((60, 20), "24", font=font(FX, 190), fill=AMBER)
    d.text((310, 52), "JAM", font=font(FX, 88), fill=WHITE)
    d.text((300, 150), "pembaikan disebut dalam", font=font(FR, 34), fill=SOFT)
    d.text((300, 190), "panduan, jika bahagian tengah", font=font(FR, 32), fill=SOFT)
    d.text((300, 230), "retina masih melekat", font=font(FR, 32), fill=SOFT)
    im.save(f"{WORK}/{name}.png"); return name

def fact_card(name, title, lines, accent=TEAL, h=230, tsize=54):
    im, d = card(900, h, accent=accent)
    d.text((50, 30), title, font=font(FX, tsize), fill=WHITE)
    y = 30 + tsize + 26
    for ln in lines:
        d.text((50, y), ln, font=font(FR, 40), fill=SOFT); y += 54
    im.save(f"{WORK}/{name}.png"); return name

def endcard(name):
    im = Image.new("RGBA", (W_, H_), (8, 16, 40, 235)); d = ImageDraw.Draw(im)
    warn_icon(d, W_ / 2 - 90, 520, 180)
    center_text(d, W_ / 2, 760, "JANGAN TUNGGU.", font(FX, 92), WHITE)
    center_text(d, W_ / 2, 900, "Periksa mata segera.", font(FB, 64), (153, 246, 228, 255))
    center_text(d, W_ / 2, 1060, "Kilat cahaya, bintik / benang baharu,", font(FR, 40), SOFT)
    center_text(d, W_ / 2, 1120, "atau tirai menutup pandangan", font(FR, 40), SOFT)
    d.rounded_rectangle((120, 1230, W_ - 120, 1360), 34, fill=RED)
    center_text(d, W_ / 2, 1262, "KE HOSPITAL HARI INI", font(FX, 66), WHITE)
    center_text(d, W_ / 2, 1700, "Maklumat umum untuk kesedaran, bukan pengganti nasihat doktor.", font(FR, 28), (148, 163, 184, 255))
    im.save(f"{WORK}/{name}.png"); return name

OV = []  # (png, src_start, src_end, y)
Y = 150
OV.append((chip("o1", warn_icon, "Kilat cahaya", "di tepi mata", AMBER), 0.85, 2.85, Y))
OV.append((chip("o2", dots, "Bintik hitam", "tiba-tiba, makin banyak", AMBER), 3.00, 5.0, Y))
OV.append((chip("o3", web, "Benang / sarang labah-labah", None, AMBER), 5.0, 7.30, Y))
OV.append((banner("o4", "JANGAN TUNGGU ESOK", "Tindakan segera menyelamatkan penglihatan", RED, 190, 70), 7.40, 8.62, Y))
OV.append((fact_card("o5", "Retina koyak / tertanggal", ["Itu mungkin tandanya."], TEAL, 190, 56), 8.70, 11.7, Y))
OV.append((eye_diagram("o6"), 11.95, 16.0, Y - 20))
OV.append((banner("o7", "KECEMASAN PERUBATAN", "Retina tertanggal", RED, 190, 66), 16.15, 20.75, Y))
OV.append((fact_card("o8", "Selalunya TIDAK SAKIT", ["Jangan tunggu sampai sakit."], AMBER, 190, 58), 20.95, 22.9, Y))
OV.append((fact_card("o9", "Kebanyakannya tak serius", ["Tapi hanya pemeriksaan mata", "yang boleh pastikan."], TEAL, 250, 54), 23.0, 28.8, Y))
OV.append((fact_card("o10", "Pakar di Malaysia", ["Nasihatkan pemeriksaan segera."], TEAL, 190, 56), 28.9, 33.0, Y))
OV.append((stat24("o11"), 33.1, 40.7, Y))
OV.append((chip("o12", warn_icon, "Tirai atau bayang", "menutup sebahagian pandangan", RED), 40.95, 46.0, Y))
OV.append((banner("o13", "KE HOSPITAL HARI INI", None, RED, 150, 70), 46.0, 47.98, Y))
endcard("end")

# ---------- 4. ffmpeg ----------
def build():
    ass = f"{ROOT}/work/awareness.ass"
    chunks = build_ass(ass)
    srt = f"{ROOT}/work/awareness.srt"
    with open(srt, "w", encoding="utf-8") as f:
        for i, ch in enumerate(chunks, 1):
            a = mp_near(ch[0][1]); b = mp_near(ch[-1][2]) + 0.15
            t = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(x%1*1000):03d}"
            f.write(f"{i}\n{t(a)} --> {t(b)}\n{' '.join(x[0] for x in ch)}\n\n")

    inputs = ["-i", SRC]
    fc = []
    # video: trim + zoom selang-seli untuk sorok jump-cut
    for i, (a, b) in enumerate(KEEP):
        z = 1.0 if i % 2 == 0 else 1.12
        zw, zh = int(W_ * z) // 2 * 2, int(H_ * z) // 2 * 2
        yoff = int((zh - H_) * 0.25)
        fc.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,scale={zw}:{zh},crop={W_}:{H_}:{(zw-W_)//2}:{yoff}[v{i}]")
        fc.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b-a-0.012:.3f}:d=0.012[a{i}]")
    n = len(KEEP)
    fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    fc.append(f"[vc]eq=contrast=1.06:saturation=1.12:brightness=0.01,format=yuv420p[vb]")
    # extend hujung untuk end card
    fc.append(f"[vb]tpad=stop_mode=clone:stop_duration={END_HOLD}[vt]")
    cur = "vt"
    for k, (png, a, b, y) in enumerate(OV):
        oa, ob = mp_near(a), mp_near(b)
        d = ob - oa
        inputs += ["-loop", "1", "-framerate", "30", "-t", f"{d:.3f}", "-i", f"{WORK}/{png}.png"]
        idx = k + 1
        fc.append(f"[{idx}:v]format=rgba,fade=t=in:st=0:d=0.28:alpha=1,fade=t=out:st={d-0.28:.3f}:d=0.28:alpha=1,setpts=PTS+{oa:.3f}/TB[ov{k}]")
        fc.append(f"[{cur}][ov{k}]overlay=x=(W-w)/2:y={y}:eof_action=pass[t{k}]")
        cur = f"t{k}"
    # subtitle
    fc.append(f"[{cur}]subtitles={ass}:fontsdir=/usr/share/fonts/opentype/inter[vs]")
    # end card
    ei = len(OV) + 1
    inputs += ["-loop", "1", "-framerate", "30", "-t", f"{END_HOLD}", "-i", f"{WORK}/end.png"]
    fc.append(f"[{ei}:v]format=rgba,fade=t=in:st=0:d=0.35:alpha=1,setpts=PTS+{MAIN_DUR:.3f}/TB[end]")
    fc.append(f"[vs][end]overlay=0:0:eof_action=pass[vout]")
    # audio: bersihkan + loudnorm -14 LUFS
    fc.append(f"[ac]highpass=f=80,afftdn=nf=-28,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
              f"afade=t=out:st={MAIN_DUR-0.2:.3f}:d=0.2,apad=pad_dur={END_HOLD},loudnorm=I=-14:TP=-1.5:LRA=9[aout]")
    out = f"{ROOT}/output/awareness_retina_final.mp4"
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
           "-t", f"{TOTAL:.3f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print(out, f"{TOTAL:.2f}s")

if __name__ == "__main__":
    build()
