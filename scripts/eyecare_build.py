#!/usr/bin/env python3
"""Eye Care (goji) edutainment — enjin render overlay.
Guna: python3 scripts/eyecare_build.py [--preview t1,t2,...] [--out output/x.mp4]
Footage asal tidak diubah; semua grafik ialah overlay (PIL, vektor melalui kod).
Timecode dari notes/eyecare_beatmap_v0.md (Whisper) + analisis tenaga audio.
"""
import math, os, subprocess, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "input/raw.mov")
W, H, FPS = 1080, 1920, 30

# ---- Brand (disampel piksel daripada gambar kotak; DEEP = PURPLE digelapkan 50%) ----
PURPLE = (84, 57, 150)      # #543996 permukaan kotak
TEAL = (127, 221, 218)      # #7FDDDA jalur sisi kotak
DEEP = (42, 28, 75)         # terbitan
WHITE = (255, 255, 255)
LAV = (200, 190, 235)
CARD = (112, 88, 176)

CUT = 74.44                 # perkataan terakhir "sendiri" tamat ~74.42
TOTAL = 78.04               # end card 3.6s selepas perkataan terakhir
END_SRC0, END_SRC1 = 79.10, 79.30   # bingkai senyum selepas ucapan (freeze selepas ini)
PANEL_H = 1056              # L2: grafik atas 55%
PRES_H = H - PANEL_H        # penyampai bawah 45%

# ---------------- font ----------------
_fc = {}
def F(kind, size, wght):
    k = (kind, size, wght)
    if k not in _fc:
        p = os.path.join(ROOT, "assets/fonts", "Montserrat-VF.ttf" if kind == "M" else "NotoSans-VF.ttf")
        ft = ImageFont.truetype(p, size)
        ft.set_variation_by_axes([wght] if kind == "M" else [wght, 100])
        _fc[k] = ft
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_back(x, s=1.2):
    x = clamp(x); c3 = s + 1
    return 1 + c3 * (x - 1) ** 3 + s * (x - 1) ** 2
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)

def anim(t, t0, t1, din=0.36, dout=0.12):
    """-> (alpha, scale). Entrance overshoot kecil, exit pantas."""
    if t < t0 or t >= t1: return 0.0, 1.0
    p = (t - t0) / din
    a = clamp(p * 2.5); s = 0.84 + 0.16 * ease_out_back(p)
    if t > t1 - dout:
        q = (t - (t1 - dout)) / dout
        a *= 1 - q; s *= 1 - 0.04 * q
    return a, s

# ---------------- sprite helpers ----------------
def with_alpha(spr, a):
    if a >= 0.999: return spr
    s = spr.copy(); al = s.getchannel("A").point(lambda v: int(v * a)); s.putalpha(al); return s

def paste(canvas, spr, cx, cy, a=1.0, sc=1.0):
    if a <= 0.003 or sc <= 0.01: return
    if abs(sc - 1) > 0.004:
        spr = spr.resize((max(1, int(spr.width * sc)), max(1, int(spr.height * sc))), Image.BILINEAR)
    spr = with_alpha(spr, a)
    canvas.paste(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)), spr)

def runs_sprite(words, kind="M", size=60, wght=800, color=WHITE, shadow=True, maxw=None, align="center", boxcolor=TEAL, boxtext=DEEP, line_gap=1.12):
    """words: list[(text, boxed)]. Kotak teal di belakang kata kunci = satu-satunya bentuk penekanan."""
    ft = F(kind, size, wght)
    words = [(w, b) for (tx, b) in words for w in ([tx] if b else tx.split())]
    asc, desc = ft.getmetrics()
    px, py, rad = int(size * 0.2), int(size * 0.06), int(size * 0.16)
    sp = ft.getlength(" ")
    def wlen(wd): return ft.getlength(wd[0])
    # susun baris
    lines, cur, curw = [], [], 0
    for wd in words:
        wl = wlen(wd) + (2 * px if wd[1] else 0)
        add = wl + (sp if cur else 0)
        if maxw and cur and curw + add > maxw:
            lines.append(cur); cur, curw = [wd], wl
        else:
            cur.append(wd); curw += add
    if cur: lines.append(cur)
    lh = int((asc + desc) * line_gap) + 2 * py
    pad = 18
    def linew(ln):
        w = 0
        for i, wd in enumerate(ln):
            w += wlen(wd) + (2 * px if wd[1] else 0) + (sp if i else 0)
        return w
    tw = int(max(linew(l) for l in lines))
    img = Image.new("RGBA", (tw + 2 * pad, lh * len(lines) + 2 * pad), (0, 0, 0, 0))
    shl = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d, ds = ImageDraw.Draw(img), ImageDraw.Draw(shl)
    for li, ln in enumerate(lines):
        w = linew(ln)
        x = pad + ((tw - w) / 2 if align == "center" else 0)
        base = pad + li * lh + py + asc
        for i, wd in enumerate(ln):
            if i: x += sp
            if wd[1]:
                top = pad + li * lh
                d.rounded_rectangle((x, top, x + wlen(wd) + 2 * px, top + lh - 2), rad, fill=boxcolor)
                d.text((x + px, base), wd[0], font=ft, fill=boxtext, anchor="ls")
                x += wlen(wd) + 2 * px
            else:
                d.text((x, base), wd[0], font=ft, fill=color, anchor="ls")
                if shadow: ds.text((x, base + 4), wd[0], font=ft, fill=(0, 0, 0, 170), anchor="ls")
                x += wlen(wd)
    if shadow:
        shl = shl.filter(ImageFilter.GaussianBlur(5))
        out = Image.alpha_composite(shl, img)
        return out
    return img

def pill(text, size=30, fill=WHITE, tc=DEEP, kind="N", wght=700, padx=30, pady=16):
    ft = F(kind, size, wght); asc, desc = ft.getmetrics()
    w = int(ft.getlength(text)) + 2 * padx; h = asc + desc + 2 * pady
    s = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    sh = Image.new("RGBA", s.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((8, 12, 8 + w, 12 + h), h // 2, fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(5)); s = Image.alpha_composite(s, sh)
    d = ImageDraw.Draw(s); d.rounded_rectangle((8, 8, 8 + w, 8 + h), h // 2, fill=fill)
    d.text((8 + padx, 8 + pady + asc), text, font=ft, fill=tc, anchor="ls")
    return s

def card_bg(w, h, fill=CARD, alpha=235, rad=36):
    s = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", s.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((20, 28, 20 + w, 28 + h), rad, fill=(0, 0, 0, 110))
    s = Image.alpha_composite(s, sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(s).rounded_rectangle((20, 20, 20 + w, 20 + h), rad, fill=fill + (alpha,))
    return s

# ---------------- vektor (supersample) ----------------
SS = 3
def vec(w, h, fn):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im); fn(d, SS)
    return im.resize((w, h), Image.LANCZOS)

def goji_icon(size=110):
    def fn(d, s):
        w = h = size * s
        # batang & kelopak hijau
        d.ellipse((w * .40, h * .02, w * .60, h * .18), fill=(86, 150, 80))
        d.line((w * .5, h * .10, w * .56, h * .0), fill=(70, 120, 60), width=int(4 * s))
        # badan beri
        d.ellipse((w * .22, h * .12, w * .78, h * .98), fill=(214, 62, 48))
        d.ellipse((w * .22, h * .12, w * .78, h * .98), outline=(170, 40, 34), width=int(3 * s))
        d.ellipse((w * .32, h * .26, w * .46, h * .48), fill=(246, 130, 110))
    return vec(size, size, fn)

def bowl_sprite():
    bw, bh = 640, 330
    def fn(d, s):
        # badan mangkuk: separuh bawah elips berpusat y=110
        d.pieslice((20 * s, -100 * s, (bw - 20) * s, 320 * s), 0, 180, fill=TEAL)
        d.ellipse((20 * s, 30 * s, (bw - 20) * s, 190 * s), fill=(210, 245, 243))      # bibir
        d.ellipse((46 * s, 44 * s, (bw - 46) * s, 176 * s), fill=(244, 227, 181))      # kuah
        d.ellipse((46 * s, 44 * s, (bw - 46) * s, 176 * s), outline=(226, 200, 140), width=int(3 * s))
        d.ellipse((bw * .30 * s, 70 * s, bw * .36 * s, 84 * s), fill=(250, 238, 200))
        d.ellipse((bw * .62 * s, 120 * s, bw * .69 * s, 134 * s), fill=(250, 238, 200))
    return vec(bw, bh, fn)

def eye_sprite():
    w, h = 700, 520
    def fn(d, s):
        cx, cy, r = 400 * s, 260 * s, 205 * s
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(238, 236, 250))            # sklera
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(190, 180, 225), width=int(6 * s))
        d.ellipse((85 * s, 150 * s, 255 * s, 370 * s), fill=(190, 228, 245))          # kornea
        d.ellipse((85 * s, 150 * s, 255 * s, 370 * s), outline=(150, 200, 225), width=int(4 * s))
        d.rectangle((226 * s, 168 * s, 246 * s, 236 * s), fill=(120, 90, 170))        # iris atas
        d.rectangle((226 * s, 284 * s, 246 * s, 352 * s), fill=(120, 90, 170))        # iris bawah
        d.ellipse((248 * s, 205 * s, 322 * s, 315 * s), fill=(250, 232, 170))         # kanta
        # retina (lengkok belakang)
        d.arc((cx - r + 16 * s, cy - r + 16 * s, cx + r - 16 * s, cy + r - 16 * s), -62, 62, fill=(236, 128, 118), width=int(16 * s))
        # makula pada retina
        mx, my = cx + r - 24 * s, cy
        d.ellipse((mx - 20 * s, my - 20 * s, mx + 20 * s, my + 20 * s), fill=(255, 196, 60))
    return vec(w, h, fn), (400 + 205 - 24, 260)   # kedudukan makula dalam sprite

# ---------------- cache sprite ----------------
S = {}
def build_sprites():
    S["goji"] = goji_icon(104)
    S["bowl"] = bowl_sprite()
    S["eye"], S["eye_macula"] = eye_sprite()
    # panel latar L2
    g = np.zeros((PANEL_H, W, 3), np.float32)
    top, bot = np.array(DEEP, np.float32), np.array(PURPLE, np.float32)
    for c in range(3): g[:, :, c] = (top[c] + (bot[c] - top[c]) * np.linspace(0, 1, PANEL_H)[:, None] ** 0.9)
    S["panel"] = Image.fromarray(g.astype(np.uint8))
    # produk (gambar sebenar, label tak diubah)
    box = Image.open(os.path.join(ROOT, "assets/brand/box_front.png")).convert("RGBA")
    box = box.crop((6, 6, box.width - 8, box.height - 8))
    for key, bw in (("box", 780), ("box_big", 800)):
        b = box.resize((bw, int(box.height * bw / box.width)), Image.LANCZOS)
        m = Image.new("L", b.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, b.width - 1, b.height - 1), 14, fill=255)
        b.putalpha(m)
        sh = Image.new("RGBA", (b.width + 80, b.height + 80), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((40, 54, 40 + b.width, 54 + b.height), 16, fill=(0, 0, 0, 120))
        sh = sh.filter(ImageFilter.GaussianBlur(16)); sh.alpha_composite(b, (40, 40)); S[key] = sh
    ho = Image.open(os.path.join(ROOT, "assets/brand/hologram_real.png")).convert("RGBA")
    hb = ho.resize((int(ho.width * 1.75), int(ho.height * 1.75)), Image.LANCZOS)
    m = Image.new("L", hb.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, hb.width - 1, hb.height - 1), 16, fill=255); hb.putalpha(m)
    sh = Image.new("RGBA", (hb.width + 80, hb.height + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((40, 54, 40 + hb.width, 54 + hb.height), 18, fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(16)); sh.alpha_composite(hb, (40, 40)); S["holo"] = sh
    # teks tetap
    R = runs_sprite
    S["slam1a"] = R([("BUKAN", False)], size=170, wght=900)
    S["slam1b"] = R([("HIASAN", True)], size=170, wght=900)
    S["slam2"] = R([("JUJUR", True)], size=210, wght=900)
    S["lbl_goji"] = R([("Beri", False), ("goji", True)], size=72, wght=800)
    S["tl_title"] = R([("Perubatan tradisional Cina", False)], kind="N", size=44, wght=700, maxw=860)
    S["tl_dahulu"] = R([("Dahulu", False)], kind="N", size=38, wght=600, color=LAV, shadow=False)
    S["tl_kini"] = R([("Kini", False)], kind="N", size=38, wght=600, color=LAV, shadow=False)
    S["zx1"] = R([("zeaxanthin", True)], size=84, wght=800)
    S["zx2"] = R([("sejenis", False), ("karotenoid", False)], size=60, wght=700)
    S["eye_lbl"] = R([("makula", True)], size=64, wght=800)
    S["eye_note"] = R([("Rajah ringkas, untuk pendidikan sahaja", False)], kind="N", size=30, wght=500, color=LAV, shadow=False)
    S["c1_head"] = R([("Ringkasan kajian", False)], kind="N", size=34, wght=700, color=LAV, shadow=False)
    S["c1_r1"] = R([("114 orang", True)], size=52, wght=800, shadow=False, align="left")
    S["c1_r2"] = R([("AMD awal", False)], size=52, wght=800, shadow=False, align="left")
    S["c1_r3"] = R([("suplemen goji harian", False)], size=52, wght=800, shadow=False, align="left")
    S["c1_r4"] = R([("ketumpatan", False), ("pigmen makula", True)], size=52, wght=800, shadow=False, align="left")
    S["c2_head"] = R([("Kajian lain", False)], kind="N", size=34, wght=700, color=LAV, shadow=False)
    S["c2_r1"] = R([("Warga emas", True)], size=62, wght=800, shadow=False, align="left")
    S["c2_r2"] = R([("jus goji", False)], size=62, wght=800, shadow=False, align="left")
    S["c2_r3"] = R([("90 hari", True)], size=62, wght=800, shadow=False, align="left")
    S["kk_a"] = R([("Kajian", False)], size=132, wght=900)
    S["kk_b"] = R([("kecil", True)], size=132, wght=900)
    S["kk_txt"] = R([("Ada pakar nutrisi yang cakap banyak artikel goji melebih-lebihkan manfaat.", False)], kind="N", size=42, wght=600, maxw=800, shadow=False)
    S["pr_ekstrak"] = R([("ekstrak", False), ("goji", True)], size=68, wght=800)
    S["pr_trad"] = R([("Digunakan secara tradisional untuk kesihatan mata", False)], kind="N", size=44, wght=600, maxw=800, shadow=False)
    S["mal_lbl"] = R([("No. pendaftaran", False)], kind="N", size=34, wght=600, color=LAV, shadow=False)
    S["mal"] = R([("MAL22076147T", True)], size=74, wght=800, shadow=False)
    S["holo_lbl"] = R([("Hologram", False), ("KKM", True)], size=56, wght=800, shadow=False)
    S["end_mal"] = R([("MAL22076147T", False)], size=64, wght=800, shadow=False)
    S["end_trad"] = R([("Digunakan secara tradisional untuk kesihatan mata", False)], kind="N", size=40, wght=600, maxw=820, shadow=False)
    S["end_warn"] = R([("Ubat tradisional. Sila rujuk ahli farmasi / doktor sebelum mengambil produk ini.", False)], kind="N", size=29, wght=500, color=LAV, maxw=840, shadow=False)
    S["chip_nm"] = pill("Sumber: News-Medical")
    S["chip_hl"] = pill("Sumber: Healthline")
    S["chip_mnt"] = pill("Sumber: Medical News Today")
    S["chip_na"] = pill("Sumber: Nutrition Advance")
    S["chip_lp"] = pill("Sumber: label produk")
    S["card1"] = card_bg(880, 560)
    S["card2"] = card_bg(880, 470)
    # kapsyen
    S["caps"] = [ (a, b, runs_sprite([(w, k) for w, k in words], size=70, wght=800, maxw=920)) for (a, b, words) in CAPS ]

# ---------------- kapsyen: (mula, tamat, [(perkataan, kata_kunci)]) ----------------
def C(a, b, s, kw=()):
    return (a, b, [(w, (i in kw)) for i, w in enumerate(s.split())])
CAPS = [
    C(0.60, 1.38, "Kalau korang perasan"), C(1.38, 2.72, "dalam masakan Cina", (2,)), C(2.72, 3.20, "dia akan ada"),
    C(3.20, 4.12, "masukkan satu"), C(4.12, 5.36, "beri kecil", (0,)), C(5.36, 6.66, "yang dipanggil"),
    C(6.66, 8.10, "nama beri goji", (2,)),
    C(8.24, 9.12, "Dia dah digunakan"), C(9.12, 9.82, "dalam perubatan"), C(9.82, 10.94, "tradisional Cina", (0,)),
    C(10.94, 11.82, "lebih around"), C(11.82, 13.12, "2,000 tahun", (0,)), C(13.12, 13.95, "yang lalu"),
    C(14.08, 15.46, "Dia kaya dengan"), C(15.46, 16.82, "zeaxanthin", (0,)), C(16.82, 18.02, "sejenis karotenoid", (3-1,)),
    C(18.02, 19.06, "yang dikaitkan"), C(19.06, 20.78, "dengan pigmen makula", (2,)),
    C(20.84, 22.08, "Satu kajian"), C(22.08, 22.52, "ke atas"), C(22.52, 24.28, "114 orang", (0,)),
    C(24.28, 26.00, "dengan AMD awal", (1,)), C(26.00, 27.58, "suplemen goji harian", (1,)),
    C(27.58, 29.30, "ditingkatkan ketumpatan"), C(29.30, 30.80, "pigmen makula", (1,)),
    C(31.60, 32.36, "Kajian lain"), C(32.36, 33.88, "tengok warga emas", (2,)), C(33.88, 34.74, "minum jus"),
    C(34.74, 36.40, "buah beri"), C(36.40, 37.43, "goji ni", (0,)), C(37.43, 38.70, "90 hari", (0,)),
    C(38.95, 40.20, "Paras zeaxanthin", (1,)), C(42.70, 44.50, "dan antioksidan"), C(44.50, 46.20, "mereka naik"),
    C(46.47, 47.72, "Tapi jujur"), C(47.72, 49.00, "kebanyakan kajian"), C(49.00, 50.20, "kecil ada pakar", (0,)),
    C(50.20, 51.44, "nutrisi yang cakap"), C(51.44, 53.16, "banyak artikel goji", (2,)),
    C(53.16, 54.76, "melebih-lebihkan"), C(54.76, 55.60, "manfaat"),
    C(57.38, 58.06, "Tetapi"), C(58.06, 59.52, "DS Pharma", (0, 1)), C(59.52, 60.34, "Eye Care", (0, 1)),
    C(60.34, 61.60, "ada ekstrak goji", (2,)), C(61.60, 63.14, "digunakan secara"), C(63.14, 64.42, "tradisional untuk"),
    C(64.42, 66.10, "kesihatan mata", (0, 1)),
    C(66.60, 67.90, "Dan dia berdaftar", (2,)), C(67.90, 68.56, "dengan MAL", (2,)), C(68.56, 69.76, "dan juga mempunyai"),
    C(69.76, 71.60, "hologram berdaftar", (0,)),
    C(71.66, 72.66, "Jadi jangan risau"), C(72.66, 73.54, "boleh semak", (1,)), C(73.54, CUT, "boleh cek sendiri"),
]

# ---------------- segmen & kesan ----------------
SEGS = [(0.0, 3.9, "L1"), (3.9, 46.4, "L2"), (46.4, 48.9, "L1"), (48.9, 71.6, "L2"), (71.6, CUT, "L1"), (CUT, TOTAL, "END")]
ZOOM_THROUGH = [3.9, 46.4, 71.6]
PUNCH = [(11.82, "L2"), (22.52, "L2"), (47.00, "L1")]
FLASH = [13.10, 47.00]
L1_ZOOM = 1.15
CAP_Y_L1, CAP_Y_L2 = 1400, 1445

def seg_at(t):
    for a, b, k in SEGS:
        if a <= t < b: return a, b, k
    return SEGS[-1]

def punch_mult(t, layout):
    m = 1.0
    for t0, lay in PUNCH:
        if lay == layout and t0 - 0.0 <= t < t0 + 0.8:
            x = t - t0
            b = ease_out(x / 0.10) if x < 0.10 else (1.0 if x < 0.45 else 1 - ease_io((x - 0.45) / 0.35))
            m = max(m, 1 + 0.12 * b)
    return m

def view(src, z, anchor, out_anchor, ow, oh):
    ax, ay = anchor; ox, oy = out_anchor
    w, h = ow / z, oh / z
    l = max(0, min(ax - ox / z, src.width - w)); t = max(0, min(ay - oy / z, src.height - h))
    return src.resize((ow, oh), Image.BICUBIC, box=(l, t, l + w, t + h))

# ---------------- komposisi ----------------
def tick_rects(d, s): pass

def draw_timeline(canvas, t):
    p_line = ease_io((t - 9.7) / 3.5)
    a_t, s_t = anim(t, 9.5, 14.1)
    if a_t <= 0: return
    paste(canvas, S["tl_title"], 520, 345, a_t, s_t)
    # garis masa (2x lalu turun)
    im = Image.new("RGBA", (880 * 2, 120 * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, x1, y = 30 * 2, 850 * 2, 60 * 2
    d.line((x0, y, x1, y), fill=(255, 255, 255, 60), width=10)
    xe = x0 + (x1 - x0) * p_line
    d.line((x0, y, xe, y), fill=WHITE + (255,), width=12)
    for i in range(0, 11):
        xx = x0 + (x1 - x0) * i / 10
        d.line((xx, y - 14, xx, y + 14), fill=WHITE + (255 if xx <= xe else 70,), width=5)
    d.ellipse((x0 - 22, y - 22, x0 + 22, y + 22), fill=TEAL)
    d.ellipse((xe - 22, y - 22, xe + 22, y + 22), fill=WHITE)
    paste(canvas, im.resize((880, 120), Image.LANCZOS), 520, 800, a_t, s_t)
    paste(canvas, S["tl_dahulu"], 125, 880, a_t, s_t); paste(canvas, S["tl_kini"], 880, 880, a_t, s_t)
    # pembilang
    if t >= 11.82:
        v = int(2000 * ease_out((t - 11.82) / 1.4))
        txt = f"{v:,}" + ("+" if v >= 2000 else "")
        spr = runs_sprite([(txt, True)], size=200, wght=900, shadow=False)
        paste(canvas, spr, 520, 520, a_t, 1.0)
        paste(canvas, runs_sprite([("tahun", False)], size=74, wght=800), 520, 705, a_t, s_t)

def draw_bowl(canvas, t):
    cx, cy = 540, 640
    if not (3.9 <= t < 8.25): return
    a, sc = anim(t, 3.9, 8.25, din=0.4)
    # ripple dan beri jatuh diurus dengan lapisan sendiri
    paste(canvas, S["bowl"], cx, 690, a, sc)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    drops = [(4.05, 470), (4.30, 575), (4.55, 520)]
    for (t0, x) in drops:
        land = t0 + 0.42
        sy = 635   # tengah permukaan kuah
        if t0 <= t < land:
            u = (t - t0) / 0.42
            y = -80 + (sy + 80) * (u * u)
            paste(canvas, S["goji"], x, y, 1.0, 0.95)
        elif t >= land:
            bob = math.sin((t - land) * 7) * 4 * math.exp(-(t - land) * 2.2)
            paste(canvas, S["goji"], x, sy + bob, a, 0.95)
            for k in range(3):
                u = (t - land - k * 0.18) / 1.1
                if 0 < u < 1:
                    rx = 30 + 190 * ease_out(u); ry = rx * 0.26
                    al = int(200 * (1 - u))
                    d.ellipse((x - rx, sy + 10 - ry, x + rx, sy + 10 + ry), outline=(255, 255, 255, al), width=4)
    canvas.paste(layer, (0, 0), layer)
    if t >= 7.65:
        a2, s2 = anim(t, 7.65, 8.15)
        paste(canvas, S["lbl_goji"], 540, 400, a2, s2)

def row_in(canvas, spr, t, t0, x, y, t1, gap=0.34):
    a, s = anim(t, t0, t1, din=gap)
    if a <= 0: return
    off = (1 - ease_out_back((t - t0) / gap)) * 60
    paste(canvas, spr, x + spr.width / 2 - off, y, a, 1.0)

def draw_top(canvas, t):
    """Kandungan panel grafik L2 (koordinat skrin; selamat x60-960, y250-1500)."""
    draw_bowl(canvas, t)
    draw_timeline(canvas, t)
    # zeaxanthin / karotenoid
    if 14.2 <= t < 19.4:
        a, s = anim(t, 15.4, 19.4)
        paste(canvas, S["zx1"], 520, 480, a, s)
        a, s = anim(t, 16.8, 19.4)
        paste(canvas, S["zx2"], 520, 640, a, s)
    # rajah mata
    if 19.3 <= t < 22.3:
        a, s = anim(t, 19.3, 22.3, din=0.4)
        paste(canvas, S["eye"], 380, 640, a, s)
        mx, my = 380 - 350 + S["eye_macula"][0], 640 - 260 + S["eye_macula"][1]
        a2, s2 = anim(t, 19.8, 22.3)
        if a2 > 0:
            lx, ly = 790, 460
            d = ImageDraw.Draw(canvas)
            q = ease_out((t - 19.8) / 0.35)
            d.line((mx, my, mx + (lx - mx) * q, my + (ly + 40 - my) * q), fill=WHITE, width=5)
            paste(canvas, S["eye_lbl"], lx, ly, a2, s2)
        a3, _ = anim(t, 19.5, 22.3)
        paste(canvas, S["eye_note"], 520, 930, a3, 1.0)
    # kad kajian 1
    if 22.3 <= t < 31.2:
        a, s = anim(t, 22.3, 31.2, din=0.4)
        paste(canvas, S["card1"], 520, 600, a, s)
        if a > 0.5:
            paste(canvas, S["c1_head"], 520, 360, a, 1)
            x = 110
            row_in(canvas, S["c1_r1"], t, 22.52, x, 470, 31.1)
            row_in(canvas, S["c1_r2"], t, 24.62, x, 585, 31.1)
            row_in(canvas, S["c1_r3"], t, 26.00, x, 700, 31.1)
            row_in(canvas, S["c1_r4"], t, 28.62, x, 815, 31.1)
    # kad kajian 2
    if 31.6 <= t < 46.3:
        a, s = anim(t, 31.6, 46.3, din=0.4)
        paste(canvas, S["card2"], 520, 560, a, s)
        if a > 0.5:
            paste(canvas, S["c2_head"], 520, 360, a, 1)
            row_in(canvas, S["c2_r1"], t, 32.86, 110, 480, 46.2)
            row_in(canvas, S["c2_r2"], t, 34.40, 110, 600, 46.2)
            row_in(canvas, S["c2_r3"], t, 37.43, 110, 720, 46.2)
    # kajian kecil
    if 48.95 <= t < 57.1:
        a, s = anim(t, 49.0, 57.1)
        paste(canvas, S["kk_a"], 520, 450, a, s)
        a, s = anim(t, 49.25, 57.1)
        paste(canvas, S["kk_b"], 520, 640, a, s)
        a, s = anim(t, 50.20, 57.1)
        paste(canvas, S["kk_txt"], 520, 840, a, s)
    # produk
    if 57.95 <= t < 66.2:
        a, s = anim(t, 58.06, 66.2, din=0.42)
        paste(canvas, S["box"], 520, 480, a, s)
        a, s = anim(t, 60.68, 66.2); paste(canvas, S["pr_ekstrak"], 520, 770, a, s)
        a, s = anim(t, 62.48, 66.2); paste(canvas, S["pr_trad"], 520, 880, a, s)
    # pendaftaran + hologram (foto sebenar, tak diubah)
    if 66.6 <= t < 71.7:
        a, s = anim(t, 66.7, 71.7, din=0.42)
        paste(canvas, S["holo"], 520, 470, a, s)
        a, s = anim(t, 67.9, 71.7); paste(canvas, S["mal_lbl"], 520, 750, a, s)
        a, s = anim(t, 68.08, 71.7); paste(canvas, S["mal"], 520, 835, a, s)
    # end card
    if t >= CUT:
        a, s = anim(t, CUT + 0.05, TOTAL + 1, din=0.42)
        paste(canvas, S["box_big"], 520, 420, a, s)
        a, s = anim(t, CUT + 0.30, TOTAL + 1); paste(canvas, S["end_mal"], 520, 690, a, s)
        a, s = anim(t, CUT + 0.42, TOTAL + 1); paste(canvas, S["end_trad"], 520, 772, a, s)
        a, s = anim(t, CUT + 0.55, TOTAL + 1); paste(canvas, S["end_warn"], 520, 892, a, s)
    # chips sumber (>=2s, dalam kawasan selamat)
    for (t0, t1, key) in [(9.5, 14.1, "chip_nm"), (15.3, 31.1, "chip_hl"), (32.6, 46.3, "chip_mnt"),
                          (49.0, 56.9, "chip_na"), (60.3, 71.6, "chip_lp"), (CUT + 0.7, TOTAL, "chip_lp")]:
        a, s = anim(t, t0, t1)
        if a > 0: paste(canvas, S[key], 520, 1000, a, s)

SLAM1_T = (0.0, 2.3)
SLAM2_T = (47.0, 48.9)
def draw_slams(canvas, t):
    for (t0, t1), keys, ys in (((0.0, 2.3), ("slam1a", "slam1b"), (1075, 1255)), ((47.0, 48.9), ("slam2",), (1110,))):
        if not (t0 <= t < t1): continue
        x = t - t0
        sc = 1 + 0.15 * (1 - ease_out(x / 0.2)) if x < 0.2 else 1.0
        shake = (math.sin(x * 70) * 12 * max(0, 1 - x / 0.28)) if x < 0.28 else 0
        a = 1.0
        if t > t1 - 0.12: a = 1 - (t - (t1 - 0.12)) / 0.12
        cy = sum(ys) / len(ys)
        for k, y in zip(keys, ys):
            paste(canvas, S[k], 540 + shake, cy + (y - cy) * sc, a, sc)

def draw_caps(canvas, t, y):
    for (a0, a1, spr) in S["caps"]:
        if a0 <= t < a1:
            a, s = anim(t, a0, a1, din=0.30, dout=0.10)
            s = 0.9 + 0.1 * (s - 0.84) / 0.16 if s < 1 else s
            paste(canvas, spr, 540, y, a, s)

def render(k, src):
    """src: PIL RGB 1080x1920 (bingkai sumber atau None)."""
    t = k / FPS
    s0, s1, lay = seg_at(t)
    prog = clamp((t - s0) / (s1 - s0))
    push = 1 + 0.035 * prog
    if lay == "L1":
        z = L1_ZOOM * push * punch_mult(t, "L1")
        frame = view(src, z, (470, 585), (540, 700), W, H)
        draw_slams(frame, t)
        # kapsyen: elak bertindih dengan slam L1 (slam di y~950-1230, kapsyen y1400)
        draw_caps(frame, t, CAP_Y_L1)
    else:
        frame = Image.new("RGB", (W, H))
        frame.paste(S["panel"], (0, 0))
        z = push * punch_mult(t, "L2") if lay == "L2" else (1 + 0.035 * prog)
        pres = view(src, z, (470, 585), (520, 190), W, PRES_H)
        frame.paste(pres, (0, PANEL_H))
        # bayang halus pada sempadan
        sh = Image.new("RGBA", (W, 26), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
        for i in range(26): sd.line((0, i, W, i), fill=(0, 0, 0, int(90 * (1 - i / 26) ** 2)))
        frame.paste(sh, (0, PANEL_H), sh)
        fr = frame.convert("RGBA"); draw_top(fr, t); frame = fr.convert("RGB")
        if lay == "L2": draw_caps(frame, t, CAP_Y_L2)
    # zoom-through ~0.3s (0.15 keluar + 0.15 masuk)
    for tc in ZOOM_THROUGH:
        d = t - tc
        if -0.15 <= d < 0.15:
            u = (d + 0.15) / 0.15 if d < 0 else 1 - d / 0.15
            u = clamp(u); sc = 1 + 0.32 * u * u
            cw, ch = W / sc, H / sc
            frame = frame.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
            frame = frame.filter(ImageFilter.GaussianBlur(14 * u * u))
    for tf in FLASH:
        d = t - tf
        if 0 <= d < 0.13:
            fl = Image.new("RGB", (W, H), WHITE); frame = Image.blend(frame, fl, 0.45 * (1 - d / 0.13))
    return frame

# ---------------- sumber bingkai ----------------
def src_index(k):
    t = k / FPS
    if t < CUT: return k
    e = round(END_SRC0 * FPS) + (k - round(CUT * FPS))
    return min(e, round(END_SRC1 * FPS))

def read_frames(idxs):
    """Penjana bingkai sumber untuk senarai indeks monoton."""
    lo, hi = idxs[0], idxs[-1]
    n = hi - lo + 1
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{lo / FPS:.4f}", "-i", SRC, "-frames:v", str(n),
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    cur, last = lo - 1, None
    for want in idxs:
        while cur < want:
            buf = p.stdout.read(W * H * 3)
            if len(buf) < W * H * 3: break
            last = Image.frombuffer("RGB", (W, H), buf, "raw", "RGB", 0, 1); cur += 1
        yield last
    p.stdout.close(); p.wait()

def render_chunk(args):
    ci, k0, k1 = args
    out = os.path.join(ROOT, f"work/chunks/c_{ci:02d}.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-g", "30",
                            "-threads", "2", out], stdin=subprocess.PIPE)
    ks = list(range(k0, k1)); idxs = [src_index(k) for k in ks]
    # kumpulkan dalam dua julat jika melintasi lompatan end card
    groups, g = [], [0]
    for i in range(1, len(ks)):
        if idxs[i] - idxs[i - 1] > 2: groups.append(g); g = [i]
        else: g.append(i)
    groups.append(g)
    for g in groups:
        for i, fr in zip(g, read_frames([idxs[i] for i in g])):
            enc.stdin.write(render(ks[i], fr).tobytes())
    enc.stdin.close(); enc.wait()
    return out

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", default="")
    ap.add_argument("--out", default=os.path.join(ROOT, "work/video_noaudio.mp4"))
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    os.makedirs(os.path.join(ROOT, "work/chunks"), exist_ok=True)
    build_sprites()
    if a.preview:
        os.makedirs(os.path.join(ROOT, "work/preview"), exist_ok=True)
        for ts in a.preview.split(","):
            k = int(round(float(ts) * FPS))
            fr = next(read_frames([src_index(k)]))
            render(k, fr).save(os.path.join(ROOT, f"work/preview/p_{float(ts):06.2f}.png"))
        return
    total = int(round(TOTAL * FPS)); step = 120
    jobs = [(i, k, min(k + step, total)) for i, k in enumerate(range(0, total, step))]
    with Pool(a.workers) as p: outs = p.map(render_chunk, jobs, chunksize=1)
    lst = os.path.join(ROOT, "work/chunks/list.txt")
    open(lst, "w").write("".join(f"file '{o}'\n" for o in outs))
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", a.out])
    print(a.out)

if __name__ == "__main__":
    main()
