#!/usr/bin/env python3
"""DS Pharma Eye Care — komposit akhir (tema medical/data).
Prasyarat: work/cut.mp4, work/cut_words.json, work/zbase.mp4 + work/zmatte.mp4 (eyecare_frames.py).
Guna: python3 scripts/eyecare_build.py [--test]
Zon selamat TikTok: atas >= y290, bawah <= y1410, kanan <= x1020. Kad imej DI BELAKANG kepala (matte), panel teks DI DEPAN.
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
W, H, FPS = 1080, 1920, 30
TEST = "--test" in sys.argv
UP = "/root/.claude/uploads/f6d0048b-b12b-5c1a-b5c6-9e624bc0aed8/"
IMG = {"goji": "6d95529d-image.webp", "avokado": "46ef0f02-image.webp", "lobak": "135e8fcb-image.webp",
       "eyebright": "e1884fb7-image.jpg", "hologram": "c348fa3c-image.jpg", "poster": "15d75b0c-image.jpg",
       "pack": "229d533d-image.jpg", "screen": "de747c66-image.jpg"}
F_EB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
F_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
F_MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf"
NAVY, TEAL, RED, AMBER, YEL, WHITE = (10, 38, 68), (25, 214, 200), (255, 77, 94), (255, 176, 32), (255, 196, 0), (255, 255, 255)

words = json.load(open("work/cut_words.json"))
DUR = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", "work/cut.mp4"]))

# ---------- 1. ejaan: ikut skrip user bila bunyi sama ----------
fix = {"diwina": "digunakan", "daripada": "dari", "Ini": "Ni"}
W2 = []
for s, e, w in words:
    w = fix.get(w, w)
    if w.startswith("-") and W2:
        ps, pe, pw = W2[-1]; W2[-1] = (ps, e, pw + w); continue
    W2.append((s, e, w))
words = W2
groups, cur = [], []
for s, e, w in words:
    if cur and (len(cur) >= 3 or cur[-1][2][-1] in ".,?!" or s - cur[-1][1] > 0.35
                or len(" ".join(x[2] for x in cur + [(s, e, w)])) > 20):
        groups.append(cur); cur = []
    cur.append((s, e, w))
if cur: groups.append(cur)
def srt_t(x):
    ms = int(round(x * 1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
os.makedirs("subs", exist_ok=True)
with open("subs/eyecare.srt", "w") as f:
    for i, g in enumerate(groups, 1):
        f.write(f"{i}\n{srt_t(g[0][0])} --> {srt_t(g[-1][1])}\n{' '.join(x[2] for x in g)}\n\n")
def t(x):
    x = max(0, x); return f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"

# ---------- 2. subtitle ASS (kotak navy lut sinar, perkataan semasa cyan) ----------
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,Inter ExtraBold,70,&H00FFFFFF,&H00FFFFFF,&H304A2A0B,&H00000000,0,0,0,0,100,100,0,0,3,18,0,5,40,40,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"""]
for g in groups:
    for i, (s, e, w) in enumerate(g):
        end = g[i + 1][0] if i + 1 < len(g) else e + 0.10
        txt = " ".join((r"{\1c&HD8E619&}" + x[2] + r"{\1c&HFFFFFF&}") if j == i else x[2] for j, x in enumerate(g))
        ass.append(f"Dialogue: 1,{t(s)},{t(end)},Sub,,0,0,0,,{{\\an5\\pos(540,1120)}}{txt}")
open("work/eyecare.ass", "w").write("\n".join(ass) + "\n")

# ---------- 3. aset grafik (PIL) ----------
def shadow_canvas(w, h, m, r, fill, border=None, bw=0):
    cv = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", cv.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 8, m + w, m + h + 8), r, fill=(0, 0, 0, 140))
    cv = Image.alpha_composite(cv, sh.filter(ImageFilter.GaussianBlur(12)))
    ImageDraw.Draw(cv).rounded_rectangle((m, m, m + w, m + h), r, fill=fill, outline=border, width=bw)
    return cv
def ecg(d, x, y, w, color, a=220, k=1.0):
    pts = [(0, 0), (.22, 0), (.30, -.25), (.38, .15), (.46, 0), (.55, 0), (.60, -.9), (.68, 1.0), (.75, -.15), (.82, 0), (1, 0)]
    d.line([(x + px * w, y + py * 22 * k) for px, py in pts], fill=color + (a,), width=max(2, int(4 * k)), joint="curve")
def icon(d, kind, cx, cy, color, k=1.0):
    r = 17 * k; lw = max(2, int(3 * k))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color + (255,), width=lw)
    if kind == "cross":
        d.rectangle((cx - 3 * k, cy - 10 * k, cx + 3 * k, cy + 10 * k), fill=color + (255,)); d.rectangle((cx - 10 * k, cy - 3 * k, cx + 10 * k, cy + 3 * k), fill=color + (255,))
    elif kind == "warn":
        d.polygon([(cx, cy - 10 * k), (cx + 11 * k, cy + 9 * k), (cx - 11 * k, cy + 9 * k)], outline=color + (255,), width=lw)
        d.rectangle((cx - k, cy - 3 * k, cx + k, cy + 3 * k), fill=color + (255,)); d.rectangle((cx - k, cy + 5 * k, cx + k, cy + 7 * k), fill=color + (255,))
    elif kind == "check":
        d.line([(cx - 9 * k, cy), (cx - 2 * k, cy + 8 * k), (cx + 10 * k, cy - 8 * k)], fill=color + (255,), width=int(4 * k), joint="curve")
    elif kind == "rx":
        d.text((cx, cy), "Rx", font=ImageFont.truetype(F_B, int(19 * k)), fill=color + (255,), anchor="mm")
def spaced(d, xy, text, font, fill, sp=3):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill, anchor="lm"); x += d.textlength(ch, font=font) + sp
    return x
def spaced_w(d, text, font, sp=3): return sum(d.textlength(c, font=font) + sp for c in text) - sp

def panel(name, header, body, accent=TEAL, size=54, kind="cross", mono=False, sub=None, sc=1.3, ecg_on=True):
    k = 2 * sc    # lukis pada 2x supaya tajam, kemudian kecilkan separuh
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    fh = ImageFont.truetype(F_B, int(24 * k)); fb = ImageFont.truetype(F_MONO if mono else F_EB, int(size * k)); fs = ImageFont.truetype(F_EB, int(size * .62 * k))
    sp = 3 * k
    hw = 24 * k + 34 * k + 12 * k + spaced_w(tmp, header, fh, sp) + 24 * k + (90 * k if ecg_on else 0)
    bw = tmp.textlength(body, font=fb) + (22 * k + tmp.textlength(sub, font=fs) if sub else 0)
    w = int(max(hw, bw) + 40 * k + 34 * k); h = int(22 * k + 34 * k + 14 * k + size * 1.12 * k + 22 * k); m = int(34 * k)
    cv = shadow_canvas(w, h, m, int(26 * k), NAVY + (240,), accent + (170,), max(2, int(3 * k)))
    d = ImageDraw.Draw(cv)
    d.rounded_rectangle((m, m, m + 14 * k, m + h), int(7 * k), fill=accent + (255,))
    hy = m + 22 * k + 17 * k
    icon(d, kind, m + 40 * k + 17 * k, hy, accent, k)
    spaced(d, (m + 40 * k + 34 * k + 12 * k, hy), header, fh, accent + (255,), sp)
    if ecg_on: ecg(d, m + w - 34 * k - 90 * k, hy, 90 * k, accent, k=k)
    d.line((m + 40 * k, m + 22 * k + 34 * k + 7 * k, m + w - 34 * k, m + 22 * k + 34 * k + 7 * k), fill=accent + (80,), width=max(2, int(2 * k)))
    by = m + 22 * k + 34 * k + 14 * k + size * .56 * k
    d.text((m + 40 * k, by), body, font=fb, fill=WHITE + (255,), anchor="lm")
    if sub: d.text((m + 40 * k + tmp.textlength(body, font=fb) + 22 * k, by + 2 * k), sub, font=fs, fill=accent + (255,), anchor="lm")
    cv = cv.resize((cv.width // 2 * 2 // 2, cv.height // 2 * 2 // 2), Image.LANCZOS) if False else cv.resize((cv.width // 2, cv.height // 2), Image.LANCZOS)
    p = f"work/p_{name}.png"; cv.save(p); return p, cv.size

def cover(im, w, h, box=None):
    if box: im = im.crop(box)
    r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r + 1), int(im.height * r + 1)), Image.LANCZOS)
    l, tp = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, tp, l + w, tp + h))
def img_card(name, key, w, h, box=None):
    b, m = 10, 34
    cv = shadow_canvas(w + 2 * b, h + 2 * b, m, 30, (255, 255, 255, 255))
    im = cover(Image.open(UP + IMG[key]).convert("RGB"), w, h, box)
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), 22, fill=255)
    cv.paste(im, (m + b, m + b), mask)
    d = ImageDraw.Draw(cv)   # penjuru medical: tanda + teal
    d.rounded_rectangle((m + w + 2 * b - 74, m - 16, m + w + 2 * b - 10, m + 22), 18, fill=TEAL + (255,))
    d.rectangle((m + w + 2 * b - 45, m - 8, m + w + 2 * b - 39, m + 14), fill=NAVY + (255,)); d.rectangle((m + w + 2 * b - 54, m - 1, m + w + 2 * b - 30, m + 5), fill=NAVY + (255,))
    p = f"work/c_{name}.png"; cv.save(p); return p, cv.size

def chart_card():
    w, h, m = 1000, 400, 34
    cv = shadow_canvas(w, h, m, 30, NAVY + (232,), TEAL + (150,), 3); d = ImageDraw.Draw(cv)
    fh = ImageFont.truetype(F_B, 32)
    icon(d, "cross", m + 48, m + 46, TEAL)
    spaced(d, (m + 82, m + 46), "KADAR KELIP MATA / SEMINIT", fh, TEAL + (255,), 3)
    ecg(d, m + w - 200, m + 46, 160, TEAL)
    for gy in (140, 220, 290):
        d.line((m + 40, m + gy, m + w - 40, m + gy), fill=(255, 255, 255, 28), width=2)
    d.line((m + 40, m + 330, m + w - 40, m + 330), fill=(255, 255, 255, 170), width=3)
    p = "work/c_chart.png"; cv.save(p); return p, cv.size
def axis(name, text, color):
    f = ImageFont.truetype(F_B, 32); tmp = ImageDraw.Draw(Image.new("RGBA", (5, 5)))
    w = int(spaced_w(tmp, text, f, 3)) + 40; cv = Image.new("RGBA", (w, 50), (0, 0, 0, 0)); d = ImageDraw.Draw(cv)
    spaced(d, (20, 25), text, f, color + (255,), 3); p = f"work/x_{name}.png"; cv.save(p); return p, cv.size
def bar(name, hh, c1, c2):
    bw = 150; cv = Image.new("RGBA", (bw, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(cv)
    for y in range(hh):
        k = y / max(hh - 1, 1); d.line((0, y, bw, y), fill=tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3)) + (255,))
    mask = Image.new("L", (bw, hh), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw, hh + 20), 14, fill=255)
    cv.putalpha(mask); p = f"work/b_{name}.png"; cv.save(p); return p, cv.size
def label(name, text, color, size=84):
    f = ImageFont.truetype(F_MONO, size); tmp = ImageDraw.Draw(Image.new("RGBA", (5, 5)))
    w = int(tmp.textlength(text, font=f)) + 40; h = size + 30
    cv = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(cv)
    d.text((w / 2 + 3, h / 2 + 4), text, font=f, fill=(0, 0, 0, 160), anchor="mm"); d.text((w / 2, h / 2), text, font=f, fill=color + (255,), anchor="mm")
    p = f"work/l_{name}.png"; cv.save(p); return p, cv.size
def cta_button():
    f = ImageFont.truetype(F_EB, 62); tmp = ImageDraw.Draw(Image.new("RGBA", (5, 5)))
    tw = int(tmp.textlength("TEKAN BEG KUNING", font=f)); w, h, m = tw + 150, 120, 30
    cv = shadow_canvas(w, h, m, 60, YEL + (255,)); d = ImageDraw.Draw(cv)
    bx, by = m + 40, m + 60   # ikon beg beli-belah
    d.rounded_rectangle((bx - 22, by - 12, bx + 22, by + 26), 6, fill=NAVY + (255,)); d.arc((bx - 12, by - 28, bx + 12, by + 2), 180, 360, fill=NAVY + (255,), width=5)
    d.text((m + 80 + (w - 80) / 2, m + h / 2 + 2), "TEKAN BEG KUNING", font=f, fill=NAVY + (255,), anchor="mm")
    p = "work/p_cta.png"; cv.save(p); return p, cv.size
def arrow():
    cv = Image.new("RGBA", (150, 110), (0, 0, 0, 0)); d = ImageDraw.Draw(cv)
    d.polygon([(10, 12), (140, 12), (75, 98)], fill=YEL + (255,), outline=NAVY + (255,), width=6)
    p = "work/p_arrow.png"; cv.save(p); return p, cv.size

# ---------- 4. senarai overlay ----------
OV = []   # dict: png,size,s,e,cx,cy,layer,anim,(bottom),(shake),(bounce)
def add(layer, made, s, e, cx, cy, anim="pop", **kw):
    p, (w, h) = made; OV.append(dict(png=p, w=w, h=h, s=s, e=e, cx=cx, cy=cy, layer=layer, anim=anim, **kw))
TOP, BOT, CARDY, CY2 = 385, 1340, 540, 610     # TOP: pusat panel atas (selamat dari bar TikTok); CY2: kad ber-label
def clampx(cx, w): return min(max(cx, w / 2 + 30), 1050 - w / 2)
def TP(name, header, body, accent=TEAL, size=50, kind="cross", **kw):   # panel zon atas (lebih padat)
    return panel(name, header, body, accent, min(size, 52), kind, sc=kw.pop("sc", 1.1), **kw)

# hook
add("front", TP("siang", "SIANG", "LAPTOP", TEAL, 52), 0.0, 3.72, 270, TOP, "slideL")
add("front", TP("malam", "MALAM", "TIKTOK", TEAL, 52), 2.10, 3.72, 810, TOP, "slideR")
add("front", TP("warn", "AMARAN", "HATI-HATI!", RED, 52, "warn"), 3.78, 4.95, 540, TOP, shake=True)
# statistik: kad carta di belakang kepala; bar/nilai/paksi di depan
add("back", chart_card(), 6.28, 12.95, 540, CARDY)
BASE = 670
add("front", axis("n", "NORMAL", WHITE), 6.28, 12.95, 230, 705)
add("front", axis("d", "DEPAN SKRIN", RED), 6.28, 12.95, 850, 705)
add("front", bar("n", 180, (60, 235, 220), (10, 150, 160)), 7.74, 12.95, 230, BASE - 90, "growv", bottom=BASE)
add("front", bar("d", 36, (255, 120, 135), (200, 40, 70)), 10.42, 12.95, 850, BASE - 18, "growv", bottom=BASE)
add("front", label("n", "18x", TEAL), 8.10, 12.95, 230, 450)
add("front", label("d", "3–4x", RED), 10.80, 12.95, 850, 596)
# gejala
for s_, hd, bd, cx in [(14.48, "GEJALA 1", "KERING", 190), (15.52, "GEJALA 2", "PEDIH", 540), (16.14, "GEJALA 3", "KABUR", 890)]:
    add("front", TP("g" + bd, hd, bd, RED, 48, "warn", sc=0.95, ecg_on=False), s_, 16.95, cx, TOP)
add("front", TP("tip1", "TIP 1", "REHATKAN MATA", TEAL, 52, "check"), 17.18, 18.60, 540, TOP)
add("front", TP("tip2", "TIP 2", "JAGA DARI DALAM", TEAL, 52, "check"), 18.64, 21.10, 540, TOP)
# produk (label di atas kad)
add("back", img_card("pack", "pack", 290, 290), 21.26, 28.78, 790, CY2)
pm = TP("produk", "DS PHARMA", "EYE CARE", TEAL, 52, "rx"); add("front", pm, 21.26, 23.60, clampx(790, pm[1][0]), TOP)
add("front", panel("bentuk", "BENTUK", "TABLET KUNYAH", TEAL, 50), 24.02, 26.30, 540, BOT)
add("front", panel("guna", "PENGGUNAAN", "SECARA TRADISIONAL", TEAL, 44), 26.30, 28.78, 540, BOT)
add("front", panel("formula", "FORMULA", "1 TABLET = 4 BAHAN", AMBER, 46, "rx"), 28.78, 31.40, 540, BOT)
add("back", img_card("poster", "poster", 420, 420), 29.60, 31.40, 290, CARDY)
# bahan: kad bergilir kiri/kanan di belakang kepala, label di atas kad
for i, (key, nm, mg, s_, e_, cx) in enumerate([("lobak", "LOBAK MERAH", "60mg", 31.44, 32.94, 790), ("goji", "BUAH GOJI", "50mg", 32.96, 34.04, 290),
                                                ("avokado", "AVOKADO", "15mg", 34.06, 34.92, 790), ("eyebright", "BUNGA EYEBRIGHT", "40mg", 34.94, 36.30, 290)]):
    add("back", img_card(key, key, 380, 280), s_, e_, cx, CY2)
    pm = TP("b" + key, f"BAHAN {i+1}/4", nm, TEAL, 44, "cross", sub=mg, sc=1.0)
    add("front", pm, s_, e_, clampx(cx, pm[1][0]), TOP)
# sasaran
add("back", img_card("screen", "screen", 420, 420), 36.24, 41.70, 290, CARDY)
for s_, e_, bd, ac in [(37.12, 38.00, "ORANG OFIS", TEAL), (38.00, 38.72, "STUDENT", TEAL), (38.72, 39.54, "KAKI SCROLL", TEAL), (39.54, 41.60, "SCREEN TIME TINGGI", RED)]:
    add("front", panel("s" + bd, "SESUAI UNTUK", bd, ac, 50, "check"), s_, e_, 540, BOT)
# MAL + KKM
add("front", TP("mal", "NO. PENDAFTARAN", "MAL22076147T", TEAL, 50, "check", mono=True), 41.96, 43.30, 540, TOP)
add("back", img_card("holo", "hologram", 560, 280, (440, 880, 1100, 1190)), 43.36, 45.40, 770, CY2)
pm = TP("kkm", "SEMAKAN", "HOLOGRAM KKM", TEAL, 48, "check"); add("front", pm, 43.36, 45.40, clampx(770, pm[1][0]), TOP)
add("front", panel("semak", "KEASLIAN", "BOLEH SEMAK SENDIRI", TEAL, 42, "check"), 45.30, 46.60, 540, BOT)
# harga
add("front", TP("harga", "HARGA", "SANGAT MURAH!", AMBER, 52, "rx"), 47.40, 49.40, 540, TOP, shake=True)
add("front", TP("free", "BONUS", "FREE SHIPPING", TEAL, 52, "cross"), 50.72, 53.50, 540, TOP, shake=True)
add("front", panel("skrg", "TAWARAN", "SEKARANG!", AMBER, 50, "rx"), 52.96, 53.65, 540, BOT)
# CTA
add("front", TP("nasihat", "NASIHAT", "JAGA MATA SEBELUM TERLAMBAT", TEAL, 34, "cross"), 54.66, DUR + 0.3, 540, TOP)
add("front", cta_button(), 53.68, DUR + 0.3, 540, BOT + 40)
add("front", arrow(), 53.90, DUR + 0.3, 540, BOT - 75, bounce=True)

# ---------- 5. SFX + audio ----------
def sh(*a): subprocess.run(a, check=True)
sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "aevalsrc='sin(2*PI*(420+2600*t)*t)*exp(-28*t)':d=0.18:s=44100", "-af", "volume=0.9", "work/pop.wav")
sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anoisesrc=d=0.45:c=pink:r=44100:a=0.6", "-af", "bandpass=f=1400:w=1.2,afade=t=in:d=0.18,afade=t=out:st=0.18:d=0.27,volume=1.6", "work/whoosh.wav")
pops = sorted({round(o["s"], 2) for o in OV if o["anim"] in ("pop", "slideL", "slideR") and o["w"] > 200})
woosh = [3.9, 10.6, 29.2, 44.8, 56.0]
fc = [f"[1:a]asplit={len(pops)}" + "".join(f"[p{i}]" for i in range(len(pops))), f"[2:a]asplit={len(woosh)}" + "".join(f"[w{i}]" for i in range(len(woosh)))]
mix = "[0:a]"
for i, s in enumerate(pops): fc.append(f"[p{i}]adelay={int(s*1000)}|{int(s*1000)},volume=0.20[q{i}]"); mix += f"[q{i}]"
for i, s in enumerate(woosh): fc.append(f"[w{i}]adelay={int(s*1000)}|{int(s*1000)},volume=0.25[x{i}]"); mix += f"[x{i}]"
fc.append(mix + f"amix=inputs={1+len(pops)+len(woosh)}:normalize=0:duration=first,alimiter=limit=0.95[m]")
sh("ffmpeg", "-y", "-v", "error", "-i", "work/cut.mp4", "-i", "work/pop.wav", "-i", "work/whoosh.wav", "-filter_complex", ";".join(fc), "-map", "[m]", "-ar", "44100", "work/mix.wav")
log = subprocess.run(["ffmpeg", "-i", "work/mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(log[log.rindex("{"):])
sh("ffmpeg", "-y", "-v", "error", "-i", "work/mix.wav", "-af",
   f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true",
   "-ar", "44100", "work/mix_norm.wav")

# ---------- 6. render ----------
cmd = ["ffmpeg", "-y", "-v", "error", "-i", "work/zbase.mp4", "-i", "work/zmatte.mp4"]
for o in OV: cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{o['e'] - o['s'] + 0.2:.2f}", "-i", o["png"]]
A = len(OV) + 2
def anim_expr(o):
    s, e = o["s"], o["e"]; u = f"(t-{s})"; p = f"clip({u}/0.28,0,1)"
    pin = f"(1+2.70158*pow({p}-1,3)+1.70158*pow({p}-1,2))"; pout = f"clip(({e}-t)/0.15,0.02,1)"
    return pin, pout, u
fl = [f"[0:v]setsar=1,split=2[bg0][bgp]", f"[1:v]scale={W}:{H}:flags=bicubic,format=gray[mt]"]
def ov_filter(i, o, cur):
    s, e, cx, cy, w, h = o["s"], o["e"], o["cx"], o["cy"], o["w"], o["h"]
    pin, pout, u = anim_expr(o); idx = i + 2
    src = f"[{idx}:v]format=rgba,setpts=PTS+{s}/TB"
    out = []
    if o["anim"] == "growv":
        G = f"max(0.02,(1-pow(1-clip({u}/0.55,0,1),3))*clip(({e}-t)/0.15,0.02,1))"
        out.append(f"{src},scale=w={w}:h='max(2,trunc({h}*{G}/2)*2)':eval=frame[c{i}]")
        xy = f"x='{cx}-w/2':y='{o['bottom']}-h'"
    else:
        F = f"max(0.02,{pin}*{pout})" if o["anim"] == "pop" else f"{pout}"
        out.append(f"{src},scale=w='max(2,trunc({w}*{F}/2)*2)':h='max(2,trunc({h}*{F}/2)*2)':eval=frame[c{i}]")
        dx = ""
        if o["anim"] in ("slideL", "slideR"):
            sgn = "-" if o["anim"] == "slideL" else ""
            dx = f"+({'-' if sgn else ''}800*pow(1-clip({u}/0.35,0,1),3))"
        if o.get("shake"): dx += f"+10*sin(55*{u})*clip(({s}+0.8-t)/0.8,0,1)"
        dy = f"+30*abs(sin(5*{u}))" if o.get("bounce") else ""
        xy = f"x='{cx}-w/2{dx}':y='{cy}-h/2{dy}'"
    out.append(f"{cur}[c{i}]overlay={xy}:enable='between(t,{s},{e})'[n{i}]")
    return out, f"[n{i}]"
cur = "[bg0]"
for i, o in enumerate(OV):
    if o["layer"] != "back": continue
    f_, cur = ov_filter(i, o, cur); fl += f_
fl += [f"[bgp][mt]alphamerge[person]", f"{cur}[person]overlay=0:0:format=auto[pp]"]; cur = "[pp]"
for i, o in enumerate(OV):
    if o["layer"] != "front": continue
    f_, cur = ov_filter(i, o, cur); fl += f_
fl.append(f"{cur}ass=work/eyecare.ass,format=yuv420p[v]")
os.makedirs("output", exist_ok=True)
out = "output/eyecare_test.mp4" if TEST else "output/eyecare_final.mp4"
cmd += ["-i", "work/mix_norm.wav", "-filter_complex", ";".join(fl), "-map", "[v]", "-map", f"{A}:a", "-r", str(FPS),
        "-c:v", "libx264", "-crf", "30" if TEST else "18", "-preset", "ultrafast" if TEST else "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out]
sh(*cmd)
print(out, len(OV), "overlay")
