#!/usr/bin/env python3
"""Video awareness 'Sakit kepala anak & mata' — flip, overlay grafik DI BELAKANG orang (matte),
subtitle karaoke, semua dalam satu pass.
Guna:  python3 scripts/build_awareness.py render     -> work/render_noaudio.mp4
       python3 scripts/build_awareness.py stills 1 6 12  -> work/still_*.jpg (semak visual)
"""
import sys, json, math, subprocess, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from matte import get_matte

W, H, FPS = 1080, 1920, 30
SRC = 'work/edit.mov'   # hasil potongan outro (scripts/ lihat nota projek)
FD = '/usr/share/fonts/opentype/inter/'
def F(name, size): return ImageFont.truetype(FD + f'Inter-{name}.otf', size)

PURPLE = (62, 30, 120); PURPLE2 = (96, 56, 170); TEAL = (46, 214, 185); YEL = (255, 216, 77)
WHITE = (255, 255, 255); RED = (255, 99, 99); GREEN = (72, 222, 128); DARK = (28, 16, 60)

# ───────────────────────── util ─────────────────────────
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease_out(p): return 1 - (1 - p) ** 3
def ease_io(p): return p * p * (3 - 2 * p)
def seg_p(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)

def ss_canvas(w, h, S=4): return Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0)), S

def rrect_img(w, h, r, fill, outline=None, ow=0, shadow=0, grad=None):
    pad = 36 if shadow else 0
    S = 3
    img = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 10, pad + w, pad + h + 10), r, fill=(0, 0, 0, 120))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14)))
    big = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    if grad:
        g = Image.new('RGBA', (w * S, h * S))
        gd = ImageDraw.Draw(g)
        for y in range(h * S):
            k = y / (h * S)
            gd.line((0, y, w * S, y), fill=tuple(int(grad[0][i] * (1 - k) + grad[1][i] * k) for i in range(3)) + (fill[3] if len(fill) > 3 else 255,))
        m = Image.new('L', big.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w * S - 1, h * S - 1), r * S, fill=255)
        big.paste(g, (0, 0), m)
    else:
        d.rounded_rectangle((0, 0, w * S - 1, h * S - 1), r * S, fill=fill)
    if outline: d.rounded_rectangle((0, 0, w * S - 1, h * S - 1), r * S, outline=outline, width=ow * S)
    img.alpha_composite(big.resize((w, h), Image.LANCZOS), (pad, pad))
    return img, pad

def text_w(font, s): return font.getlength(s)

def fit_font(name, s, maxw, size, minsize=28):
    while size > minsize and F(name, size).getlength(s) > maxw: size -= 2
    return F(name, size)

# ───────────────────────── ikon ─────────────────────────
def icon(name, s, fg=WHITE, bg=None):
    S = 4; im = Image.new('RGBA', (s * S, s * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); n = s * S
    if bg: d.ellipse((0, 0, n - 1, n - 1), fill=bg)
    c = n / 2; u = n * (0.52 if bg else 0.9) / 2   # separuh saiz glyph
    lw = int(n * 0.07)
    if name == 'eye':
        pts = []
        for i in range(41):
            x = -1 + i / 20; pts.append((c + x * u, c - (1 - x * x) * 0.55 * u))
        for i in range(41):
            x = 1 - i / 20; pts.append((c + x * u, c + (1 - x * x) * 0.55 * u))
        d.polygon(pts, outline=fg, width=lw)
        d.ellipse((c - .38 * u, c - .38 * u, c + .38 * u, c + .38 * u), fill=fg)
        d.ellipse((c - .14 * u, c - .14 * u, c + .14 * u, c + .14 * u), fill=bg or (0, 0, 0, 255))
    elif name == 'glasses':
        r = .42 * u
        for cx in (c - .55 * u, c + .55 * u): d.ellipse((cx - r, c - r, cx + r, c + r), outline=fg, width=lw)
        d.line((c - .13 * u, c - .1 * u, c + .13 * u, c - .1 * u), fill=fg, width=lw)
    elif name == 'drop':
        r = .55 * u; cy = c + .25 * u
        d.polygon([(c, c - .95 * u), (c - r * .95, cy - .1 * u), (c + r * .95, cy - .1 * u)], fill=fg)
        d.ellipse((c - r, cy - r, c + r, cy + r), fill=fg)
    elif name == 'bolt':
        p = [(.15, -1), (-.55, .1), (-.05, .1), (-.25, 1), (.6, -.2), (.08, -.2), (.4, -1)]
        d.polygon([(c + x * u, c + y * u) for x, y in p], fill=fg)
    elif name == 'moon':
        d.ellipse((c - .8 * u, c - .8 * u, c + .8 * u, c + .8 * u), fill=fg)
        cut = Image.new('L', im.size, 0); ImageDraw.Draw(cut).ellipse((c - .35 * u, c - .95 * u, c + 1.05 * u, c + .65 * u), fill=255)
        im.paste((0, 0, 0, 0), (0, 0), cut)
        d = ImageDraw.Draw(im)
    elif name == 'check':
        d.line([(c - .7 * u, c + .0 * u), (c - .2 * u, c + .55 * u), (c + .75 * u, c - .55 * u)], fill=fg, width=int(lw * 1.6), joint='curve')
    elif name == 'search':
        r = .55 * u
        d.ellipse((c - .75 * u, c - .75 * u, c - .75 * u + 2 * r, c - .75 * u + 2 * r), outline=fg, width=lw)
        d.line((c + .3 * u, c + .3 * u, c + .85 * u, c + .85 * u), fill=fg, width=int(lw * 1.4))
    elif name == 'book':
        d.rounded_rectangle((c - .85 * u, c - .6 * u, c - .05 * u, c + .65 * u), 6, outline=fg, width=lw)
        d.rounded_rectangle((c + .05 * u, c - .6 * u, c + .85 * u, c + .65 * u), 6, outline=fg, width=lw)
    elif name == 'phone':
        d.rounded_rectangle((c - .5 * u, c - .9 * u, c + .5 * u, c + .9 * u), int(.18 * u), outline=fg, width=lw)
        d.ellipse((c - .07 * u, c + .6 * u, c + .07 * u, c + .74 * u), fill=fg)
    elif name == 'clock':
        d.ellipse((c - .85 * u, c - .85 * u, c + .85 * u, c + .85 * u), outline=fg, width=lw)
        d.line((c, c, c, c - .5 * u), fill=fg, width=lw); d.line((c, c, c + .4 * u, c + .2 * u), fill=fg, width=lw)
    elif name == 'alert':
        d.polygon([(c, c - .9 * u), (c - .95 * u, c + .75 * u), (c + .95 * u, c + .75 * u)], outline=fg, width=lw)
        d.line((c, c - .3 * u, c, c + .25 * u), fill=fg, width=lw); d.ellipse((c - .07 * u, c + .4 * u, c + .07 * u, c + .54 * u), fill=fg)
    elif name == 'pill':
        d.rounded_rectangle((c - .85 * u, c - .4 * u, c + .85 * u, c + .4 * u), int(.4 * u), outline=fg, width=lw)
        d.line((c, c - .4 * u, c, c + .4 * u), fill=fg, width=lw)
    elif name == 'tired':   # mata mengantuk
        d.arc((c - .8 * u, c - .5 * u, c + .8 * u, c + .7 * u), 20, 160, fill=fg, width=lw)
        d.line((c - .7 * u, c - .35 * u, c + .7 * u, c - .35 * u), fill=fg, width=lw)
    return im.resize((s, s), Image.LANCZOS)

def photo_circle(path, d, crop=None, ring=WHITE, rw=6):
    im = Image.open(path).convert('RGB')
    if crop: im = im.crop(crop)
    w, h = im.size; m = min(w, h)
    im = im.crop(((w - m) // 2, (h - m) // 2, (w + m) // 2, (h + m) // 2)).resize((d * 3, d * 3), Image.LANCZOS)
    out = Image.new('RGBA', (d * 3, d * 3), (0, 0, 0, 0))
    mask = Image.new('L', out.size, 0); ImageDraw.Draw(mask).ellipse((0, 0, d * 3 - 1, d * 3 - 1), fill=255)
    out.paste(im, (0, 0), mask)
    ImageDraw.Draw(out).ellipse((rw, rw, d * 3 - 1 - rw, d * 3 - 1 - rw), outline=ring + (255,), width=rw * 2)
    return out.resize((d, d), Image.LANCZOS)

# ───────────────────────── elemen ─────────────────────────
class El:
    """Elemen statik (RGBA dirender sekali). anim: slide_down/slide_up/slide_l/slide_r/pop/fade"""
    top = False
    def __init__(self, img, x, y, t0, t1, anim='pop', dur=.35, tag=''):
        self.img, self.x, self.y, self.t0, self.t1, self.anim, self.dur, self.tag = img, x, y, t0, t1, anim, dur, tag
        self.arr = np.asarray(img).astype(np.float32)
        self._cache = {}
    def at(self, t):
        if t < self.t0 or t > self.t1: return None
        pin = ease_out(seg_p(t, self.t0, self.t0 + self.dur)); pout = ease_io(seg_p(t, self.t1 - .22, self.t1))
        a = pin * (1 - pout)
        if a <= 0.001: return None
        dx = dy = 0; sc = 1.0; vis = 1 - (1 - pin) * 0
        if self.anim == 'slide_down': dy = -60 * (1 - pin)
        elif self.anim == 'slide_up': dy = 60 * (1 - pin)
        elif self.anim == 'slide_l': dx = -120 * (1 - pin)
        elif self.anim == 'slide_r': dx = 120 * (1 - pin)
        elif self.anim == 'pop': sc = 0.82 + 0.18 * pin + 0.05 * math.sin(pin * math.pi)
        img = self.arr
        if abs(sc - 1) > 1e-3:
            k = round(sc, 2)
            if k not in self._cache:
                w, h = self.img.size
                self._cache[k] = np.asarray(self.img.resize((max(1, int(w * k)), max(1, int(h * k))), Image.BILINEAR)).astype(np.float32)
            img = self._cache[k]
            ox = self.x + (self.arr.shape[1] - img.shape[1]) / 2; oy = self.y + (self.arr.shape[0] - img.shape[0]) / 2
        else: ox, oy = self.x, self.y
        return img, int(ox + dx), int(oy + dy), a

class Dyn:
    top = False
    """Elemen dinamik: fn(t) -> RGBA PIL image, dirender per frame"""
    def __init__(self, fn, x, y, t0, t1, anim='fade', dur=.3):
        self.fn, self.x, self.y, self.t0, self.t1, self.anim, self.dur = fn, x, y, t0, t1, anim, dur
    def at(self, t):
        if t < self.t0 or t > self.t1: return None
        pin = ease_out(seg_p(t, self.t0, self.t0 + self.dur)); pout = ease_io(seg_p(t, self.t1 - .22, self.t1))
        a = pin * (1 - pout)
        if a <= 0.001: return None
        dx = 0; dy = 0
        if self.anim == 'slide_l': dx = -120 * (1 - pin)
        elif self.anim == 'slide_r': dx = 120 * (1 - pin)
        elif self.anim == 'slide_up': dy = 60 * (1 - pin)
        return np.asarray(self.fn(t)).astype(np.float32), int(self.x + dx), int(self.y + dy), a

# ───────────────────────── banner ─────────────────────────
BX, BY, BW, BH = 40, 96, 1000, 232
def banner(label, head, sub, ic, t0, t1, sub_t=None, icon_bg=TEAL, sub2=None, sub2_t=None):
    """Panel atas. sub boleh muncul lewat (sub_t)."""
    def make(with_sub):
        img, pad = rrect_img(BW, BH, 34, (0, 0, 0, 242), shadow=1, grad=(PURPLE2, PURPLE))
        d = ImageDraw.Draw(img)
        # aksen teal kiri
        d.rounded_rectangle((pad, pad + 26, pad + 10, pad + BH - 26), 5, fill=TEAL)
        img.alpha_composite(icon(ic, 120, fg=DARK, bg=icon_bg), (pad + 38, pad + (BH - 120) // 2))
        tx = pad + 190; mw = BW - 190 - 36
        d.text((tx, pad + 26), label.upper(), font=F('Bold', 26), fill=TEAL)
        hf = fit_font('ExtraBold', head, mw, 60, 38)
        d.text((tx, pad + 62), head, font=hf, fill=WHITE)
        if with_sub and sub:
            sf = fit_font('Medium', sub, mw, 38, 26)
            d.text((tx, pad + 148), sub, font=sf, fill=(226, 218, 250))
        return img, pad
    base, pad = make(sub_t is None); els = [El(base, BX - pad, BY - pad, t0, t1, 'slide_down')]
    if sub_t is not None:
        base0, _ = make(False); els = [El(base0, BX - pad, BY - pad, t0, t1, 'slide_down')]
        full, _ = make(True)
        # lapisan sub sahaja (potong kawasan sub)
        sub_only = Image.new('RGBA', full.size, (0, 0, 0, 0))
        reg = full.crop((pad + 180, pad + 140, pad + BW - 20, pad + BH - 10)); sub_only.paste(reg, (pad + 180, pad + 140))
        els.append(El(sub_only, BX - pad, BY - pad, sub_t, t1, 'slide_up', .3))
    return els

# ───────────────────────── chip / kad kecil ─────────────────────────
def chip(text, ic, w, color=TEAL, t0=0, t1=0, x=0, y=0, anim='pop', h=104):
    img, pad = rrect_img(w, h, h // 2, (255, 255, 255, 250), shadow=1)
    d = ImageDraw.Draw(img)
    img.alpha_composite(icon(ic, h - 28, fg=DARK, bg=color), (pad + 14, pad + 14))
    f = fit_font('ExtraBold', text, w - h - 18, 36, 22)
    d.text((pad + h + 2, pad + h / 2), text, font=f, fill=DARK, anchor='lm')
    return El(img, x - pad, y - pad, t0, t1, anim)

# ───────────────────────── kad artikel (screenshot sumber) ─────────────────────────
def article_card(t0, t1, x, y, rot=-4):
    n1 = Image.open('work/img/news1.png').convert('RGB').crop((40, 1250, 1170, 1650))
    n2 = Image.open('work/img/news2.png').convert('RGB').crop((40, 1685, 1170, 2260))
    n2o = n2.convert('RGBA'); hl = Image.new('RGBA', n2o.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).rounded_rectangle((0, 295, n2o.width, 505), 14, fill=(255, 214, 0, 105))
    n2 = Image.alpha_composite(n2o, hl).convert('RGB')
    cw = 480; sc = (cw - 40) / n1.width
    a = n1.resize((cw - 40, int(n1.height * sc)), Image.LANCZOS); b = n2.resize((cw - 40, int(n2.height * sc)), Image.LANCZOS)
    hh = 62; ch = hh + a.height + b.height + 40
    card, pad = rrect_img(cw, ch, 24, (255, 255, 255, 255), shadow=1)
    d = ImageDraw.Draw(card)
    hdr = Image.new('RGBA', (cw, hh), (0, 0, 0, 0)); hd = ImageDraw.Draw(hdr)
    hd.rounded_rectangle((0, 0, cw, hh + 30), 24, fill=PURPLE)
    hd.text((22, hh // 2 - 2), 'SUMBER', font=F('ExtraBold', 20), fill=TEAL, anchor='lm')
    hd.text((120, hh // 2 - 2), 'Khaleej Times · 10 Jul 2026', font=F('Bold', 22), fill=WHITE, anchor='lm')
    card.alpha_composite(hdr.crop((0, 0, cw, hh)), (pad, pad))
    card.paste(a, (pad + 20, pad + hh + 10)); card.paste(b, (pad + 20, pad + hh + 20 + a.height))
    card = card.rotate(rot, resample=Image.BICUBIC, expand=True)
    return El(card, x, y, t0, t1, 'slide_l', .45)

# ───────────────────────── kad blur vs jelas ─────────────────────────
def blur_card(t0, t1, x, y):
    w, h = 300, 250
    img, pad = rrect_img(w, h, 26, (255, 255, 255, 250), shadow=1)
    d = ImageDraw.Draw(img)
    def letters(blur):
        l = Image.new('RGBA', (120, 110), (0, 0, 0, 0)); ld = ImageDraw.Draw(l)
        ld.text((60, 55), 'E', font=F('Black', 96), fill=DARK, anchor='mm')
        return l.filter(ImageFilter.GaussianBlur(blur)) if blur else l
    img.alpha_composite(letters(0), (pad + 20, pad + 38)); img.alpha_composite(letters(7), (pad + 160, pad + 38))
    d.text((pad + 80, pad + 168), 'Jelas', font=F('Bold', 28), fill=(40, 150, 90), anchor='mm')
    d.text((pad + 220, pad + 168), 'Kabur', font=F('Bold', 28), fill=(200, 60, 60), anchor='mm')
    d.text((pad + w / 2, pad + 218), 'Anak mungkin tak perasan', font=F('SemiBold', 22), fill=PURPLE, anchor='mm')
    return El(img, x - pad, y - pad, t0, t1, 'slide_r', .4)

# ───────────────────────── gauge usaha mata ─────────────────────────
def effort_card(t0, t1, x, y, fill_a, fill_b):
    w, h = 290, 250
    def fn(t):
        img, pad = rrect_img(w, h, 26, (255, 255, 255, 250), shadow=1)
        d = ImageDraw.Draw(img)
        d.text((pad + 24, pad + 36), 'USAHA MATA', font=F('ExtraBold', 28), fill=PURPLE, anchor='lm')
        p = ease_io(seg_p(t, fill_a, fill_b))
        bx0, by0, bx1, by1 = pad + 24, pad + 74, pad + w - 24, pad + 112
        d.rounded_rectangle((bx0, by0, bx1, by1), 19, fill=(226, 222, 240))
        ww = int((bx1 - bx0) * (0.12 + 0.88 * p))
        col = tuple(int(TEAL[i] * (1 - p) + RED[i] * p) for i in range(3))
        d.rounded_rectangle((bx0, by0, bx0 + ww, by1), 19, fill=col)
        d.text((pad + 24, pad + 140), 'Mata penat' if p > .55 else 'Biasa', font=F('Bold', 30), fill=(200, 60, 60) if p > .55 else (40, 150, 90), anchor='lm')
        # chip baca / gajet
        for i, (nm, ic, ta) in enumerate((('Baca', 'book', 12.36), ('Gajet', 'phone', 13.3))):
            on = t >= ta
            cx = pad + 20 + i * 126
            d.rounded_rectangle((cx, pad + 172, cx + 118, pad + 226), 27, fill=(PURPLE if on else (226, 222, 240)))
            img.alpha_composite(icon(ic, 32, fg=WHITE if on else (150, 140, 180)), (cx + 14, pad + 183))
            d.text((cx + 50, pad + 199), nm, font=F('Bold', 22), fill=WHITE if on else (150, 140, 180), anchor='lm')
        return img
    return Dyn(lambda t: fn(t), x - 36, y - 36, t0, t1, 'slide_r', .4)

# ───────────────────────── carta bar ─────────────────────────
def bar_chart_el(side, t0, t1, x, base_y, maxh, val, label, anim_a, anim_b, color):
    w = 270
    def fn(t):
        pad = 20; hh = maxh + 150
        img = Image.new('RGBA', (w + 2 * pad, hh + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
        p = ease_out(seg_p(t, anim_a, anim_b))
        bh = int(maxh * (val / 34.4) * p)
        by1 = pad + hh - 90; by0 = by1 - bh
        sh = Image.new('RGBA', img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((pad + 30, by0 + 10, pad + w - 30, by1 + 10), 20, fill=(0, 0, 0, 110))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((pad + 30, by0, pad + w - 30, by1), 22, fill=color)
        d.rounded_rectangle((pad + 30, by0, pad + w - 30, min(by0 + 26, by1)), 22, fill=tuple(min(255, c + 40) for c in color))
        # angka
        shown = val * p
        s = f'{shown:.1f}%'
        f = F('Black', 74)
        tw = f.getlength(s); ty = by0 - 62
        pill = rrect_img(int(tw + 36), 92, 26, (255, 255, 255, 250))[0]
        img.alpha_composite(pill, (int(pad + w / 2 - tw / 2 - 18), ty - 14))
        d.text((pad + w / 2, ty + 32), s, font=f, fill=PURPLE, anchor='mm')
        # label dasar
        lb = rrect_img(w - 20, 80, 24, (255, 255, 255, 250), shadow=0)[0]
        img.alpha_composite(lb, (pad + 10, by1 + 12))
        d.text((pad + w / 2, by1 + 52), label, font=F('ExtraBold', 34), fill=DARK, anchor='mm')
        return img
    hh = maxh + 150
    return Dyn(fn, x - 20, base_y - hh - 20 + 90 + 0, t0, t1, 'slide_up', .35)

# ───────────────────────── produk & bahan ─────────────────────────
def product_card(t0, t1, x, y):
    box = Image.open('work/img/box_front.jpg').convert('RGB').crop((200, 740, 1180, 1300))
    cw = 360; bw = cw - 30; bh = int(box.height * bw / box.width)
    ch = bh + 128
    img, pad = rrect_img(cw, ch, 26, (255, 255, 255, 252), shadow=1)
    d = ImageDraw.Draw(img)
    m = Image.new('L', (bw, bh), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, bw - 1, bh - 1), 16, fill=255)
    img.paste(box.resize((bw, bh), Image.LANCZOS), (pad + 15, pad + 15), m)
    d.text((pad + cw / 2, pad + bh + 46), 'DS PHARMA Eye Care', font=fit_font('ExtraBold', 'DS PHARMA Eye Care', cw - 30, 32, 22), fill=PURPLE, anchor='mm')
    d.text((pad + cw / 2, pad + bh + 86), 'Traditionally used for healthy eyes', font=F('Medium', 21), fill=(90, 80, 130), anchor='mm')
    img = img.rotate(3, resample=Image.BICUBIC, expand=True)
    return El(img, x - 20, y - 20, t0, t1, 'slide_l', .45)

ING = [('carrot.webp', 'Karot', '60mg', None), ('avocado.webp', 'Avokado', '15mg', None),
       ('goji.webp', 'Goji', '50mg', None), ('eyebright.jpg', 'Euphrasia', '40mg', None)]
def ingredient_els(t0s, t1, x0, y0):
    els = []; d_ = 138
    for i, (f, nm, mg, _) in enumerate(ING):
        cx = x0 + (i % 2) * 160; cy = y0 + (i // 2) * 205
        ph = photo_circle('work/img/' + f, d_, ring=TEAL, rw=5)
        card = Image.new('RGBA', (150, 200), (0, 0, 0, 0))
        sh = Image.new('RGBA', card.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse((8, 14, 142, 148), fill=(0, 0, 0, 120))
        card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
        card.alpha_composite(ph, (6, 4))
        dd = ImageDraw.Draw(card)
        dd.rounded_rectangle((0, 148, 150, 198), 18, fill=(255, 255, 255, 250))
        dd.text((75, 165), nm, font=fit_font('ExtraBold', nm, 136, 26, 18), fill=DARK, anchor='mm')
        dd.text((75, 187), mg, font=F('Bold', 20), fill=PURPLE2, anchor='mm')
        els.append(El(card, cx, cy, t0s[i], t1, 'pop', .4))
    return els

def tiktok_card(t0, t1, x, y):
    im = Image.open('work/img/tiktok.png').convert('RGB').crop((0, 321, 1206, 1521))
    w = 330; h = int(im.height * w / im.width)
    cw, ch = w + 24, h + 24 + 76
    img, pad = rrect_img(cw, ch, 28, (255, 255, 255, 252), shadow=1)
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 20, fill=255)
    img.paste(im.resize((w, h), Image.LANCZOS), (pad + 12, pad + 12), m)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((pad + 12, pad + h + 18, pad + cw - 12, pad + ch - 10), 22, fill=(254, 44, 85))
    d.text((pad + cw / 2, pad + h + 18 + 25), 'TikTok Shop · DS Pharma', font=F('ExtraBold', 24), fill=WHITE, anchor='mm')
    img = img.rotate(-3, resample=Image.BICUBIC, expand=True)
    return El(img, x - 20, y - 20, t0, t1, 'slide_r', .45)

def disclaimer(t0, t1):
    s = 'Ubat tradisional. Sila rujuk pakar farmasi / doktor sebelum mengambil produk ini.'
    f = F('SemiBold', 25); w = int(f.getlength(s)) + 44
    img, pad = rrect_img(w, 54, 27, (20, 10, 50, 215), shadow=0)
    ImageDraw.Draw(img).text((22, 27), s, font=f, fill=(235, 230, 255), anchor='lm')
    e = El(img, (W - w) // 2, 1610, t0, t1, 'fade', .4); e.top = True
    return e

# ───────────────────────── skrip / token masa ─────────────────────────
def load_tokens():
    w = json.load(open('work/words.json'))                     # small (0-46.3 digunakan)
    small = [x for x in w if x[0] < 46.3]
    # medium (>=46.56) — nilai dari transkrip kedua (dibuat manual dari output)
    med = [(46.56, 47.08, 'bawa'), (47.08, 47.36, 'buat'), (47.36, 48.26, 'pemeriksaan'), (48.26, 48.66, 'mata'),
           (48.66, 49.42, 'atau'), (49.42, 49.68, 'boleh'), (49.68, 50.26, 'dapatkan'), (50.26, 50.66, 'suplemen'),
           (50.66, 51.14, 'untuk'), (51.14, 51.76, 'penjagaan'), (51.76, 52.22, 'kesihatan'), (52.22, 52.54, 'mata'),
           (52.54, 52.88, 'dengan'), (52.88, 53.38, 'segera.'), (53.38, 53.65, 'okey.'),
           (53.93, 54.31, 'Jangan'), (54.31, 54.57, 'tunggu'), (54.57, 54.85, 'lagi.'),
           (55.21, 55.95, 'Dapatkan'), (55.95, 56.37, 'rawatan'), (56.50, 56.85, 'sekarang.'),
           (57.25, 57.5, 'Bye'), (57.95, 58.3, 'bye.')]
    return small + med

# [teks ikut audio; ejaan dibetulkan]. Setiap baris = satu paparan subtitle; bilangan perkataan mesti sama dgn token.
CHUNKS = [
    ('Anak kerap sakit kepala?', 4), ('Mata pun boleh jadi', 4), ('salah satu sebab.', 3),
    ('Kalau anak rabun atau', 4), ('ada masalah penglihatan', 3), ('yang belum dibetulkan,', 3),
    ('mata kena kerja lebih kuat,', 5), ('terutamanya lepas baca', 3), ('atau main gajet.', 3),
    ('Itu boleh buat mata penat', 5), ('dan sakit kepala.', 3),
    ('Tapi jangan panik.', 3), ('Sakit kepala budak', 3), ('biasanya bukan serius.', 3),
    ('Punca lain termasuk', 3), ('kurang minum air,', 3), ('stres dan kurang tidur.', 4),
    ('Fakta di Malaysia:', 3), ('rabun jauh kanak-kanak', 4), ('dianggarkan 9.8%', 4), ('pada umur 7 tahun.', 4),
    ('Naik kepada 34.4%', 4), ('pada umur 15 tahun.', 4),
    ('Anak pun sering tak sedar', 5), ('penglihatan dia bermasalah.', 3),
    ('Jadi kalau sakit kepala berulang,', 5), ('bawa buat pemeriksaan mata,', 4),
    ('atau boleh dapatkan suplemen', 5), ('untuk penjagaan kesihatan mata', 4), ('dengan segera.', 2), ('okey.', 1),
    ('Jangan tunggu lagi.', 3), ('Dapatkan rawatan sekarang.', 3), ('Bye bye.', 2),
]
# Betulkan token whisper → perkataan sebenar sebelum dipadan (indeks mengikut senarai selepas digabung)
def build_tokens():
    tk = load_tokens(); out = []; i = 0
    words = [list(x) for x in tk]
    # normalisasi + gabung
    merged = []
    i = 0
    while i < len(words):
        s, e, t = words[i]
        if t.lower() == 'jauhkan': merged.append([s, e, 'jauh']); i += 1; continue
        if t.lower() == 'nak' and i + 1 < len(words) and words[i + 1][2].lower() == 'kanak':
            merged.append([s, words[i + 1][1], 'kanak-kanak']); i += 2; continue
        if t == '9' and i + 2 < len(words): merged.append([s, words[i + 2][1], '9.8%']); i += 3; continue
        if t == '34' and i + 2 < len(words): merged.append([s, words[i + 2][1], '34.4%']); i += 3; continue
        if t == '7': merged.append([s, e, '7']); i += 1; continue
        merged.append([s, e, t]); i += 1
    return merged

def make_caps():
    tk = build_tokens()
    # buang "dia"+"bermasalah" kekal; kira bilangan token vs chunk
    n_needed = sum(n for _, n in CHUNKS)
    # kes khas: 'kerab' 1 token, 'ataupun' 'atau' dsb — ikut kiraan
    caps = []; k = 0
    for text, n in CHUNKS:
        ws = text.split()
        n = len(ws); toks = tk[k:k + n]; k += n
        # peta perkataan paparan → token masa (bilangan sama)
        if len(ws) != len(toks): raise SystemExit(f'Chunk "{text}" {len(ws)} perkataan tapi {len(toks)} token: {[t[2] for t in toks]}')
        caps.append([(w, t[0], t[1]) for w, t in zip(ws, toks)])
    return caps, tk, n_needed

# ───────────────────────── subtitle ─────────────────────────
SUBF = F('ExtraBold', 66)
def render_caption(words, t, hold_end):
    maxw = 940; lines = [[]]; cw = 0
    sp = SUBF.getlength(' ')
    for i, (w, a, b) in enumerate(words):
        ww = SUBF.getlength(w)
        if cw + ww > maxw and lines[-1]: lines.append([]); cw = 0
        lines[-1].append((i, w, ww)); cw += ww + sp
    lh = 86; Hh = lh * len(lines) + 40
    img = Image.new('RGBA', (W, Hh), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    y = 20 + lh / 2
    for ln in lines:
        tw = sum(x[2] for x in ln) + sp * (len(ln) - 1); x = (W - tw) / 2
        for i, w, ww in ln:
            a, b = words[i][1], words[i][2]
            active = a - 0.02 <= t <= b + 0.02
            done = t > b + 0.02
            col = YEL if active else WHITE
            d.text((x, y), w, font=SUBF, fill=col, anchor='lm', stroke_width=9, stroke_fill=(24, 12, 52, 255))
            x += ww + sp
        y += lh
    return img, Hh

CAPS, TOKENS, _ = make_caps()
CAP_Y = 1380

# ───────────────────────── susunan scene ─────────────────────────
def build_scene():
    E = []
    # 1 — tajuk
    E += banner('Awareness kesihatan mata', 'Anak kerap sakit kepala?', 'Mata pun boleh jadi sebab', 'eye', 0.0, 4.55, sub_t=1.92)
    # 2 — rabun
    E += banner('Punca tersembunyi', 'Rabun / masalah penglihatan', 'yang belum dibetulkan', 'glasses', 4.55, 8.45)
    # 3 — mata kerja lebih kuat
    E += banner('Kesan pada mata', 'Mata kena kerja lebih kuat', 'Terutamanya lepas baca atau main gajet', 'eye', 8.45, 14.5)
    E.append(article_card(9.2, 20.0, -20, 400))
    E.append(effort_card(9.4, 15.3, 765, 420, 9.6, 13.6))
    # 4 — akibat
    E += banner('Akibatnya', 'Mata penat & sakit kepala', None, 'tired', 14.5, 18.3)
    E.append(chip('Mata penat', 'eye', 300, TEAL, 15.44, 18.3, 745, 440))
    E.append(chip('Sakit kepala', 'bolt', 320, YEL, 16.66, 18.3, 725, 570))
    # 5 — jangan panik
    E += banner('Bertenang', 'Jangan panik', 'Sakit kepala budak biasanya bukan serius', 'check', 18.3, 22.7, icon_bg=GREEN, sub_t=19.7)
    # 6 — punca lain
    E += banner('Punca lain', 'Antara punca sakit kepala', None, 'alert', 22.7, 27.3, icon_bg=YEL)
    E.append(chip('Kurang minum air', 'drop', 360, (90, 190, 255), 24.32, 27.3, 20, 430))
    E.append(chip('Stres', 'bolt', 250, YEL, 24.84, 27.3, 790, 430))
    E.append(chip('Kurang tidur', 'moon', 330, (170, 150, 255), 26.30, 27.3, 20, 560))
    # 7 — fakta malaysia (carta)
    E += banner('Fakta di Malaysia', 'Rabun jauh kanak-kanak', 'Anggaran peratusan mengikut umur', 'search', 27.3, 37.6)
    E += banner('Fakta di Malaysia', 'Rabun jauh kanak-kanak', 'Hampir 3.5× ganda dalam 8 tahun', 'search', 37.6, 39.5, icon_bg=YEL)
    E.append(bar_chart_el('l', 29.0, 39.5, 30, 740, 260, 9.8, 'Umur 7 tahun', 30.15, 32.2, TEAL))
    E.append(bar_chart_el('r', 34.4, 39.5, 745, 740, 260, 34.4, 'Umur 15 tahun', 35.1, 37.5, RED))
    # 8 — anak tak sedar
    E += banner('Tanda yang terlepas', 'Anak pun sering tak sedar', 'penglihatan dia bermasalah', 'eye', 39.5, 43.2)
    E.append(blur_card(40.3, 43.2, 770, 440))
    # 9 — pemeriksaan
    E += banner('Langkah seterusnya', 'Sakit kepala berulang?', 'Bawa buat pemeriksaan mata', 'search', 43.2, 46.5, icon_bg=YEL)
    E.append(chip('Pemeriksaan mata', 'check', 430, GREEN, 44.4, 46.5, 20, 440))
    # 10 — suplemen
    E += banner('Penjagaan mata', 'Suplemen penjagaan mata', 'DS Pharma Eye Care · 650mg', 'pill', 46.5, 53.4)
    E.append(product_card(47.9, 58.7, 10, 395))
    E += ingredient_els([49.9, 50.4, 50.9, 51.4], 53.4, 735, 395)
    E.append(disclaimer(47.2, 58.65))
    # 11 — jangan tunggu
    E += banner('Jangan tunggu lagi', 'Semak mata anak anda', 'Sakit kepala berulang? Periksa mata', 'clock', 53.4, 55.1, icon_bg=YEL)
    E.append(tiktok_card(54.5, 58.7, 682, 400))
    # 12 — CTA
    E += banner('Dapatkan sekarang', 'DS Pharma Eye Care', 'TikTok Shop · DS Pharma Wellness', 'pill', 55.1, 58.7)
    return E

def banner_sub_badge(text):
    f = F('ExtraBold', 34); w = int(f.getlength(text)) + 60
    img, pad = rrect_img(w, 70, 35, (255, 216, 77, 255), shadow=1)
    ImageDraw.Draw(img).text((pad + w / 2, pad + 35), text, font=f, fill=DARK, anchor='mm')
    return img

SCENE = None

# ───────────────────────── komposit ─────────────────────────
def composite(frame, t, matte):
    out = frame.copy().astype(np.float32)
    boxes = []
    tops = [e for e in SCENE if e.top]
    for e in [e for e in SCENE if not e.top]:
        r = e.at(t)
        if r is None: continue
        img, x, y, a = r
        h, w = img.shape[:2]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0: continue
        s = img[y0 - y:y1 - y, x0 - x:x1 - x]
        al = (s[..., 3:4] / 255.0) * a
        out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - al) + s[..., :3] * al
        boxes.append((x0, y0, x1, y1))
    # orang kembali ke hadapan (overlay "di belakang kepala/badan")
    for (x0, y0, x1, y1) in boxes:
        m = matte[y0:y1, x0:x1, None]
        out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - m) + frame[y0:y1, x0:x1].astype(np.float32) * m
    for e in tops:
        r = e.at(t)
        if r is None: continue
        img, x, y, a = r; h, w = img.shape[:2]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        s_ = img[y0 - y:y1 - y, x0 - x:x1 - x]; al = (s_[..., 3:4] / 255.0) * a
        out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - al) + s_[..., :3] * al
    # subtitle di atas semua
    for words in CAPS:
        a, b = words[0][1], words[-1][2]
        nxt_gap = 0.35
        if a - 0.05 <= t <= b + nxt_gap:
            img, hh = render_caption(words, t, b)
            arr = np.asarray(img).astype(np.float32)
            y0 = CAP_Y; y1 = min(H, y0 + hh)
            al = arr[:y1 - y0, :, 3:4] / 255.0
            out[y0:y1] = out[y0:y1] * (1 - al) + arr[:y1 - y0, :, :3] * al
            break
    return np.clip(out, 0, 255).astype(np.uint8)

def read_frames():
    cmd = ['ffmpeg', '-v', 'error', '-i', SRC, '-vf', 'hflip', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 2)
    n = W * H * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)

def cmd_render(out='work/render_noaudio.mp4'):
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                            '-color_trc', 'bt709', out], stdin=subprocess.PIPE)
    prev = None
    for i, fr in enumerate(read_frames()):
        t = i / FPS
        m = get_matte(fr)
        if prev is not None: m = 0.7 * m + 0.3 * prev
        prev = m
        enc.stdin.write(composite(fr, t, m).tobytes())
        if i % 150 == 0: print('frame', i, flush=True)
    enc.stdin.close(); enc.wait()

def cmd_stills(times):
    for t in times:
        cmd = ['ffmpeg', '-v', 'error', '-ss', str(t), '-i', SRC, '-vf', 'hflip', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
        fr = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.uint8).reshape(H, W, 3)
        o = composite(fr, float(t), get_matte(fr))
        Image.fromarray(o).resize((540, 960), Image.LANCZOS).save(f'work/still_{t}.jpg', quality=88)

if __name__ == '__main__':
    SCENE = build_scene()
    if sys.argv[1] == 'render': cmd_render()
    elif sys.argv[1] == 'stills': cmd_stills(sys.argv[2:])
    elif sys.argv[1] == 'caps':
        for c in CAPS: print(f'{c[0][1]:6.2f}-{c[-1][2]:6.2f}', ' '.join(w for w, _, _ in c))
