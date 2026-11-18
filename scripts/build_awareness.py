#!/usr/bin/env python3
"""Bina video awareness retina v2: jump-cut, subtitle pop-in, overlay beranimasi (jujukan frame PNG), -14 LUFS.
Guna: python3 -I scripts/build_awareness.py   (perlu work/words.json dari faster-whisper)
"""
import json, math, os, shutil, subprocess
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_, H_ = 1080, 1920
FPS = 30
SRC = f"{ROOT}/input/awareness.mov"
WORK = f"{ROOT}/work/ov"
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FX = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FR = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"

# ---------- 1. segmen dikekalkan (masa sumber) ----------
KEEP = [(0.60, 2.80), (2.92, 11.70), (11.88, 20.75), (20.92, 40.75),
        (40.90, 43.45), (44.82, 49.42)]
END_HOLD = 2.4

def mp_near(t):
    acc = 0.0
    for a, b in KEEP:
        if t < a: return acc
        if t <= b: return acc + (t - a)
        acc += b - a
    return acc
def mp(t):
    acc = 0.0
    for a, b in KEEP:
        if a <= t <= b: return acc + (t - a)
        acc += b - a
    return None
MAIN_DUR = sum(b - a for a, b in KEEP)
TOTAL = MAIN_DUR + END_HOLD

# ---------- 2. subtitle ----------
FIX = {"keota.": "otak.", "menghebut": "menyebut"}
DROP = {"pun"}
words = []
for seg in json.load(open(f"{ROOT}/work/words.json")):
    for w, s, e in seg["w"]:
        w = w.strip(); w = FIX.get(w, w)
        if w.lower() in DROP: continue
        if w in ("-tiba", "-labah"): words[-1][0] += w; words[-1][2] = e; continue
        words.append([w, s, e])
words[0][1] = max(words[0][1], 0.78)
# masa sebenar hujung ayat (dari tenaga audio)
for w in words:
    if w[0] == "ataupun": w[1], w[2] = 48.10, 48.70
    if w[0] == "sekarang.": w[1], w[2] = 48.88, 49.32
    if w[0] == "ini": w[1], w[2] = 47.30, 47.95

KEY = ("kilat", "bintik", "benang", "labah", "esok", "retina", "tertanggal", "koyak", "kecemasan", "sakit",
       "24", "jam", "hospital", "tirai", "bayang", "segera", "hari", "ini", "otak", "sekarang")
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
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"

def build_ass(path):
    chunks = build_chunks(); ev = []
    for i, ch in enumerate(chunks):
        a = max(mp_near(ch[0][1]) - 0.03, 0)
        b = mp_near(ch[-1][2]) + 0.18
        if i + 1 < len(chunks): b = min(b, mp_near(chunks[i + 1][0][1]) - 0.02)
        b = min(b, MAIN_DUR)
        if b - a < 0.25: b = a + 0.25
        parts = [(YEL if any(w[0].strip(".,?!").lower().startswith(k) for k in KEY) else WHT) + w[0].upper() for w in ch]
        pop = r"{\fscx82\fscy82\alpha&H80&\t(0,130,\fscx100\fscy100\alpha&H00&)}"
        ev.append(f"Dialogue: 0,{tc(a)},{tc(b)},Sub,,0,0,0,,{pop}{' '.join(parts)}")
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W_}
PlayResY: {H_}
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,Inter,64,&H00FFFFFF,&H000000FF,&H00201008,&H80000000,1,0,0,0,100,100,0,0,1,7,2,2,60,60,520,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    open(path, "w", encoding="utf-8").write(hdr + "\n".join(ev) + "\n")
    return chunks

# ---------- 3. enjin grafik beranimasi ----------
SS = 2  # supersample
def F(p, s): return ImageFont.truetype(p, int(s * SS))
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def seg(t, a, b): return clamp((t - a) / (b - a)) if b > a else 1.0

NAVY = (11, 22, 52); TEAL = (45, 212, 191); RED = (239, 68, 68); AMBER = (251, 191, 36)
WHITE = (255, 255, 255); SOFT = (203, 213, 225); BLUE = (96, 165, 250)

class G:
    """Kanvas 1x logik, lukis pada 2x."""
    def __init__(self, w, h):
        self.im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im); self.w, self.h = w, h
    def s(self, pts): return [(x * SS, y * SS) for x, y in pts]
    def rrect(self, x0, y0, x1, y1, r, fill, outline=None, width=0):
        self.d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], r * SS, fill=fill, outline=outline, width=int(width * SS))
    def ell(self, cx, cy, rx, ry=None, fill=None, outline=None, width=0):
        ry = rx if ry is None else ry
        self.d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=fill, outline=outline, width=int(width * SS))
    def poly(self, pts, fill): self.d.polygon(self.s(pts), fill=fill)
    def line(self, pts, fill, width=3): self.d.line(self.s(pts), fill=fill, width=int(width * SS), joint="curve")
    def arc(self, cx, cy, r, a0, a1, fill, width):
        self.d.arc([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], a0, a1, fill=fill, width=int(width * SS))
    def text(self, x, y, t, font, fill=WHITE, anchor="la"):
        self.d.text((x * SS, y * SS), t, font=font, fill=fill, anchor=anchor)
    def tw(self, t, font): b = self.d.textbbox((0, 0), t, font=font); return (b[2] - b[0]) / SS
    def glow(self, cx, cy, r, col, a):
        g = Image.new("RGBA", self.im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        for k in range(8):
            rr = r * (1 - k / 8) * SS
            gd.ellipse([cx * SS - rr, cy * SS - rr, cx * SS + rr, cy * SS + rr], fill=col + (int(a * 255 * (k + 1) / 20),))
        self.im = Image.alpha_composite(self.im, g); self.d = ImageDraw.Draw(self.im)

CW = 920          # lebar kad seragam
PAD = 40          # ruang untuk animasi keluar-masuk di sekeliling kad

def card_base(g, h, accent, fill=NAVY, a=232):
    g.rrect(PAD, PAD, PAD + CW, PAD + h, 34, fill + (a,))
    g.rrect(PAD, PAD, PAD + 16, PAD + h, 8, accent + (255,))
    g.rrect(PAD, PAD, PAD + CW, PAD + h, 34, None, outline=(255, 255, 255, 40), width=2)

def title_sub(g, t, title, sub, h, tsize=56, x=PAD + 60, accent=None, sub2=None):
    """Teks kad: tajuk muncul dahulu, sub menyusul."""
    ta = ease_out(seg(t, 0.12, 0.45)); sa = ease_out(seg(t, 0.30, 0.65))
    fs = tsize
    while g.tw(title, F(FX, fs)) > (PAD + CW - 30 - x) and fs > 28: fs -= 2
    ty = PAD + (h - (fs + (52 if sub else 0))) / 2 - 4
    g.text(x + (1 - ta) * 24, ty, title, F(FX, fs), WHITE + (int(255 * ta),))
    if sub:
        sf = 38
        while g.tw(sub, F(FR, sf)) > (PAD + CW - 30 - x) and sf > 24: sf -= 1
        g.text(x + (1 - sa) * 24, ty + fs + 14, sub, F(FR, sf), SOFT + (int(255 * sa),))

# ---- ikon beranimasi (cx, cy = pusat, t = masa lokal) ----
def ico_warn(g, cx, cy, t, col=AMBER, s=92):
    pulse = 1 + 0.06 * math.sin(t * 7)
    s *= pulse
    g.glow(cx, cy, s * .85, col, 0.5 + 0.3 * math.sin(t * 7))
    g.poly([(cx, cy - s / 2), (cx + s / 2, cy + s * .42), (cx - s / 2, cy + s * .42)], col + (255,))
    g.rrect(cx - 4.5, cy - s * .12, cx + 4.5, cy + s * .2, 3, NAVY + (255,))
    g.ell(cx, cy + s * .3, 5.5, fill=NAVY + (255,))

def ico_bolt(g, cx, cy, t, s=96):
    flick = 1.0 if int(t * 9) % 4 else 0.35
    g.glow(cx, cy, s * .9, AMBER, 0.55 * flick)
    p = [(.55, 0), (.15, .55), (.45, .55), (.3, 1), (.85, .4), (.52, .4), (.7, 0)]
    g.poly([(cx - s / 2 + a * s, cy - s / 2 + b * s) for a, b in p], AMBER + (int(255 * (0.6 + 0.4 * flick)),))

def ico_dots(g, cx, cy, t, s=96):
    import random
    rnd = random.Random(11)
    for i in range(8):
        r = rnd.uniform(4, 9); bx = rnd.uniform(-s / 2, s / 2); by = rnd.uniform(-s / 2, s / 2)
        ph = rnd.uniform(0, 6)
        ap = ease_out(seg(t, 0.06 * i, 0.06 * i + 0.25))
        x = cx + bx + math.sin(t * 2 + ph) * 8; y = cy + by + math.cos(t * 1.7 + ph) * 8
        g.ell(x, y, r * ap, fill=WHITE + (240,))

def ico_web(g, cx, cy, t, s=96):
    n = 8; R = s / 2
    pr = ease_out(seg(t, 0, 0.8))
    for k in range(n):
        a = k * 2 * math.pi / n
        g.line([(cx, cy), (cx + math.cos(a) * R * pr, cy + math.sin(a) * R * pr)], WHITE + (230,), 2.5)
    for rr in (.3, .55, .8, 1.0):
        if pr * 1 >= rr * .9:
            pts = [(cx + math.cos(k * 2 * math.pi / n) * R * rr, cy + math.sin(k * 2 * math.pi / n) * R * rr) for k in range(n + 1)]
            g.line(pts, WHITE + (230,), 2.5)
    # labah-labah bergayut
    sy = cy - R + 12 + 18 * (0.5 + 0.5 * math.sin(t * 3))
    g.line([(cx + R * 0.55, cy - R), (cx + R * 0.55, sy)], WHITE + (180,), 2)
    g.ell(cx + R * 0.55, sy + 6, 6, fill=(250, 204, 21, 255))

def ico_check(g, cx, cy, t, s=92):
    p = ease_out(seg(t, 0.1, 0.7))
    g.glow(cx, cy, s * .8, TEAL, 0.35)
    g.ell(cx, cy, s / 2, fill=TEAL + (255,))
    pts = [(cx - s * .22, cy + s * .02), (cx - s * .06, cy + s * .18), (cx + s * .24, cy - s * .16)]
    if p < .5: pts = [pts[0], (pts[0][0] + (pts[1][0] - pts[0][0]) * p * 2, pts[0][1] + (pts[1][1] - pts[0][1]) * p * 2)]
    else:
        q = (p - .5) * 2; pts = [pts[0], pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * q, pts[1][1] + (pts[2][1] - pts[1][1]) * q)]
    g.line(pts, NAVY + (255,), 9)

def ico_curtain(g, cx, cy, t, s=96):
    """Pandangan mata dengan bayang/tirai gelap menutup dari tepi."""
    x0, y0 = cx - s / 2, cy - s * .38
    g.rrect(x0, y0, x0 + s, y0 + s * .76, 16, (125, 190, 240, 255))
    g.ell(cx - 8, cy - 4, 9, fill=(255, 255, 255, 230))
    p = 0.35 + 0.35 * (0.5 - 0.5 * math.cos(clamp(t / 2.2) * math.pi))
    sh = Image.new("RGBA", g.im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([x0 * SS, y0 * SS, (x0 + s) * SS, (y0 + s * .76) * SS], 16 * SS, fill=(0, 0, 0, 255))
    mask = Image.new("L", g.im.size, 0); md = ImageDraw.Draw(mask)
    md.rectangle([(x0 + s * (1 - p)) * SS, y0 * SS, (x0 + s) * SS, (y0 + s * .76) * SS], fill=255)
    sh.putalpha(Image.composite(sh.split()[3], Image.new("L", g.im.size, 0), mask))
    g.im = Image.alpha_composite(g.im, sh); g.d = ImageDraw.Draw(g.im)

def ico_siren(g, cx, cy, t, s=92):
    g.glow(cx, cy, s * .95, RED, 0.45 + 0.4 * abs(math.sin(t * 6)))
    g.ell(cx, cy, s / 2, fill=RED + (255,))
    g.rrect(cx - 6, cy - s * .26, cx + 6, cy + s * .08, 4, WHITE + (255,))
    g.ell(cx, cy + s * .22, 6.5, fill=WHITE + (255,))

# ---- templat kad ----
def make_chip(icon, title, sub, accent=AMBER, h=170):
    def draw(g, t):
        card_base(g, h, accent)
        icon(g, PAD + 100, PAD + h / 2, t)
        title_sub(g, t, title, sub, h, tsize=58, x=PAD + 190, accent=accent)
    return CW + 2 * PAD, h + 2 * PAD, draw

def make_banner(title, sub=None, col=RED, h=170, tsize=70, siren=True):
    def draw(g, t):
        shake = math.sin(t * 40) * 6 * (1 - seg(t, 0.3, 0.7)) if t < 0.7 else 0
        pulse = 1 + 0.015 * math.sin(t * 8)
        g.glow(PAD + CW / 2, PAD + h / 2, CW * .55, col, 0.15 + 0.1 * math.sin(t * 8))
        g.rrect(PAD + shake, PAD, PAD + CW + shake, PAD + h, 34, col + (255,))
        g.rrect(PAD + shake, PAD, PAD + CW + shake, PAD + h, 34, None, outline=(255, 255, 255, 60), width=2)
        ta = ease_back(seg(t, 0.1, 0.5))
        fs = tsize
        while g.tw(title, F(FX, fs)) > CW - 80 and fs > 30: fs -= 2
        ty = PAD + (h - fs - (44 if sub else 0)) / 2 - 4
        g.text(PAD + CW / 2 + shake, ty, title, F(FX, fs * (0.9 + 0.1 * ta)), WHITE + (int(255 * clamp(ta)),), anchor="ma")
        if sub:
            sa = ease_out(seg(t, 0.4, 0.8))
            g.text(PAD + CW / 2 + shake, ty + fs + 14, sub, F(FR, 36), (255, 232, 232, int(255 * sa)), anchor="ma")
    return CW + 2 * PAD, h + 2 * PAD, draw

def make_eye():
    h = 370
    def draw(g, t):
        card_base(g, h, TEAL)
        cx, cy, R = PAD + 180, PAD + h / 2, 108
        pe = ease_out(seg(t, 0.05, 0.6))
        g.ell(cx, cy, R * pe, fill=(241, 245, 250, 255)); g.ell(cx, cy, R * pe, outline=(148, 163, 184, 255), width=5)
        g.ell(cx - R + 14, cy, 40 * pe, 52 * pe, fill=(125, 211, 252, 255))
        g.ell(cx - R + 38, cy, 17 * pe, 24 * pe, fill=(30, 41, 59, 255))
        # retina: sapuan arka di belakang
        pr = ease_out(seg(t, 0.55, 1.25))
        if pr > 0:
            g.arc(cx, cy, R - 5, -62, -62 + 124 * pr, RED + (255,), 14)
        # label retina
        la = ease_out(seg(t, 1.1, 1.5))
        if la > 0:
            g.line([(cx + R * .55, cy - R * .5), (cx + R * .55 + 70, cy - 105)], RED + (int(255 * la),), 4)
            g.text(cx + R + 20 + (1 - la) * 20, cy - 150, "RETINA", F(FX, 54), (254, 202, 202, int(255 * la)))
            g.text(cx + R + 22 + (1 - la) * 20, cy - 92, "lapisan di belakang mata", F(FR, 32), SOFT + (int(255 * la),))
        # paket data bergerak ke otak
        aa = ease_out(seg(t, 2.0, 2.4))
        if aa > 0:
            ly = cy + 70
            sx, ex = cx + R + 14, PAD + 690
            g.line([(sx, ly), (ex - 6, ly)], TEAL + (int(200 * aa),), 5)
            for k in range(3):
                q = ((t * 0.8 + k / 3) % 1)
                g.ell(sx + (ex - sx) * q, ly, 9, fill=(153, 246, 228, int(255 * aa)))
            g.text(sx + 6, ly - 52, "hantar gambar ke otak", F(FB, 30), WHITE + (int(255 * aa),))
        oa = ease_back(seg(t, 2.3, 2.8))
        if oa > 0:
            pu = 1 + 0.05 * math.sin(t * 6)
            g.rrect(PAD + 690, cy + 70 - 41, PAD + 690 + 200 * pu, cy + 70 + 41, 30, (30, 58, 110, 255), outline=TEAL + (255,), width=3)
            g.text(PAD + 690 + 100 * pu, cy + 70 - 26, "OTAK", F(FX, 44), WHITE + (int(255 * clamp(oa)),), anchor="ma")
    return CW + 2 * PAD, h + 2 * PAD, draw

def make_24():
    h = 290
    def draw(g, t):
        card_base(g, h, AMBER)
        cx, cy, R = PAD + 190, PAD + h / 2, 92
        p = ease_out(seg(t, 0.1, 1.6))
        g.ell(cx, cy, R, fill=(30, 41, 59, 255)); g.ell(cx, cy, R, outline=(71, 85, 105, 255), width=6)
        g.arc(cx, cy, R - 3, -90, -90 + 360 * p, AMBER + (255,), 12)
        n = int(round(24 * p))
        g.text(cx, cy - 52, str(n), F(FX, 96), WHITE, anchor="ma")
        g.text(cx, cy + 40, "JAM", F(FB, 30), AMBER + (255,), anchor="ma")
        tx = PAD + 340
        a1 = ease_out(seg(t, 0.4, 0.8)); a2 = ease_out(seg(t, 0.8, 1.2))
        g.text(tx + (1 - a1) * 20, PAD + 62, "Pembaikan dalam 24 jam", F(FX, 42), WHITE + (int(255 * a1),))
        g.text(tx + (1 - a2) * 20, PAD + 128, "jika bahagian tengah retina", F(FR, 34), SOFT + (int(255 * a2),))
        g.text(tx + (1 - a2) * 20, PAD + 174, "masih melekat", F(FR, 34), SOFT + (int(255 * a2),))
    return CW + 2 * PAD, h + 2 * PAD, draw

def make_end():
    def draw(g, t):
        g.rrect(0, 0, W_, H_, 0, (8, 16, 40, int(238 * ease_out(seg(t, 0, 0.4)))))
        a = ease_back(seg(t, 0.2, 0.7)); ico_warn(g, W_ / 2, 640, t, s=170 * clamp(a))
        b = ease_out(seg(t, 0.45, 0.85)); g.text(W_ / 2, 790 + (1 - b) * 40, "JANGAN TUNGGU.", F(FX, 96), WHITE + (int(255 * b),), anchor="ma")
        c = ease_out(seg(t, 0.7, 1.1)); g.text(W_ / 2, 910 + (1 - c) * 40, "Periksa mata segera.", F(FB, 64), (153, 246, 228, int(255 * c)), anchor="ma")
        d_ = ease_out(seg(t, 0.95, 1.35))
        g.text(W_ / 2, 1060, "Kilat cahaya, bintik / benang baharu,", F(FR, 40), SOFT + (int(255 * d_),), anchor="ma")
        g.text(W_ / 2, 1116, "atau tirai menutup pandangan", F(FR, 40), SOFT + (int(255 * d_),), anchor="ma")
        e = ease_back(seg(t, 1.2, 1.7)); pu = 1 + 0.02 * math.sin(t * 7)
        w2 = 840 * clamp(e) * pu
        g.rrect(W_ / 2 - w2 / 2, 1230, W_ / 2 + w2 / 2, 1360, 34, RED + (int(255 * clamp(e)),))
        g.text(W_ / 2, 1262, "KE HOSPITAL HARI INI", F(FX, 66), WHITE + (int(255 * clamp(e)),), anchor="ma")
        f = ease_out(seg(t, 1.6, 2.0))
        g.text(W_ / 2, 1700, "Maklumat umum untuk kesedaran, bukan pengganti nasihat doktor.", F(FR, 28), (148, 163, 184, int(255 * f)), anchor="ma")
    return W_, H_, draw

# (nama, templat, src_start, src_end, y)
Y = 120
OVERLAYS = [
    ("o1", make_chip(ico_bolt, "Kilat cahaya", "di tepi mata"), 0.85, 2.85, Y),
    ("o2", make_chip(ico_dots, "Bintik hitam", "tiba-tiba, makin banyak"), 3.00, 5.0, Y),
    ("o3", make_chip(ico_web, "Benang / sarang labah-labah", "makin banyak"), 5.0, 7.30, Y),
    ("o4", make_banner("JANGAN TUNGGU ESOK", "Bertindak segera selamatkan penglihatan", RED, 190, 70), 7.40, 8.62, Y),
    ("o5", make_chip(ico_warn, "Retina koyak / tertanggal", "itu mungkin tandanya", TEAL), 8.70, 11.7, Y),
    ("o6", make_eye(), 11.95, 16.0, Y - 20),
    ("o7", make_banner("KECEMASAN PERUBATAN", "Retina tertanggal", RED, 190, 66), 16.15, 20.75, Y),
    ("o8", make_chip(ico_check, "Selalunya TIDAK SAKIT", "jangan tunggu sampai sakit", AMBER), 20.95, 22.9, Y),
    ("o9", make_chip(ico_check, "Kebanyakannya tak serius", "hanya pemeriksaan mata boleh pastikan", TEAL, 190), 23.0, 28.8, Y),
    ("o10", make_chip(ico_check, "Pakar di Malaysia", "nasihatkan pemeriksaan segera", TEAL), 28.9, 33.0, Y),
    ("o11", make_24(), 33.1, 40.7, Y),
    ("o12", make_chip(ico_curtain, "Tirai atau bayang", "menutup sebahagian pandangan", RED), 40.95, 46.4, Y),
    ("o13", make_banner("KE HOSPITAL HARI INI", None, RED, 150, 70), 46.4, 49.42, Y),
]

def render_frames(job):
    name, idx, dur, outdir = job
    w, h, draw = make_end() if name == 'end' else OVERLAYS[idx][1]
    os.makedirs(outdir, exist_ok=True)
    n = int(round(dur * FPS)); IN, OUT = 0.38, 0.28
    for i in range(n):
        t = i / FPS
        g = G(w, h); draw(g, t)
        im = g.im
        if name != "end":
            tin = seg(t, 0, IN); tout = seg(t, dur - OUT, dur)
            sc = (0.9 + 0.1 * ease_back(tin)) if tin < 1 else 1.0
            dy = (1 - ease_out(tin)) * -46 + ease_out(tout) * -30
            alpha = clamp(tin * 1.6) * (1 - tout)
            if sc != 1.0:
                nw, nh = int(im.width * sc), int(im.height * sc)
                im2 = im.resize((nw, nh), Image.LANCZOS)
                canvas = Image.new("RGBA", im.size, (0, 0, 0, 0)); canvas.paste(im2, ((im.width - nw) // 2, (im.height - nh) // 2))
                im = canvas
            if dy:
                canvas = Image.new("RGBA", im.size, (0, 0, 0, 0)); canvas.paste(im, (0, int(dy * SS))); im = canvas
            a = im.split()[3].point(lambda v: int(v * alpha)); im.putalpha(a)
        elif t > dur - 0.0: pass
        im = im.resize((w, h), Image.LANCZOS)
        im.save(f"{outdir}/{i:04d}.png")
    return name

def build_assets():
    shutil.rmtree(WORK, ignore_errors=True); os.makedirs(WORK)
    jobs = []
    for i, (name, tpl, a, b, y) in enumerate(OVERLAYS):
        jobs.append((name, i, mp_near(b) - mp_near(a), f"{WORK}/{name}"))
    jobs.append(("end", -1, END_HOLD, f"{WORK}/end"))
    with Pool() as p: p.map(render_frames, jobs)

# ---------- 4. ffmpeg ----------
def build():
    build_assets()
    ass = f"{ROOT}/work/awareness.ass"
    chunks = build_ass(ass)
    with open(f"{ROOT}/work/awareness.srt", "w", encoding="utf-8") as f:
        for i, ch in enumerate(chunks, 1):
            a = mp_near(ch[0][1]); b = mp_near(ch[-1][2]) + 0.15
            t = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(x%1*1000):03d}"
            f.write(f"{i}\n{t(a)} --> {t(b)}\n{' '.join(x[0] for x in ch)}\n\n")
    inputs = ["-i", SRC]; fc = []
    for i, (a, b) in enumerate(KEEP):
        z = 1.0 if i % 2 == 0 else 1.12
        zw, zh = int(W_ * z) // 2 * 2, int(H_ * z) // 2 * 2
        fc.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,scale={zw}:{zh},crop={W_}:{H_}:{(zw-W_)//2}:{int((zh-H_)*0.25)}[v{i}]")
        fc.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b-a-0.012:.3f}:d=0.012[a{i}]")
    n = len(KEEP)
    fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    fc.append("[vc]eq=contrast=1.06:saturation=1.12:brightness=0.01,format=yuv420p[vb]")
    fc.append(f"[vb]tpad=stop_mode=clone:stop_duration={END_HOLD}[vt]")
    cur = "vt"
    for k, (name, tpl, a, b, y) in enumerate(OVERLAYS):
        oa = mp_near(a)
        inputs += ["-framerate", str(FPS), "-i", f"{WORK}/{name}/%04d.png"]
        fc.append(f"[{k+1}:v]format=rgba,setpts=PTS+{oa:.3f}/TB[ov{k}]")
        fc.append(f"[{cur}][ov{k}]overlay=x=(W-w)/2:y={y}-{PAD}:eof_action=pass[t{k}]")
        cur = f"t{k}"
    fc.append(f"[{cur}]subtitles={ass}:fontsdir=/usr/share/fonts/opentype/inter[vs]")
    ei = len(OVERLAYS) + 1
    inputs += ["-framerate", str(FPS), "-i", f"{WORK}/end/%04d.png"]
    fc.append(f"[{ei}:v]format=rgba,setpts=PTS+{MAIN_DUR:.3f}/TB[end]")
    fc.append("[vs][end]overlay=0:0:eof_action=repeat[vout]")
    fc.append(f"[ac]highpass=f=80,afftdn=nf=-28,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
              f"afade=t=out:st={MAIN_DUR-0.25:.3f}:d=0.25,apad=pad_dur={END_HOLD},loudnorm=I=-14:TP=-1.5:LRA=9[aout]")
    out = f"{ROOT}/output/awareness_retina_final.mp4"
    subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
                    "-t", f"{TOTAL:.3f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
    print(out, f"{TOTAL:.2f}s")

if __name__ == "__main__":
    build()
