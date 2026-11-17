#!/usr/bin/env python3
"""Video awareness 'Gosok Mata' — potong senyap + grafik overlay (di belakang orang guna matte) + subtitle karaoke.

Guna:  python3 scripts/awareness_build.py preview <saat_sumber> [...]   -> work/prev_*.jpg
       python3 scripts/awareness_build.py render                        -> work/video_noaudio.mp4 + work/audio_cut.wav
Perlu: work/matte.npy (MODNet, 540x960 uint8), work/cc_shot.png, work/words_final.json
"""
import sys, json, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SRC = "input/gosok_mata.mov"
FD = "/usr/share/fonts/opentype/inter/"
def F(name, size): return ImageFont.truetype(FD + f"Inter-{name}.otf", size)
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

NAVY = (9, 24, 48); TEAL = (25, 195, 177); AMBER = (255, 200, 87); RED = (255, 107, 107)
WHITE = (255, 255, 255); MUTED = (170, 188, 212); PURPLE = (140, 110, 255)

# ---------------------------------------------------------------- potongan (masa sumber)
SILENCES = [(4.763,5.334),(12.938,13.390),(17.410,17.906),(19.701,20.566),(22.162,22.558),(25.308,25.633),
            (27.879,28.221),(35.320,35.780),(39.930,40.321),(43.641,44.053),(48.102,48.487),(49.659,49.979),
            (57.361,57.704),(60.412,60.791),(65.203,65.504)]
REMOVE = [(0, 1.75), (26.28, 32.74)]            # intro senyap + tersasul (kornea yang memanjang…)
for s, e in SILENCES:
    if e - s >= 0.35 and not (26.28 <= s <= 32.74):
        REMOVE.append((s + 0.12, e - 0.12))
END = 66.10
REMOVE.append((END, 999))
REMOVE.sort()
def merged(r):
    out = []
    for a, b in r:
        if out and a <= out[-1][1]: out[-1] = (out[-1][0], max(out[-1][1], b))
        else: out.append((a, b))
    return out
REMOVE = merged(REMOVE)
KEEP = []; p = 0.0
for a, b in REMOVE:
    if a > p: KEEP.append((p, a))
    p = b
def out_t(ts):
    """masa sumber -> masa output"""
    o = 0.0
    for a, b in KEEP:
        if ts <= a: return o
        if ts < b: return o + ts - a
        o += b - a
    return o
def kept(ts): return any(a <= ts < b for a, b in KEEP)

# ---------------------------------------------------------------- util animasi
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(p): return 1 - (1 - p) ** 3
def ease_back(p):
    c1 = 1.4; p = clamp(p); return 1 + (c1 + 1) * (p - 1) ** 3 + c1 * (p - 1) ** 2
def ease_io(p): p = clamp(p); return p * p * (3 - 2 * p)
def win(t, a, b, fin=0.45, fout=0.30):
    """(masuk, keluar) kemajuan 0..1 untuk tetingkap output-time a..b"""
    return clamp((t - a) / fin), clamp((b - t) / fout)

S = 2  # supersample
class Layer:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
    def rr(self, x, y, w, h, r, fill, outline=None, ow=2):
        self.d.rounded_rectangle([x*S, y*S, (x+w)*S, (y+h)*S], r*S, fill=fill, outline=outline, width=ow*S)
    def text(self, x, y, s, font, fill, anchor="la", stroke=0, sfill=(0,0,0,255)):
        self.d.text((x*S, y*S), s, font=font, fill=fill, anchor=anchor, stroke_width=stroke*S, stroke_fill=sfill)
    def tw(self, s, font): return self.d.textlength(s, font=font) / S
    def line(self, pts, fill, width, joint=True):
        self.d.line([(x*S, y*S) for x, y in pts], fill=fill, width=int(width*S), joint="curve" if joint else None)
    def ell(self, cx, cy, rx, ry, fill=None, outline=None, ow=2):
        self.d.ellipse([(cx-rx)*S, (cy-ry)*S, (cx+rx)*S, (cy+ry)*S], fill=fill, outline=outline, width=int(ow*S))
    def poly(self, pts, fill): self.d.polygon([(x*S, y*S) for x, y in pts], fill=fill)
    def done(self): return self.im.resize((self.w, self.h), Image.LANCZOS)

def F_(n, s): return F(n, s*S)  # font pada skala supersample
FONTS = {}
def fnt(n, s):
    k = (n, s)
    if k not in FONTS: FONTS[k] = F(n, s * S)
    return FONTS[k]

def card(L, x, y, w, h, accent=TEAL, fill=(9, 24, 48, 232)):
    L.rr(x, y, w, h, 34, fill, outline=(255, 255, 255, 46), ow=2)
    L.rr(x + 22, y + 26, 8, h - 52, 4, accent + (255,))

def shadowed(layer_im, blur=16, dy=14, alpha=0.55):
    a = layer_im.split()[3]
    sh = Image.new("RGBA", layer_im.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: int(v * alpha)))
    sh = sh.transform(sh.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    return Image.alpha_composite(sh, layer_im)

# ---------------------------------------------------------------- ikon
def eye_icon(L, cx, cy, sc=1.0, color=TEAL, look=0.0):
    w, h = 90 * sc, 50 * sc
    pts = []
    for i in range(0, 41):
        u = -1 + 2 * i / 40
        pts.append((cx + u * w, cy - h * (1 - u * u) ** 0.9))
    low = [(cx + (-1 + 2 * i / 40) * w, cy + h * (1 - (-1 + 2 * i / 40) ** 2) ** 0.9) for i in range(0, 41)]
    L.line(pts + low[::-1] + [pts[0]], color + (255,), 7 * sc)
    L.ell(cx + look * 14 * sc, cy, 24 * sc, 24 * sc, fill=color + (255,))
    L.ell(cx + look * 14 * sc, cy, 10 * sc, 10 * sc, fill=NAVY + (255,))
    L.ell(cx + look * 14 * sc + 8 * sc, cy - 8 * sc, 5 * sc, 5 * sc, fill=(255, 255, 255, 255))

def warn_icon(L, cx, cy, sc=1.0):
    L.poly([(cx, cy - 34*sc), (cx + 38*sc, cy + 30*sc), (cx - 38*sc, cy + 30*sc)], AMBER + (255,))
    L.rr(cx - 4*sc, cy - 10*sc, 8*sc, 24*sc, 4*sc, NAVY + (255,))
    L.ell(cx, cy + 21*sc, 4.5*sc, 4.5*sc, fill=NAVY + (255,))

def check_icon(L, cx, cy, r=24, color=WHITE, tick=NAVY):
    L.ell(cx, cy, r, r, fill=color + (255,))
    L.line([(cx - r*0.45, cy), (cx - r*0.1, cy + r*0.38), (cx + r*0.5, cy - r*0.36)], tick + (255,), r*0.28)

# ---------------------------------------------------------------- adegan (lapisan di BELAKANG orang) — koordinat kanvas 1080x720
CC = None
def scene_hook(t, ts):
    L = Layer(W, 720)
    card(L, 60, 150, 960, 352)
    L.rr(100, 186, 330, 46, 23, TEAL + (255,))
    L.text(265, 209, "KESIHATAN MATA", fnt("Bold", 24), NAVY + (255,), "mm")
    L.text(100, 250, "Gosok mata", fnt("Black", 112), WHITE + (255,))
    L.text(100, 362, "bila penat?", fnt("Black", 112), TEAL + (255,))
    blink = 0.5 + 0.5 * math.sin(t * 5)
    eye_icon(L, 900, 300, 1.15, AMBER, look=math.sin(t * 2.2))
    return L.done()

def scene_bh(t, ts):
    L = Layer(W, 720)
    card(L, 60, 140, 960, 390, accent=PURPLE)
    L.rr(100, 174, 170, 44, 22, PURPLE + (255,))
    L.text(185, 196, "SUMBER", fnt("Bold", 24), WHITE + (255,), "mm")
    L.text(100, 236, "Berita Harian", ImageFont.truetype(SERIF, 66 * S), WHITE + (255,))
    L.text(100, 322, "Tabiat gosok mata beri", fnt("Bold", 44), WHITE + (255,))
    L.text(100, 376, "kesan buruk", fnt("Bold", 44), AMBER + (255,))
    L.line([(100, 446), (980, 446)], (255, 255, 255, 50), 2)
    L.text(100, 470, "Pegawai Optometri, HSAAS UPM  ·  Dis 2025", fnt("Medium", 30), MUTED + (255,))
    return L.done()

def scene_serius(t, ts, t0):
    L = Layer(W, 720)
    card(L, 60, 150, 960, 400, accent=AMBER)
    warn_icon(L, 135, 235, 1.1)
    L.text(200, 190, "KESAN BURUK", fnt("Black", 70), AMBER + (255,))
    L.text(200, 270, "yang serius", fnt("Bold", 52), WHITE + (255,))
    # garis masa: bergerak ke kanan
    x0, x1, y = 120, 960, 440
    p = ease_io((t - t0 - 0.5) / 4.3)
    L.line([(x0, y), (x1, y)], (255, 255, 255, 60), 8)
    xe = x0 + (x1 - x0) * p
    if p > 0: L.line([(x0, y), (xe, y)], AMBER + (255,), 8)
    L.ell(x0, y, 13, 13, fill=TEAL + (255,))
    L.ell(xe, y, 16, 16, fill=AMBER + (255,))
    L.poly([(x1 + 8, y), (x1 - 18, y - 18), (x1 - 18, y + 18)], (255, 255, 255, 120) if p < 0.97 else AMBER + (255,))
    L.text(x0, y + 28, "Hari ini", fnt("Medium", 28), MUTED + (255,))
    L.text(x1, y + 28, "Jangka panjang", fnt("Bold", 30), WHITE + (255,), "ra")
    return L.done()

def scene_risk(t, ts):
    L = Layer(W, 720)
    card(L, 60, 190, 960, 250, accent=RED)
    L.rr(100, 226, 220, 44, 22, RED + (255,))
    L.text(210, 248, "SATU RISIKO", fnt("Bold", 24), WHITE + (255,), "mm")
    L.text(100, 290, "Keratoconus", fnt("Black", 104), WHITE + (255,))
    return L.done()

def scene_cc(t, ts):
    L = Layer(W, 720)
    x, y, w = 160, 120, 760
    sc = w / CC.width
    img = CC.resize((w, int(CC.height * sc)), Image.LANCZOS).convert("RGBA")
    hh = img.height; bar = 62
    card(L, x - 22, y - 2, w + 44, hh + bar + 26, accent=TEAL, fill=(9, 24, 48, 240))
    L.rr(x + 18, y + 14, 260, 40, 20, TEAL + (255,))
    L.text(x + 148, y + 34, "CLEVELAND CLINIC", fnt("Bold", 21), NAVY + (255,), "mm")
    base = L.done()
    # tampal screenshot dengan sudut bulat
    m = Image.new("L", img.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, img.width, img.height], 22, fill=255)
    base.paste(img, (x, y + bar), m)
    return base

def cornea_morph(ts):
    """0 = normal, 1 = keratoconus"""
    return ease_io((ts - 35.5) / 2.2)

def scene_cornea(t, ts):
    L = Layer(W, 720)
    card(L, 60, 140, 960, 480, accent=TEAL)
    m = cornea_morph(ts)
    col = tuple(int(TEAL[i] * (1 - m) + AMBER[i] * m) for i in range(3))
    # tajuk bertukar
    if m < 0.5:
        L.text(100, 172, "KORNEA NORMAL", fnt("Black", 44), TEAL + (255,))
        L.text(100, 226, "Bulat seperti kubah", fnt("Medium", 30), MUTED + (255,))
    else:
        L.text(100, 172, "KERATOCONUS", fnt("Black", 44), AMBER + (255,))
        L.text(100, 226, "Membonjol seperti kon", fnt("Medium", 30), MUTED + (255,))
    cx, yb, hw = 540, 560, 330
    def prof(u, mm):
        f = (1 - u * u) ** 0.62
        g = math.exp(-((u - 0.08) / 0.46) ** 2) * (1 - abs(u) ** 6)   # kon berpuncak bulat
        return (1 - mm) * f + mm * g
    H0 = 190
    def curve(mm, hmul=1.0):
        return [(cx + u * hw, yb - H0 * hmul * prof(u, mm) - (0 if mm == 0 else 0)) for u in np.linspace(-1, 1, 81)]
    normal = curve(0.0); cur = curve(m, 1.0 + 0.30 * m)
    # akueus (isi bawah lengkung)
    L.poly(cur + [(cx + hw, yb + 36), (cx - hw, yb + 36)], col + (55,))
    # garis rujukan normal (putus-putus) bila membonjol
    if m > 0.04:
        for i in range(0, len(normal) - 1, 2):
            L.line([normal[i], normal[i + 1]], (255, 255, 255, int(150 * m)), 4)
    L.line(cur, col + (255,), 13)
    L.line([(cx - hw - 30, yb + 36), (cx + hw + 30, yb + 36)], (255, 255, 255, 40), 3)
    L.ell(cx - hw, yb, 11, 11, fill=(255, 255, 255, 255)); L.ell(cx + hw, yb, 11, 11, fill=(255, 255, 255, 255))
    # anak panah + label puncak
    if m > 0.6:
        a = clamp((m - 0.6) / 0.4)
        top = min(p[1] for p in cur)
        ax = cx + 0.10 * hw
        L.line([(ax + 170, top - 34), (ax + 36, top + 2)], AMBER + (int(255 * a),), 6)
        L.poly([(ax + 22, top + 6), (ax + 52, top - 14), (ax + 50, top + 16)], AMBER + (int(255 * a),))
        L.text(ax + 180, top - 66, "membonjol", fnt("Bold", 34), AMBER + (int(255 * a),))
    L.text(980, 184, "Ilustrasi keratan sisi", fnt("Medium", 22), MUTED + (200,), "ra")
    return L.done()

def scene_kaitan(t, ts):
    L = Layer(W, 720)
    card(L, 60, 190, 960, 300, accent=AMBER)
    L.text(100, 214, "Ada kaitan dengan", fnt("Bold", 46), WHITE + (255,))
    L.text(100, 274, "kerap gosok mata", fnt("Black", 76), AMBER + (255,))
    L.line([(100, 378), (980, 378)], (255, 255, 255, 50), 2)
    L.text(100, 398, "Cleveland Clinic: dikaitkan, punca belum dapat dibuktikan", fnt("Medium", 26), MUTED + (255,))
    return L.done()

def scene_tips(t, ts, t0):
    L = Layer(W, 720)
    L.rr(60, 120, 520, 66, 33, (9, 24, 48, 235), outline=(255, 255, 255, 46), ow=2)
    L.text(90, 154, "BILA MATA PENAT", fnt("Black", 40), WHITE + (255,), "lm")
    items = [("Kelip banyak kali", 44.0, TEAL), ("Rehatkan mata", 45.7, TEAL), ("Tak hilang? Jumpa pakar", 48.3, AMBER)]
    for i, (s, a, c) in enumerate(items):
        pr = ease_back((t - out_t(a)) / 0.45)
        if pr <= 0: continue
        y = 200 + i * 118
        off = (1 - clamp(pr, 0, 1.1)) * -120
        L.rr(60 + off, y, 960, 100, 30, (9, 24, 48, 235), outline=(255, 255, 255, 46), ow=2)
        L.rr(60 + off, y, 14, 100, 7, c + (255,))
        L.ell(130 + off, y + 50, 30, 30, fill=c + (255,))
        L.text(130 + off, y + 51, str(i + 1), fnt("Black", 36), NAVY + (255,), "mm")
        L.text(190 + off, y + 51, s, fnt("Bold", 46), WHITE + (255,), "lm")
    return L.done()

def scene_product(t, ts, t0):
    L = Layer(W, 720)
    card(L, 60, 130, 960, 370, accent=PURPLE)
    eye_icon(L, 170, 262, 0.95, TEAL, look=math.sin(t * 2))
    L.text(290, 176, "DS PHARMA", fnt("Black", 84), WHITE + (255,))
    L.text(290, 270, "EYE CARE", fnt("Black", 84), TEAL + (255,))
    L.text(100, 394, "Tablet kunyah · penggunaan tradisional", fnt("Bold", 34), WHITE + (255,))
    L.text(100, 442, "untuk kesihatan mata", fnt("Medium", 28), MUTED + (255,))
    # cip KKM / Hologram
    for s, a, x in (("KKM", 57.9, 70), ("HOLOGRAM", 58.9, 300)):
        pr = ease_back((t - out_t(a)) / 0.4)
        if pr <= 0: continue
        sc = clamp(pr, 0, 1.1); w, h = (190 if s == "KKM" else 330), 76
        cxm = x + w / 2; cy = 560
        ww = w * sc; hh = h * sc
        L.rr(cxm - ww/2, cy - hh/2, ww, hh, 38 * sc, TEAL + (255,))
        check_icon(L, cxm - ww/2 + 40, cy, 22 * sc)
        L.d.ellipse([0, 0, 0, 0])
        L.text(cxm - ww/2 + 74 * sc, cy + 2, s, fnt("Black", int(36 * sc)), NAVY + (255,), "lm")
    return L.done()

def scene_cta(t, ts, t0):
    L = Layer(W, 720)
    card(L, 60, 170, 960, 330, accent=AMBER, fill=(9, 24, 48, 240))
    L.text(100, 196, "DAPATKAN DI", fnt("Bold", 40), MUTED + (255,))
    L.text(100, 252, "Bakul Kuning", fnt("Black", 100), AMBER + (255,))
    L.text(100, 392, "Tak jumpa? Tengok di profil kami", fnt("Bold", 38), WHITE + (255,))
    # bakul
    cx, cy = 880, 300
    pulse = 1 + 0.06 * math.sin(t * 6)
    L.rr(cx - 60*pulse, cy - 20*pulse, 120*pulse, 70*pulse, 14, AMBER + (255,))
    L.line([(cx - 40*pulse, cy - 20*pulse), (cx - 22*pulse, cy - 60*pulse), (cx + 22*pulse, cy - 60*pulse), (cx + 40*pulse, cy - 20*pulse)], AMBER + (255,), 9)
    return L.done()

# jadual adegan (masa sumber): nama, mula, tamat, fungsi
def sched():
    return [
        ("hook", 2.0, 7.62, lambda t, ts: scene_hook(t, ts)),
        ("bh", 7.75, 13.45, scene_bh),
        ("serius", 13.60, 20.45, lambda t, ts: scene_serius(t, ts, out_t(13.60))),
        ("risk", 20.50, 23.55, scene_risk),
        ("cc", 23.55, 26.28, scene_cc),
        ("cornea", 32.76, 38.30, scene_cornea),
        ("kaitan", 38.40, 42.10, scene_kaitan),
        ("tips", 42.35, 50.20, lambda t, ts: scene_tips(t, ts, out_t(42.35))),
        ("product", 52.3, 60.55, lambda t, ts: scene_product(t, ts, out_t(52.3))),
        ("cta", 60.85, 66.10, lambda t, ts: scene_cta(t, ts, out_t(60.85))),
    ]
SCHED = sched()

def behind_layer(t, ts):
    """lapisan 1080x720 RGBA (PIL) untuk masa output t / sumber ts, atau None"""
    acc = None
    for name, a, b, fn in SCHED:
        ta, tb = out_t(a), out_t(b)
        if not (ta - 0.01 <= t <= tb + 0.35): continue
        pin, pout = win(t, ta, tb)
        if pin <= 0 or pout <= 0: continue
        im = fn(t, ts)
        im = shadowed(im)
        e = ease_out(pin)
        dy = int((1 - e) * -60 + (1 - pout) * -30)
        a_mul = clamp(e) * clamp(pout)
        al = im.split()[3].point(lambda v, k=a_mul: int(v * k)); im.putalpha(al)
        if dy: im = im.transform(im.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy))
        acc = im if acc is None else Image.alpha_composite(acc, im)
    return acc

# ---------------------------------------------------------------- subtitle karaoke + lapisan atas
def load_subs():
    w = json.load(open("work/words_final.json"))
    # kumpul ke baris (max ~3-4 kata / 2 baris)
    chunks = []; cur = []
    for word, a, b in w:
        cur.append((word, a, b))
        end_p = word.rstrip()[-1:] in ".?!,"
        long_ = len(" ".join(x[0] for x in cur)) > 22 or len(cur) >= 4
        gap = False
        if end_p or long_: chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    return chunks
CHUNKS = load_subs()

def top_layer(t, ts):
    L = Layer(W, 360)  # kawasan y 1250..1610
    # sumber (kekal) 7.75–50.2
    if out_t(7.75) <= t <= out_t(50.2):
        s = "Sumber: Berita Harian (HSAAS UPM), Dis 2025 · Cleveland Clinic"
        f = fnt("Medium", 25); tw = L.tw(s, f); x = (W - tw) / 2
        pin, pout = win(t, out_t(7.75) + 0.2, out_t(50.2), 0.4, 0.4)
        a = int(255 * ease_out(pin) * pout)
        L.rr(x - 26, 252, tw + 52, 52, 26, (9, 24, 48, int(210 * ease_out(pin) * pout)), outline=(255, 255, 255, int(50 * pin * pout)), ow=2)
        L.text(W / 2, 279, s, f, (225, 235, 250, a), "mm")
    # subtitle
    for ch in CHUNKS:
        a, b = ch[0][1], ch[-1][2]
        if not kept(ch[0][1] + 0.01) and not kept(a + 0.05): pass
        if a - 0.05 <= ts <= b + 0.25:
            words = [w[0].strip() for w in ch]
            f = fnt("Black", 64)
            sp = L.tw(" ", f)
            widths = [L.tw(w, f) for w in words]
            total = sum(widths) + sp * (len(words) - 1)
            lines = [list(range(len(words)))]
            if total > W - 150:  # pecah dua baris
                half = math.ceil(len(words) / 2); lines = [list(range(half)), list(range(half, len(words)))]
            y = 28
            for ln in lines:
                lw = sum(widths[i] for i in ln) + sp * (len(ln) - 1)
                x = (W - lw) / 2
                for i in ln:
                    active = ch[i][1] - 0.02 <= ts
                    col = AMBER + (255,) if (ch[i][1] - 0.02 <= ts <= ch[i][2] + 0.02) else (WHITE + (255,))
                    if ts > ch[i][2] + 0.02: col = WHITE + (255,)
                    scale_pop = 1.0
                    L.text(x, y, words[i], f, col, "la", stroke=7, sfill=(8, 14, 30, 255))
                    x += widths[i] + sp
                y += 80
            break
    return L.done()

def progress_bar(img, t, total):
    p = clamp(t / total); w = int(W * p)
    img[0:10, :, :] = (img[0:10, :, :].astype(np.float32) * 0.5).astype(np.uint8)
    img[0:10, :w, :] = TEAL[::-1]

# ---------------------------------------------------------------- komposit
BLOCKS = [1.75, 7.68, 13.48, 20.5, 32.74, 38.4, 42.16, 50.06, 57.7, 60.84, 66.2]
def zoom_for(ts):
    k = max(i for i, b in enumerate(BLOCKS[:-1]) if ts >= b) if ts >= BLOCKS[0] else 0
    p = clamp((ts - BLOCKS[k]) / (BLOCKS[k + 1] - BLOCKS[k]))
    base = 1.0 if k % 2 == 0 else 1.07
    return base + 0.04 * p

def to_np_rgba(im):
    a = np.asarray(im, dtype=np.float32)
    return a[..., :3], a[..., 3:4] / 255.0

def compose(frame, matte_half, t, ts, total):
    z = zoom_for(ts)
    M = cv2.getRotationMatrix2D((540, 900), 0, z)
    fr = cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    m = cv2.resize(matte_half, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0
    m = cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    m = np.clip((m - 0.08) / 0.84, 0, 1)
    fr_f = fr.astype(np.float32)
    # latar: gelapkan sedikit + vinjet halus (orang kekal terang)
    yy = np.linspace(-1, 1, H, dtype=np.float32)[:, None]; xx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    vig = 1 - 0.20 * np.clip(xx ** 2 * 0.6 + yy ** 2 * 0.6, 0, 1)
    bg = fr_f * (0.80 * vig)[..., None]
    bg[..., 0] *= 1.0; bg[..., 2] *= 0.98
    out = bg * (1 - m[..., None]) + fr_f * m[..., None] * 1.0
    # kad di belakang orang
    bl = behind_layer(t, ts)
    if bl is not None:
        rgb, a = to_np_rgba(bl)
        rgb = rgb[..., ::-1]  # RGB->BGR
        reg = out[0:720]
        mreg = m[0:720, :, None]
        comp = reg * (1 - a) + rgb * a
        out[0:720] = comp * (1 - mreg) + reg * mreg   # orang kekal di depan kad
        # elak latar tergelap bocor ke atas orang: pulihkan piksel orang
    out = np.clip(out, 0, 255).astype(np.uint8)
    # lapisan atas (sumber + subtitle) y=1250..1610
    tl = top_layer(t, ts)
    rgb, a = to_np_rgba(tl)
    rgb = rgb[..., ::-1]
    reg = out[1250:1610].astype(np.float32)
    out[1250:1610] = np.clip(reg * (1 - a) + rgb * a, 0, 255).astype(np.uint8)
    progress_bar(out, t, total)
    return out

# ---------------------------------------------------------------- main
def main():
    global CC
    CC = Image.open("work/cc_shot.png").convert("RGB")
    mode = sys.argv[1]
    mt = np.load("work/matte.npy", mmap_mode="r")
    cap = cv2.VideoCapture(SRC)
    total = sum(b - a for a, b in KEEP)
    if mode == "preview":
        for s in sys.argv[2:]:
            ts = float(s); cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(ts * FPS))); ok, f = cap.read()
            i = int(round(ts * FPS)); t = out_t(ts)
            o = compose(f, np.array(mt[i]), t, ts, total)
            cv2.imwrite(f"work/prev_{s}.jpg", cv2.resize(o, (540, 960), interpolation=cv2.INTER_AREA))
        return
    # render
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                           "-movflags", "+faststart", "work/video_noaudio.mp4"], stdin=subprocess.PIPE)
    i = 0; n = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        ts = i / FPS
        if kept(ts):
            o = compose(f, np.array(mt[i]), out_t(ts), ts, total)
            ff.stdin.write(o.tobytes()); n += 1
            if n % 90 == 0: print(f"{n} frames  ts={ts:.1f}", flush=True)
        i += 1
    ff.stdin.close(); ff.wait(); print("DONE", n, "frames", total, "s")

if __name__ == "__main__":
    main()
