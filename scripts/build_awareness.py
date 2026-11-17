#!/usr/bin/env python3
"""Video awareness 9:16 dengan overlay grafik di belakang/di sekeliling pengacara.

Aliran: frame (PNG 30fps) -> mask orang (MediaPipe) -> lapisan B (di BELAKANG orang)
-> orang di-composite semula di atas B -> lapisan F (depan: kapsyen, chip, progress).

Guna:
  build_awareness.py preview <frame_no> [<frame_no> ...]   # simpan PNG ujian
  build_awareness.py render <start_frame> <end_frame> <out.mp4>

Persekitaran: variabel WORK (folder kerja: fr30/, as/, dl/, words.json) wajib.
"""
import json, math, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

WORK = os.environ["WORK"]
W, H, FPS = 1080, 1920, 30
CROP = 1152                      # tinggi kawasan lapisan B (overlay hanya di bahagian atas)
FD = "/usr/share/fonts/opentype/inter/"

PURPLE_D = (30, 12, 84); PURPLE = (75, 42, 174); PURPLE_L = (150, 120, 245)
TEAL = (79, 209, 197); YEL = (255, 201, 60); RED = (255, 82, 98); WHITE = (255, 255, 255)
INK = (36, 16, 96)

_fc = {}
def font(w, size):
    k = (w, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(FD + f"Inter-{w}.otf", size)
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def e_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def e_back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def e_io(x): x = clamp(x); return x * x * (3 - 2 * x)

def tsize(txt, f, stroke=0):
    d = ImageDraw.Draw(Image.new("L", (4, 4)))
    b = d.textbbox((0, 0), txt, font=f, stroke_width=stroke)
    return b[2] - b[0], b[3] - b[1], b

def text_img(txt, f, fill=WHITE, stroke=0, sfill=PURPLE_D, pad=6):
    w, h, b = tsize(txt, f, stroke)
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), txt, font=f, fill=fill,
                            stroke_width=stroke, stroke_fill=sfill)
    return im

def fit_font(w, txt, maxw, size, stroke=0):
    while size > 10 and tsize(txt, font(w, size), stroke)[0] > maxw: size -= 2
    return font(w, size)

def shadow(im, off=(0, 10), blur=18, alpha=90):
    a = im.getchannel("A").point(lambda v: v * alpha // 255)
    pad = blur * 3
    sh = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    blk = Image.new("RGBA", im.size, (20, 8, 60, 255)); blk.putalpha(a)
    sh.paste(blk, (pad, pad)); sh = sh.filter(ImageFilter.GaussianBlur(blur))
    sh.alpha_composite(im, (pad, pad))
    return sh, pad - off[1]  # (img, offset) ofset dikira pengguna: lihat place()

def rrect(w, h, r, fill, outline=None, ow=2, ss=2):
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=fill,
                                         outline=outline, width=ow * ss if outline else 0)
    return im.resize((w, h), Image.LANCZOS)

def rounded_photo(im, w, h, r):
    im = im.convert("RGB").resize((w, h), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), r * 2, fill=255)
    im.putalpha(m.resize((w, h), Image.LANCZOS)); return im

def with_shadow(im, blur=16, alpha=110, dy=10):
    pad = blur * 3
    out = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    a = im.getchannel("A").point(lambda v: v * alpha // 255)
    blk = Image.new("RGBA", im.size, (18, 6, 56, 255)); blk.putalpha(a)
    out.paste(blk, (pad, pad + dy)); out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad)); return out, pad

def paste(layer, im, x, y, alpha=1.0):
    x, y = int(round(x)), int(round(y))
    if alpha < 0.999:
        a = im.getchannel("A").point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    # clip
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + im.width, layer.width), min(y + im.height, layer.height)
    if x1 <= x0 or y1 <= y0: return
    layer.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def show(layer, im, x, y, t, a, b, how="up", din=0.45, dout=0.28, pad=0):
    """Tampilkan im pada [a,b] dengan animasi masuk/keluar."""
    if t < a or t > b: return
    pin = e_back((t - a) / din); pout = clamp((b - t) / dout)
    al = min(clamp((t - a) / (din * 0.6)), e_io(pout))
    dx = dy = 0; sc = 1.0
    if how == "up": dy = (1 - pin) * 70
    elif how == "down": dy = -(1 - pin) * 70
    elif how == "left": dx = -(1 - pin) * 120
    elif how == "right": dx = (1 - pin) * 120
    elif how == "pop": sc = 0.55 + 0.45 * pin
    if pout < 1: dy -= (1 - e_io(pout)) * 18
    if abs(sc - 1) > 0.003:
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
        x += (1 - sc) * im.width / sc / 2; y += (1 - sc) * im.height / sc / 2
    paste(layer, im, x + dx - pad, y + dy - pad, al)

def ss_draw(w, h, fn, ss=2):
    """Lukis di skala ss lalu kecilkan (anti-alias)."""
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    fn(ImageDraw.Draw(im), ss)
    return im.resize((w, h), Image.LANCZOS)

# ------------------------------------------------------------------ aset
A = lambda n: Image.open(f"{WORK}/as/{n}").convert("RGB")
ASSETS = {}
def asset(n):
    if n not in ASSETS: ASSETS[n] = A(n)
    return ASSETS[n]

CARD = (36, 16, 100, 238)   # kad kaca ungu gelap
CARD_LINE = (150, 120, 245, 120)

def dark_card(w, h, r=30): return rrect(w, h, r, CARD, CARD_LINE, 2)

_cache = {}
def cached(key, fn):
    if key not in _cache: _cache[key] = fn()
    return _cache[key]

# ------------------------------------------------------------------ kad statik
def card_hook():
    def mk():
        out = []
        for txt, col in (("GOSOK MATA", WHITE), ("BUKU JARI?", YEL)):
            f = fit_font("Black", txt, 900, 150, 8)
            out.append(text_img(txt, f, col, 8, PURPLE_D, 14))
        return out
    return cached("hook", mk)

def card_article():
    def mk():
        head = asset("head.png"); w = 900
        h = int(head.height * w / head.width)
        card = rrect(940, h + 30, 28, (255, 255, 255, 255))
        card.alpha_composite(rounded_photo(head, w, h, 14), (20, 15))
        bar = rrect(8, h + 30 - 40, 4, RED); card.alpha_composite(bar, (6, 20))
        return with_shadow(card)
    return cached("article", mk)

def card_logo():
    def mk():
        lg = asset("logo.png").crop((0, 0, 700, 230)); w = 190; h = int(lg.height * w / lg.width)
        pill = rrect(w + 40, h + 24, 20, (255, 255, 255, 255))
        pill.alpha_composite(rounded_photo(lg, w, h, 6), (20, 12))
        return with_shadow(pill, 10, 100, 6)
    return cached("logo", mk)

def tag(txt, col=TEAL, fg=INK, size=26):
    def mk():
        t = text_img(txt, font("ExtraBold", size), fg, 0, pad=0)
        p = rrect(t.width + 36, t.height + 22, (t.height + 22) // 2, col + (255,))
        p.alpha_composite(t, (18, 11)); return p
    return cached(("tag", txt, col, size), mk)

def donut(t):
    """Kad kajian: 202 pesakit vs 355 kawalan (data sebenar artikel)."""
    w, h = 320, 330
    prog = e_out((t - 4.9) / 1.1)
    def fn(d, s):
        d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), 30 * s, fill=CARD, outline=CARD_LINE, width=2 * s)
        d.text((24 * s, 18 * s), "KAJIAN PASUKAN", font=font("ExtraBold", 20 * s), fill=TEAL)
        d.text((24 * s, 42 * s), "PENYELIDIK PERANCIS", font=font("ExtraBold", 20 * s), fill=TEAL)
        cx, cy, R, wd = 160 * s, 148 * s, 70 * s, 26 * s
        box = (cx - R, cy - R, cx + R, cy + R)
        d.arc(box, 0, 360, fill=(255, 255, 255, 40), width=wd)
        frac = 202 / 557
        a0 = -90
        d.arc(box, a0, a0 + 360 * frac * prog, fill=RED, width=wd)
        d.arc(box, a0 + 360 * frac, a0 + 360 * frac + 360 * (1 - frac) * prog, fill=PURPLE_L, width=wd)
        n = int(557 * prog)
        tw = tsize(str(n), font("Black", 44 * s))[0]
        d.text((cx - tw / 2, cy - 30 * s), str(n), font=font("Black", 44 * s), fill=WHITE)
        pw = tsize("peserta", font("Medium", 18 * s))[0]
        d.text((cx - pw / 2, cy + 18 * s), "peserta", font=font("Medium", 18 * s), fill=(210, 200, 250))
        d.ellipse((24 * s, 246 * s, 40 * s, 262 * s), fill=RED)
        d.text((50 * s, 241 * s), "202 pesakit keratoconus", font=font("Bold", 21 * s), fill=WHITE)
        d.ellipse((24 * s, 282 * s, 40 * s, 298 * s), fill=PURPLE_L)
        d.text((50 * s, 277 * s), "355 kawalan sihat", font=font("Bold", 21 * s), fill=WHITE)
    return ss_draw(w, h, fn)

def callout_all():
    def mk():
        w, h = 340, 250
        def fn(d, s):
            d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), 30 * s, fill=CARD, outline=CARD_LINE, width=2 * s)
            d.text((26 * s, 22 * s), "SEMUA CARA", font=font("ExtraBold", 24 * s), fill=TEAL)
            d.text((26 * s, 54 * s), "GOSOK MATA", font=font("Black", 40 * s), fill=WHITE)
            # anak panah naik
            ax, ay = 62 * s, 205 * s
            d.polygon([(ax, ay - 80 * s), (ax + 48 * s, ay - 28 * s), (ax + 20 * s, ay - 28 * s), (ax + 20 * s, ay),
                       (ax - 20 * s, ay), (ax - 20 * s, ay - 28 * s), (ax - 48 * s, ay - 28 * s)], fill=RED)
            d.text((130 * s, 140 * s), "RISIKO", font=font("Black", 38 * s), fill=RED)
            d.text((130 * s, 182 * s), "NAIK", font=font("Black", 38 * s), fill=WHITE)
        return ss_draw(w, h, fn)
    return cached("callout_all", mk)

def bars(t):
    """Carta tahap kaitan (ilustrasi kualitatif, BUKAN angka kajian)."""
    w, h = 940, 312
    rows = [("BUKU JARI", 1.0, RED, 10.1, 11.4),
            ("Pangkal ibu jari", 0.62, PURPLE_L, 9.5, 10.4),
            ("Hujung jari", 0.55, PURPLE_L, 9.3, 10.2)]
    def fn(d, s):
        d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), 30 * s, fill=CARD, outline=CARD_LINE, width=2 * s)
        d.text((32 * s, 22 * s), "KAITAN DENGAN KERATOCONUS", font=font("Black", 32 * s), fill=WHITE)
        d.text((32 * s, 64 * s), "mengikut cara gosok mata", font=font("Medium", 22 * s), fill=(210, 200, 250))
        y = 108
        for lab, v, col, a, b in rows:
            p = e_out((t - a) / (b - a))
            f = font("ExtraBold", 26 * s)
            d.text((32 * s, (y + 12) * s), lab, font=f, fill=WHITE if col == RED else (225, 218, 255))
            x0, x1 = 290, 906
            d.rounded_rectangle((x0 * s, y * s, x1 * s, (y + 54) * s), 27 * s, fill=(255, 255, 255, 34))
            ww = max(54, int((x1 - x0) * v * p))
            if p > 0.01:
                d.rounded_rectangle((x0 * s, y * s, (x0 + ww) * s, (y + 54) * s), 27 * s, fill=col)
            if col == RED and p > 0.9:
                d.text(((x1 - 22) * s, (y + 27) * s), "PALING TINGGI", font=font("Black", 25 * s), fill=WHITE, anchor="rm")
            y += 70
        d.text((32 * s, 292 * s - 0), "", font=font("Medium", 10 * s))
    im = ss_draw(w, h, fn)
    d = ImageDraw.Draw(im)
    d.text((w - 32, 30), "ilustrasi tahap, bukan angka kajian", font=font("Medium", 17), fill=(190, 180, 240), anchor="ra")
    return im

def cornea_card():
    def mk():
        w, h = 350, 300
        def fn(d, s):
            d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), 30 * s, fill=CARD, outline=CARD_LINE, width=2 * s)
            d.text((26 * s, 20 * s), "KERATOCONUS", font=font("Black", 32 * s), fill=WHITE)
            d.text((26 * s, 60 * s), "kornea berubah bentuk", font=font("Medium", 21 * s), fill=(210, 200, 250))
            for k, (cx, lab, cone, col) in enumerate(((95, "Normal", False, TEAL), (255, "Keratoconus", True, RED))):
                base = 215
                pts = []
                for i in range(41):
                    u = -1 + i / 20
                    if cone: y = (1 - abs(u) ** 1.25) * 62 + (1 - abs(u + 0.18)) * 0
                    else: y = (1 - u * u) * 42
                    if cone: y = 70 * math.exp(-((u - 0.25) ** 2) / 0.12) + 14 * (1 - u * u)
                    pts.append(((cx + u * 62) * s, (base - y) * s))
                d.polygon(pts + [((cx + 62) * s, (base + 14) * s), ((cx - 62) * s, (base + 14) * s)], fill=(255, 255, 255, 30))
                d.line(pts, fill=col, width=7 * s, joint="curve")
                lf = font("ExtraBold", 21 * s); tw = tsize(lab, lf)[0]
                d.text((cx * s - tw / 2, 244 * s), lab, font=lf, fill=col)
        return ss_draw(w, h, fn)
    return cached("cornea", mk)

def chip_list():
    items = ["Screen time berpanjangan", "Kerja waktu malam", "Mata kering", "Alahan mata", "Tidur meniarap / mengiring"]
    def mk():
        out = []
        for i, t in enumerate(items):
            w, h = 360, 64
            hl = i == 0
            im = rrect(w, h, 32, (YEL + (255,)) if hl else CARD, None if hl else CARD_LINE)
            f = fit_font("ExtraBold", t, 280, 24)
            ti = text_img(t, f, INK if hl else WHITE, 0, pad=0)
            dot = ss_draw(26, 26, lambda d, s: d.ellipse((0, 0, 26 * s - 1, 26 * s - 1), fill=(INK if hl else TEAL)))
            im.alpha_composite(dot, (18, 19)); im.alpha_composite(ti, (56, (h - ti.height) // 2))
            out.append(with_shadow(im, 8, 90, 5))
        return out
    return cached("chips", mk)

def card_quote():
    def mk():
        q = asset("quote2.png"); w = 880; h = int(q.height * w / q.width)
        card = rrect(940, h + 30, 28, (255, 255, 255, 255))
        ph = rounded_photo(q, w, h, 12)
        # penyerlah kuning pada "prolonged screen time"
        sc = w / q.width
        hl = Image.new("RGBA", (int(430 * sc), int(62 * sc)), YEL + (0,))
        base = ph.copy()
        ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).rounded_rectangle((int(350 * sc), int(138 * sc), int(778 * sc), int(200 * sc)), 8, fill=YEL + (120,))
        base = Image.alpha_composite(base, ov); base.putalpha(ph.getchannel("A"))
        card.alpha_composite(base, (30, 15))
        bar = rrect(8, h + 30 - 40, 4, RED); card.alpha_composite(bar, (6, 20))
        return with_shadow(card)
    return cached("quote", mk)

def card_product():
    def mk():
        box = asset("box.png"); h = 236; w = int(box.width * h / box.height)
        im = rounded_photo(box, w, h, 26)
        card = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
        card.alpha_composite(rrect(w + 16, h + 16, 32, (255, 255, 255, 255)), (0, 0))
        card.alpha_composite(im, (8, 8))
        return with_shadow(card)
    return cached("product", mk)

def card_product_text():
    def mk():
        w, h = 395, 240
        def fn(d, s):
            d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), 30 * s, fill=CARD, outline=CARD_LINE, width=2 * s)
            d.text((28 * s, 22 * s), "DS PHARMA", font=font("ExtraBold", 28 * s), fill=TEAL)
            d.text((26 * s, 56 * s), "EYE CARE", font=font("Black", 70 * s), fill=WHITE)
            d.text((28 * s, 142 * s), "Tablet kunyah · 650mg", font=font("Bold", 26 * s), fill=(225, 218, 255))
            d.text((28 * s, 180 * s), "10 tablet kunyah", font=font("Medium", 22 * s), fill=(190, 180, 240))
        return ss_draw(w, h, fn)
    return cached("product_text", mk)

def ingredient_tiles():
    def mk():
        out = []
        for img, l1, l2, mg in (("carrot.png", "Serbuk", "lobak merah", "60mg"), ("avo.png", "Ekstrak", "avokado", "15mg"),
                                ("goji.png", "Ekstrak", "goji", "50mg"), ("eyebright.png", "Ekstrak bunga", "Eyebright", "40mg")):
            w, h = 220, 268
            card = rrect(w, h, 28, (255, 255, 255, 255))
            card.alpha_composite(rounded_photo(asset(img), 196, 140, 20), (12, 12))
            d = ImageDraw.Draw(card)
            d.text((w // 2, 160), l1, font=font("Medium", 19), fill=(90, 70, 150), anchor="mt")
            d.text((w // 2, 180), l2, font=fit_font("Bold", l2, 196, 24), fill=INK, anchor="mt")
            pill = rrect(110, 36, 18, TEAL + (255,))
            card.alpha_composite(pill, (w // 2 - 55, 218))
            d.text((w // 2, 236), mg, font=font("Black", 26), fill=INK, anchor="mm")
            out.append(with_shadow(card, 10, 100, 6))
        return out
    return cached("ingr", mk)

def card_kkm():
    def mk():
        k = asset("kkm.png"); w = 470; h = int(k.height * w / k.width)
        card = rrect(w + 20, h + 20, 22, (255, 255, 255, 255))
        card.alpha_composite(rounded_photo(k, w, h, 14), (10, 10))
        return with_shadow(card)
    return cached("kkm", mk)

def card_mal():
    def mk():
        w, h = 430, 250
        def fn(d, s):
            d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), 30 * s, fill=CARD, outline=CARD_LINE, width=2 * s)
            d.text((26 * s, 22 * s), "NO. PENDAFTARAN", font=font("ExtraBold", 22 * s), fill=TEAL)
            f = fit_font("Black", "MAL22076147T", 380, 56)
            d.text((24 * s, 52 * s), "MAL22076147T", font=ImageFont.truetype(FD + "Inter-Black.otf", f.size * s), fill=WHITE)
            d.rounded_rectangle((26 * s, 140 * s, 404 * s, 214 * s), 37 * s, fill=TEAL)
            # tanda semak
            d.line([(52 * s, 177 * s), (66 * s, 192 * s), (92 * s, 160 * s)], fill=INK, width=8 * s, joint="curve")
            d.text((112 * s, 150 * s), "LULUS KKM", font=font("Black", 40 * s), fill=INK)
        return ss_draw(w, h, fn)
    return cached("mal", mk)

def cta_top():
    def mk():
        out = []
        for txt, col in (("TEKAN", WHITE), ("BEG KUNING", YEL)):
            out.append(text_img(txt, fit_font("Black", txt, 900, 122, 8), col, 8, PURPLE_D, 14))
        return out
    return cached("cta_top", mk)

def stock_badge():
    def mk():
        w, h = 340, 118
        def fn(d, s):
            d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), 30 * s, fill=RED, outline=(255, 255, 255, 230), width=3 * s)
            d.text((w * s / 2, 36 * s), "STOK TERHAD", font=font("Black", 42 * s), fill=WHITE, anchor="mm")
            d.text((w * s / 2, 84 * s), "untuk yang terawal saja", font=font("Bold", 24 * s), fill=WHITE, anchor="mm")
        return with_shadow(ss_draw(w, h, fn), 10, 110, 6)
    return cached("stock", mk)

def cart_icon(size=80, col=INK):
    def fn(d, s):
        k = s * size / 80
        d.line([(6 * k, 14 * k), (20 * k, 14 * k), (30 * k, 52 * k), (64 * k, 52 * k), (72 * k, 24 * k), (24 * k, 24 * k)],
               fill=col, width=int(7 * k), joint="curve")
        d.ellipse((28 * k, 60 * k, 42 * k, 74 * k), fill=col); d.ellipse((54 * k, 60 * k, 68 * k, 74 * k), fill=col)
    return ss_draw(size, size, fn)

def cta_pill(t):
    w, h = 520, 118
    pulse = 1 + 0.035 * math.sin(t * 7)
    im = rrect(w, h, 59, YEL + (255,))
    ic = cart_icon(70)
    im.alpha_composite(ic, (34, 24))
    d = ImageDraw.Draw(im)
    d.text((118, 22), "BEG KUNING", font=font("Black", 44), fill=INK)
    d.text((118, 70), "tekan sekarang", font=font("Bold", 26), fill=(92, 60, 0))
    sh, pad = with_shadow(im, 14, 130, 8)
    sh = sh.resize((int(sh.width * pulse), int(sh.height * pulse)), Image.LANCZOS)
    return sh, pad

def arrow_down(t):
    def fn(d, s):
        d.polygon([(40 * s, 96 * s), (4 * s, 52 * s), (28 * s, 52 * s), (28 * s, 4 * s), (52 * s, 4 * s), (52 * s, 52 * s), (76 * s, 52 * s)],
                  fill=YEL, outline=PURPLE_D)
    return ss_draw(80, 100, fn)

# ------------------------------------------------------------------ kapsyen
WORDS = None
def load_groups():
    ws = json.load(open(f"{WORK}/words2.json"))
    fix = {"Optometry,": "Optometry,"}
    groups, cur = [], []
    for w, s, e in ws:
        w = w.strip()
        if cur:
            gap = s - cur[-1][2]
            chars = sum(len(x[0]) + 1 for x in cur) + len(w)
            if cur[-1][0][-1] in ".,?!" or gap > 0.5 or chars > 27 or len(cur) >= 5:
                groups.append(cur); cur = []
        cur.append([w, s, e])
    if cur: groups.append(cur)
    # selaraskan masa tamat
    out = []
    for i, g in enumerate(groups):
        start = g[0][1]; end = g[-1][2] + 0.22
        if i + 1 < len(groups): end = min(end, groups[i + 1][0][1])
        out.append((start, end, g))
    return out

def caption_img(g, t):
    f = font("Black", 64)
    words = [w.upper().rstrip(".,") if w.endswith((".", ",")) else w.upper() for w, s, e in g]
    cur = 0
    for i, (w, s, e) in enumerate(g):
        if t >= s: cur = i
    gap = 16
    ws = [tsize(w, f, 9)[0] for w in words]
    total = sum(ws) + gap * (len(ws) - 1)
    # pecah dua baris jika lebar > 940
    lines = [list(range(len(words)))]
    if total > 940:
        mid = len(words) // 2; lines = [list(range(mid)), list(range(mid, len(words)))]
    lh = 88
    im = Image.new("RGBA", (1000, lh * len(lines) + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for li, idxs in enumerate(lines):
        lw = sum(ws[i] for i in idxs) + gap * (len(idxs) - 1)
        x = (1000 - lw) // 2
        for i in idxs:
            col = YEL if i == cur else WHITE
            d.text((x, 14 + li * lh), words[i], font=f, fill=col, stroke_width=9, stroke_fill=PURPLE_D)
            x += ws[i] + gap
    sh, pad = with_shadow(im, 8, 120, 5)
    return sh, pad

# ------------------------------------------------------------------ komposisi
GROUPS = None
TOTAL = 38.9
def build_layers(t):
    global GROUPS
    if GROUPS is None: GROUPS = load_groups()
    B = Image.new("RGBA", (W, CROP), (0, 0, 0, 0))
    F = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # --- lapisan B ---
    # cahaya ungu di bahagian atas (belakang orang)
    g = cached("glow", lambda: Image.fromarray(np.dstack([
        np.full((CROP, W), 60, np.uint8), np.full((CROP, W), 30, np.uint8), np.full((CROP, W), 150, np.uint8),
        (np.clip(1 - np.linspace(0, 1, CROP) / 0.78, 0, 1)[:, None] ** 1.4 * 120 * np.ones((1, W))).astype(np.uint8)]), "RGBA"))
    ga = clamp(t / 0.5) * clamp((TOTAL - 1.2 - t) / 0.6 + 0.0)
    paste(B, g, 0, 0, ga)

    # Scene 1: hook
    l1, l2 = card_hook()
    show(B, l1, (W - l1.width) // 2, 66, t, 0.1, 3.5, "up")
    show(B, l2, (W - l2.width) // 2, 196, t, 0.28, 3.5, "up")
    # Scene 2: artikel
    show(B, tag("SUMBER RUJUKAN"), 90, 52, t, 3.5, 9.4, "left")
    ar, p = card_article()
    show(B, ar, 70, 112, t, 3.7, 9.2, "up", pad=p)
    lg, p = card_logo()
    show(B, lg, 790, 34, t, 3.9, 9.2, "right", pad=p)
    if 4.4 <= t <= 9.2: show(B, donut(t), 24, 400, t, 4.6, 9.2, "left")
    show(B, callout_all(), 700, 420, t, 6.2, 9.2, "right")
    # Scene 3: carta
    if 9.2 <= t <= 15.4:
        show(B, bars(t), 70, 40, t, 9.2, 15.4, "up", din=0.5)
        show(B, cornea_card(), 700, 392, t, 12.3, 15.4, "right")
    # Scene 4: faktor lain
    show(B, tag("FAKTOR LAIN DALAM KAJIAN YANG SAMA", YEL), 90, 52, t, 15.3, 19.3, "left")
    q, p = card_quote()
    show(B, q, 70, 100, t, 15.5, 19.2, "up", pad=p)
    for i, (ci, pc) in enumerate(chip_list()):
        show(B, ci, 690, 400 + i * 78, t, 16.3 + i * 0.4, 19.4, "right", pad=pc)
    show(B, tag("REHATKAN MATA", TEAL, INK, 28), 40, 396, t, 16.45, 19.4, "left")
    # Scene 5: produk
    pr, p = card_product()
    show(B, pr, 62, 62, t, 19.4, 25.1, "up", pad=p)
    show(B, card_product_text(), 612, 70, t, 19.6, 25.1, "right")
    for i, (ti, pc) in enumerate(ingredient_tiles()):
        show(B, ti, 70 + i * 240, 36, t, 25.2 + i * 0.25, 28.7, "up", pad=pc)
    # Scene 6: MAL / KKM
    kk, p = card_kkm()
    show(B, kk, 70, 40, t, 28.8, 32.0, "up", pad=p)
    show(B, card_mal(), 580, 52, t, 29.1, 32.0, "right")
    # Scene 7: CTA
    c1, c2 = cta_top()
    show(B, c1, (W - c1.width) // 2, 40, t, 31.9, 37.3, "up")
    show(B, c2, (W - c2.width) // 2, 150, t, 32.15, 37.3, "up")
    sb, p = stock_badge()
    show(B, sb, 690, 420, t, 34.6, 37.3, "right", pad=p)

    # --- lapisan F ---
    # progress bar
    pw = int((W - 60) * clamp(t / TOTAL))
    F.alpha_composite(rrect(W - 60, 8, 4, (255, 255, 255, 70)), (30, 18))
    if pw > 8: F.alpha_composite(rrect(pw, 8, 4, TEAL + (255,)), (30, 18))
    # chip sumber
    show(F, cached("src", lambda: _src_chip()), 40, 1462, t, 3.6, TOTAL, "left")
    show(F, cached("disc", lambda: _disc()), 40, 1528, t, 19.4, TOTAL, "left")
    # kapsyen
    for s, e, gp in GROUPS:
        if s - 0.02 <= t <= e:
            im, pad = caption_img(gp, t)
            k = e_back((t - s) / 0.16); sc = 0.88 + 0.12 * k
            if sc != 1: im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
            paste(F, im, (W - im.width) // 2, 1300 - im.height // 2 + 20 - pad // 2)
            break
    # CTA bawah
    if 31.9 <= t <= 38.2:
        pi, pad = cta_pill(t)
        a = clamp((t - 31.9) / 0.3)
        # anak panah melambung menuding beg kuning di bawah
        bob = abs(math.sin(t * 6)) * 26
        ar = arrow_down(t)
        if t > 32.3:
            paste(F, ar, 120, 1565 + bob, clamp((t - 32.3) / 0.3) * clamp((38.2 - t) / 0.3))
    return B, F

def _src_chip():
    t1 = text_img("Sumber: Review of Optometry · Label produk", font("Bold", 24), WHITE, 0, pad=0)
    p = rrect(t1.width + 64, t1.height + 26, (t1.height + 26) // 2, (20, 8, 60, 215), (255, 255, 255, 70), 1)
    # ikon buku
    ic = ss_draw(24, 24, lambda d, s: (d.rectangle((2 * s, 3 * s, 22 * s, 21 * s), outline=TEAL, width=3 * s),
                                       d.line([(12 * s, 3 * s), (12 * s, 21 * s)], fill=TEAL, width=2 * s)))
    p.alpha_composite(ic, (18, (p.height - 24) // 2)); p.alpha_composite(t1, (52, 13)); return p

def _disc():
    t1 = text_img("MAL22076147T · Ubat tradisional · Sila rujuk ahli farmasi / doktor sebelum mengambil produk ini.",
                  font("Medium", 18), (235, 230, 255), 0, pad=0)
    p = rrect(t1.width + 36, t1.height + 16, (t1.height + 16) // 2, (20, 8, 60, 190))
    p.alpha_composite(t1, (18, 8)); return p

# ------------------------------------------------------------------ pipeline
_seg = None
def segmenter():
    global _seg
    if _seg is None:
        import mediapipe as mp
        from mediapipe.tasks import python as mpp
        from mediapipe.tasks.python import vision
        opt = vision.ImageSegmenterOptions(base_options=mpp.BaseOptions(model_asset_path=WORK + "/dl/multi.tflite"),
                                           output_confidence_masks=True)
        _seg = vision.ImageSegmenter.create_from_options(opt)
    return _seg

def person_mask(bgr):
    import mediapipe as mp
    rgb = np.ascontiguousarray(bgr[:CROP, :, ::-1])
    res = segmenter().segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
    m = np.clip(1 - res.confidence_masks[0].numpy_view(), 0, 1)
    m = cv2.resize(m, (W, CROP), interpolation=cv2.INTER_CUBIC)
    g = cv2.cvtColor(bgr[:CROP], cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    r, eps = 10, 2e-3
    bf = lambda x: cv2.boxFilter(x, -1, (2 * r + 1, 2 * r + 1))
    mI, mP = bf(g), bf(m); a = (bf(g * m) - mI * mP) / (bf(g * g) - mI * mI + eps); b = mP - a * mI
    m = np.clip(bf(a) * g + bf(b), 0, 1)
    m = np.clip((m - 0.12) / 0.76, 0, 1); m = m * m * (3 - 2 * m)
    return m

def compose(i, bgr, mask=None):
    t = (i - 1) / FPS
    B, F = build_layers(t)
    if mask is None: mask = person_mask(bgr)
    base = Image.fromarray(bgr[:, :, ::-1], "RGB").convert("RGBA")
    top = base.crop((0, 0, W, CROP))
    top.alpha_composite(B)
    mk = Image.fromarray((mask * 255).astype(np.uint8), "L")
    orig_top = base.crop((0, 0, W, CROP))
    top = Image.composite(orig_top, top, mk)
    base.paste(top, (0, 0))
    base.alpha_composite(F)
    return base.convert("RGB")

def main():
    mode = sys.argv[1]
    if mode == "preview":
        for n in map(int, sys.argv[2:]):
            bgr = cv2.imread(f"{WORK}/fr30/{n:04d}.png")
            compose(n, bgr).save(f"{WORK}/prev_{n:04d}.png")
            print("ok", n)
    else:
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "12", "-preset", "veryfast",
                              "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for n in range(a, b + 1):
            bgr = cv2.imread(f"{WORK}/fr30/{n:04d}.png")
            p.stdin.write(np.asarray(compose(n, bgr)).tobytes())
        p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
