#!/usr/bin/env python3
"""Video awareness 9:16: overlay grafik animasi di BELAKANG orang (segmentasi) + subtitle.
Guna:  python3 -I scripts/overlay_edu.py input/main.mov output/out.mp4 [--stills 1,5,13]
Perlu: mediapipe, opencv-python-headless, pillow, numpy, work/seg.tflite (selfie_segmenter)
"""
import sys, math, subprocess, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import mediapipe as mp
from mediapipe.tasks import python as mpp
from mediapipe.tasks.python import vision

W, H, FPS, S = 1080, 1920, 30, 2
FD = '/usr/share/fonts/opentype/inter/'
_fc = {}
def F(sz, w='Bold'):
    k = (sz, w)
    if k not in _fc: _fc[k] = ImageFont.truetype(f'{FD}Inter-{w}.otf', int(sz * S))
    return _fc[k]

WHITE=(255,255,255); TEAL=(45,212,191); AMBER=(251,191,36); RED=(248,95,95); NAVY=(12,20,46); VIOL=(139,92,246)

def ease(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def anim(t, t0, d=0.4): return ease((t - t0) / d)

# ---------- helpers (koordinat 1x, dilukis 2x) ----------
def rr(d, x0, y0, x1, y1, r, fill=None, outline=None, width=1):
    d.rounded_rectangle([x0*S, y0*S, x1*S, y1*S], r*S, fill=fill, outline=outline, width=int(width*S))
def tx(d, x, y, s, font, fill=WHITE, anchor='la', shadow=True):
    if shadow:
        d.text((x*S, (y+3)*S), s, font=font, fill=(0, 0, 0, 120), anchor=anchor)
    d.text((x*S, y*S), s, font=font, fill=fill, anchor=anchor)
def tw(s, font): return font.getlength(s) / S
def circ(d, cx, cy, r, fill=None, outline=None, width=1):
    d.ellipse([(cx-r)*S, (cy-r)*S, (cx+r)*S, (cy+r)*S], fill=fill, outline=outline, width=int(width*S))
def poly(d, pts, fill, width=0):
    d.polygon([(x*S, y*S) for x, y in pts], fill=fill)
def line(d, pts, fill, width):
    d.line([(x*S, y*S) for x, y in pts], fill=fill, width=int(width*S), joint='curve')

def blit(canvas, x, y, w, h, alpha, fn, dy=0):
    """lukis fn(d) pada layer tempatan (origin = x,y) dan composite dengan alpha."""
    if alpha <= 0.01: return
    tmp = Image.new('RGBA', (int(w*S), int(h*S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    fn(d)
    if alpha < 1:
        a = tmp.getchannel('A').point(lambda v: int(v * alpha)); tmp.putalpha(a)
    canvas.alpha_composite(tmp, (int(x*S), int((y+dy)*S)))

# ---------- ikon (lokal 0..size) ----------
def badge(d, cx, cy, r, col):
    circ(d, cx, cy, r+10, fill=(*col, 50))
    circ(d, cx, cy, r, fill=(*NAVY, 235), outline=col, width=5)
def eye(d, cx, cy, s, pupil=WHITE, iris=TEAL):
    pts = []
    for i in range(41):
        u = i / 40 * 2 - 1
        pts.append((cx + u * s, cy - (1 - u*u) * s * 0.55))
    for i in range(41):
        u = 1 - i / 40 * 2
        pts.append((cx + u * s, cy + (1 - u*u) * s * 0.55))
    poly(d, pts, (245, 248, 255, 255))
    circ(d, cx, cy, s*0.42, fill=iris); circ(d, cx, cy, s*0.18, fill=(10, 20, 40))
def icon(d, kind, cx, cy, r, t=0):
    col = {'sun':AMBER,'warn':AMBER,'bolt':VIOL,'vision':TEAL,'redeye':RED,'scratch':TEAL,'inflam':RED,
           'cataract':TEAL,'virus':RED,'ask':AMBER,'plus':TEAL}[kind]
    badge(d, cx, cy, r, col)
    if kind == 'sun':
        circ(d, cx, cy, r*0.38, fill=AMBER)
        for i in range(12):
            a = i * math.pi / 6 + t * 0.6
            line(d, [(cx+math.cos(a)*r*0.55, cy+math.sin(a)*r*0.55), (cx+math.cos(a)*r*0.8, cy+math.sin(a)*r*0.8)], AMBER, 6)
    elif kind == 'warn':
        poly(d, [(cx, cy-r*0.6), (cx+r*0.62, cy+r*0.45), (cx-r*0.62, cy+r*0.45)], AMBER)
        line(d, [(cx, cy-r*0.2), (cx, cy+r*0.15)], NAVY, 9); circ(d, cx, cy+r*0.3, 5, fill=NAVY)
    elif kind == 'bolt':
        poly(d, [(cx+r*.15, cy-r*.65), (cx-r*.4, cy+r*.08), (cx-r*.02, cy+r*.08), (cx-r*.15, cy+r*.65), (cx+r*.42, cy-r*.12), (cx+r*.05, cy-r*.12)], VIOL)
    elif kind == 'vision':
        eye(d, cx, cy, r*0.62)
        for k in (-1, 1): line(d, [(cx+k*r*.75, cy-r*.4), (cx+k*r*.92, cy-r*.55)], TEAL, 5)
    elif kind == 'redeye':
        eye(d, cx, cy, r*0.62, iris=(60, 100, 160))
        for a in (-.5, -.2, .2, .5, 2.6, 2.9, 3.4, 3.7): line(d, [(cx+math.cos(a)*r*.22, cy+math.sin(a)*r*.22), (cx+math.cos(a)*r*.58, cy+math.sin(a)*r*.3)], RED, 4)
    elif kind == 'scratch':
        eye(d, cx, cy, r*0.62); line(d, [(cx-r*.3, cy-r*.35), (cx+r*.3, cy+r*.35)], RED, 6)
    elif kind == 'inflam':
        eye(d, cx, cy, r*0.62)
        for a in range(0, 360, 30):
            q = math.radians(a); line(d, [(cx+math.cos(q)*r*.7, cy+math.sin(q)*r*.7), (cx+math.cos(q)*r*.88, cy+math.sin(q)*r*.88)], RED, 5)
    elif kind == 'cataract':
        eye(d, cx, cy, r*0.62); circ(d, cx, cy, r*0.26, fill=(225, 232, 240, 235))
    elif kind == 'virus':
        circ(d, cx, cy, r*.32, fill=RED)
        for a in range(0, 360, 45):
            q = math.radians(a); line(d, [(cx+math.cos(q)*r*.32, cy+math.sin(q)*r*.32), (cx+math.cos(q)*r*.58, cy+math.sin(q)*r*.58)], RED, 5)
            circ(d, cx+math.cos(q)*r*.62, cy+math.sin(q)*r*.62, 6, fill=RED)
    elif kind == 'ask':
        tx(d, cx, cy, '?', F(r*1.3, 'ExtraBold'), AMBER, 'mm', shadow=False)
    elif kind == 'plus':
        rr(d, cx-r*.14, cy-r*.5, cx+r*.14, cy+r*.5, 5, fill=TEAL); rr(d, cx-r*.5, cy-r*.14, cx+r*.5, cy+r*.14, 5, fill=TEAL)

def pill(d, x, y, s, font, bg, fg, padx=22, h=52):
    w = tw(s, font) + padx * 2
    rr(d, x, y, x+w, y+h, h/2, fill=bg)
    tx(d, x+padx, y+h/2, s, font, fg, 'lm', shadow=False)
    return w

# ---------- jadual adegan ----------
# (mula, tamat)
SC = dict(A=(0.5,3.7), A2=(3.7,5.4), B1=(5.4,10.2), B2=(10.2,12.4), C=(12.4,18.0), D=(18.0,30.0),
          E=(30.0,33.3), F=(33.3,42.2), G=(42.2,48.1))
D_ITEMS = [('Mata merah berjangkit','redeye',18.0,23.6),('Luka pada permukaan mata','scratch',23.6,25.4),
           ('Radang dalam mata','inflam',25.4,27.2),('Katarak','cataract',27.2,28.5),('Jangkitan selaput otak','virus',28.5,30.0)]

def vis(key, t):
    a, b = SC[key]
    if t < a - 0.02 or t > b + 0.3: return 0, 0
    return anim(t, a, .45) * (1 - ease((t - b) / .3)), a

def head(c, t, key, kicker, lines, kcol=TEAL):
    """kicker pill + baris headline besar. lines=[(teks,saiz,warna)]"""
    al, a = vis(key, t)
    if al <= 0: return
    dy = (1 - anim(t, a, .45)) * 30
    def f(d):
        x = (W - (tw(kicker, F(34)) + 44)) / 2
        pill(d, x, 0, kicker, F(34), (*kcol, 255), NAVY, 22, 54)
        y = 62
        for s, sz, col in lines:
            tx(d, W/2, y, s, F(sz, 'ExtraBold'), col, 'ma'); y += sz * 1.08
    blit(c, 0, 105, W, 260, al, f, dy)

def side_icon(c, t, key, kind, left=True, y=540, r=95):
    al, a = vis(key, t)
    if al <= 0: return
    cx = 175 if left else W - 175
    sc = 0.7 + 0.3 * anim(t, a, .5) + 0.03 * math.sin(t * 4)
    def f(d): icon(d, kind, 130, 130, r * sc, t)
    blit(c, cx - 130, y - 130, 260, 260, al, f)

def overlay(t):
    c = Image.new('RGBA', (W*S, 760*S), (0, 0, 0, 0))
    # ---- A
    head(c, t, 'A', 'FAKTA KESIHATAN ANAK', [('ANAK SILAU CAHAYA', 62, WHITE), ('MATAHARI?', 90, AMBER)], AMBER)
    side_icon(c, t, 'A', 'sun', True)
    head(c, t, 'A2', 'AMARAN', [('JANGAN', 72, WHITE), ('AGAK-AGAK', 88, AMBER)], RED)
    side_icon(c, t, 'A2', 'warn', False)
    # ---- B
    head(c, t, 'B1', 'SILAU / SENSITIF CAHAYA', [('BUKAN PENYAKIT', 92, WHITE)])
    side_icon(c, t, 'B1', 'sun', False)
    head(c, t, 'B2', 'TANDA ADA SESUATU BERLAKU', [('IA SIMPTOM', 100, AMBER)], AMBER)
    side_icon(c, t, 'B2', 'warn', True)
    # ---- C
    al, a = vis('C', t)
    if al > 0:
        def kick(d):
            tx(d, W/2, 0, 'PUNCA BIASA PADA KANAK-KANAK', F(36, 'ExtraBold'), TEAL, 'ma')
        blit(c, 0, 125, W, 60, al, kick, (1 - anim(t, a, .45)) * 20)
        for i, (t0, kind, l1, l2, col) in enumerate([(13.6, 'bolt', 'MIGRAIN', '', VIOL), (15.3, 'vision', 'PENGLIHATAN', 'belum dibetulkan', TEAL)]):
            p = anim(t, t0, .45)
            if p <= 0: continue
            x = 50 + i * 490
            def card(d, kind=kind, l1=l1, l2=l2, col=col, i=i):
                rr(d, 0, 0, 480, 150, 28, fill=(*NAVY, 225), outline=(*col, 255), width=3)
                icon(d, kind, 80, 75, 48, t)
                tx(d, 148, 62 if l2 else 75, l1, F(36 if l2 else 44, 'ExtraBold'), WHITE, 'lm', False)
                if l2: tx(d, 148, 100, l2, F(28, 'SemiBold'), col, 'lm', False)
                rr(d, 440, 12, 468, 40, 14, fill=(*col, 255)); tx(d, 454, 26, str(i+1), F(20, 'ExtraBold'), NAVY, 'mm', False)
            blit(c, x, 195, 480, 150, al * p, card, (1 - p) * 40)
    # ---- D
    al, a = vis('D', t)
    if al > 0:
        def trk(d):
            for i in range(5):
                on = t >= D_ITEMS[i][2] - 0.02
                cx = W/2 + (i - 2) * 56
                circ(d, 20+cx-W/2+W/2-20, 15, 14, fill=(*TEAL, 255) if on else (255, 255, 255, 70))
        blit(c, 0, 105, W, 40, al, lambda d: [circ(d, W/2 + (i-2)*54, 18, 13, fill=(*TEAL,255) if t >= D_ITEMS[i][2]-.02 else (255,255,255,80)) for i in range(5)])
        blit(c, 0, 140, W, 60, al, lambda d: tx(d, W/2, 0, 'DOKTOR MALAYSIA SENARAIKAN PUNCA LAIN', F(31, 'ExtraBold'), TEAL, 'ma'))
        for i, (name, kind, t0, t1) in enumerate(D_ITEMS):
            if t < t0 - .02 or t > t1 + .25: continue
            p = anim(t, t0, .4) * (1 - ease((t - t1) / .25)) if t > t1 else anim(t, t0, .4)
            fs = 74
            while tw(name.upper(), F(fs, 'ExtraBold')) > 980: fs -= 4
            blit(c, 0, 195, W, 130, al * p, lambda d, name=name, fs=fs: tx(d, W/2, 8, name.upper(), F(fs, 'ExtraBold'), AMBER if i % 2 == 0 else WHITE, 'ma'), (1-p)*30)
            cx = 175 if i % 2 == 0 else W - 175
            blit(c, cx-130, 410, 260, 260, al * p, lambda d, kind=kind: icon(d, kind, 130, 130, 85 * (0.7 + 0.3*p) + 2*math.sin(t*4), t))
    # ---- E
    head(c, t, 'E', 'SEBAB ITU', [('JANGAN TEKA', 72, WHITE), ('SENDIRI', 88, AMBER)], AMBER)
    side_icon(c, t, 'E', 'ask', True)
    # ---- F
    al, a = vis('F', t)
    if al > 0:
        dy = (1 - anim(t, a, .45)) * 30
        kk, kc = ('LANGKAH SETERUSNYA', TEAL) if t < 35.6 else ('TERUTAMA JIKA:', AMBER)
        blit(c, 0, 105, W, 160, al, lambda d: (pill(d, (W-(tw(kk, F(34))+44))/2, 0, kk, F(34), (*kc, 255), NAVY, 22, 54),
                                                 tx(d, W/2, 62, 'BAWA ANAK JUMPA DOKTOR', F(66, 'ExtraBold'), WHITE, 'ma')), dy)
        side_icon(c, t, 'F', 'plus', True)
        chips = [('BERULANG', 36.3), ('SAKIT KEPALA', 37.9), ('DEMAM', 39.2), ('MATA MERAH', 40.2)]
        fnt = F(28, 'ExtraBold'); gap = 14
        ws = [tw(s, fnt) + 40 for s, _ in chips]; x = (W - sum(ws) - gap * 3) / 2
        for (s, t0), w in zip(chips, ws):
            p = anim(t, t0, .35)
            if p > 0:
                blit(c, x, 262, w, 52, al * p, lambda d, s=s, w=w: (rr(d, 0, 0, w, 52, 26, fill=(*RED, 255)), tx(d, w/2, 26, s, fnt, WHITE, 'mm', False)), (1-p)*14)
            x += w + gap
    # ---- G
    al, a = vis('G', t)
    if al > 0:
        dy = (1 - anim(t, a, .45)) * 24
        names = ['Doctor on Call Malaysia', 'Specialty Vision', 'AllAboutVision']; fnt = F(30, 'Bold')
        ws = [tw(s, fnt) + 32 for s in names]; gap = 14; x = (W - sum(ws) - gap * 2) / 2
        def g1(d): tx(d, W/2, 0, 'SUMBER RUJUKAN', F(36, 'ExtraBold'), TEAL, 'ma')
        blit(c, 0, 125, W, 60, al, g1, dy)
        for s, w in zip(names, ws):
            blit(c, x, 190, w, 54, al, lambda d, s=s, w=w: (rr(d, 0, 0, w, 54, 27, fill=(*NAVY, 235), outline=(*TEAL, 255), width=3), tx(d, w/2, 27, s, fnt, WHITE, 'mm', False)), dy)
            x += w + gap
        blit(c, 0, 258, W, 40, al, lambda d: tx(d, W/2, 0, 'Maklumat umum. Rujuk doktor untuk diagnosis.', F(25, 'SemiBold'), (225, 232, 245), 'ma'), dy)
    return c.resize((W, 760), Image.LANCZOS)

# ---------- subtitle ----------
CAPS = [(0.6,3.4,'Anak silau cahaya matahari sampai rasa tak larat?'),(3.8,5.1,'Jangan agak-agak.'),
 (5.5,9.95,'Silau atau sensitif cahaya ni bukan penyakit.'),(10.35,12.2,'Ia simptom, tanda ada sesuatu yang berlaku.'),
 (12.55,17.7,'Pada kanak-kanak, punca biasa ialah migrain atau masalah penglihatan yang belum dibetulkan.'),
 (18.04,23.3,'Tapi doktor di Malaysia juga senaraikan punca lain, macam mata merah berjangkit,'),
 (23.67,26.92,'luka pada permukaan mata, radang dalam mata,'),(27.21,29.7,'katarak, dan jangkitan selaput otak.'),
 (30.0,33.18,'Sebab tu jangan teka sendiri.'),(33.45,35.28,'Bawa anak jumpa doktor,'),
 (36.22,41.58,'terutama kalau berulang, atau ada sakit kepala, demam atau mata merah.'),
 (42.37,45.9,'Sumber: Doctor on Call Malaysia; Specialty Vision; AllAboutVision')]
def chunks():
    out = []
    for a, b, s in CAPS:
        ws = s.split(); ch = []; cur = []
        for w in ws:
            if cur and len(' '.join(cur + [w])) > 26: ch.append(' '.join(cur)); cur = []
            cur.append(w)
        if cur: ch.append(' '.join(cur))
        # gabung chunk terakhir pendek
        if len(ch) > 1 and len(ch[-1]) < 8: ch[-2] += ' ' + ch[-1]; ch.pop()
        tot = sum(len(x) for x in ch); t = a
        for x in ch:
            d = (b - a) * len(x) / tot; out.append((t, t + d, x)); t += d
    return out
CH = chunks()
def caption(t):
    for a, b, s in CH:
        if a - .05 <= t < b + .05 or (b <= t < b + .0): return s
    return None
def draw_caption(img, s):
    d = ImageDraw.Draw(img); fnt = ImageFont.truetype(FD + 'Inter-ExtraBold.otf', 58)
    words = s.split(); lines = []; cur = ''
    for w in words:
        if cur and d.textlength(cur + ' ' + w, font=fnt) > 940: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    lines.append(cur)
    y = 1475 - (len(lines) - 1) * 35
    for ln in lines:
        d.text((W/2, y), ln, font=fnt, fill=WHITE, anchor='mm', stroke_width=8, stroke_fill=(8, 12, 28))
        y += 70

# ---------- gradient latar ----------
yy = np.arange(H)[:, None].astype(np.float32)
g_top = np.clip(1 - yy / 560, 0, 1) ** 1.3 * 0.72
g_bot = np.clip((yy - 1330) / 260, 0, 1) * np.clip((1900 - yy) / 200, 0, 1) * 0.35
GRAD = (g_top + g_bot).astype(np.float32)[:, :, None]
NAVYF = np.array(NAVY, np.float32)

def make_seg(model):
    return vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=mpp.BaseOptions(model_asset_path=model), output_confidence_masks=True,
        output_category_mask=False, running_mode=vision.RunningMode.IMAGE))
def person_mask(seg, rgb, prev):
    sm = cv2.resize(rgb, (540, 960), interpolation=cv2.INTER_AREA)
    r = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(sm)))
    m = r.confidence_masks[0].numpy_view()[:, :, 0].astype(np.float32)
    m = np.clip((m - 0.4) / 0.35, 0, 1)
    if prev is not None: m = 0.6 * m + 0.4 * prev
    return m

def compose(rgb, t, m):
    base = rgb.astype(np.float32)
    base = base * (1 - GRAD) + NAVYF * GRAD
    ov = np.asarray(overlay(t)).astype(np.float32)  # 760 x W x 4
    a = ov[:, :, 3:4] / 255.0
    base[:760] = base[:760] * (1 - a) + ov[:, :, :3] * a
    mm = cv2.resize(cv2.GaussianBlur(m, (5, 5), 0), (W, H), interpolation=cv2.INTER_LINEAR)[:, :, None]
    out = base * (1 - mm) + rgb.astype(np.float32) * mm
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    s = caption(t)
    if s: draw_caption(img, s)
    return img

def main():
    src, dst = sys.argv[1], sys.argv[2]
    stills = None
    if '--stills' in sys.argv: stills = [float(x) for x in sys.argv[sys.argv.index('--stills') + 1].split(',')]
    seg = make_seg('work/seg.tflite')
    cap = cv2.VideoCapture(src)
    if stills:
        for t in stills:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read()
            rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            m = person_mask(seg, rgb, None)
            compose(rgb, t, m).resize((540, 960), Image.LANCZOS).save(f'work/still_{t:05.1f}.png')
        return
    audio = ['-af', 'loudnorm=I=-14:TP=-1.5:LRA=11']
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', src, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                          *audio, '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', dst], stdin=subprocess.PIPE)
    prev = None; n = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        t = n / FPS
        rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        prev = person_mask(seg, rgb, prev)
        p.stdin.write(np.asarray(compose(rgb, t, prev)).tobytes()); n += 1
        if n % 90 == 0: print('frame', n, flush=True)
    p.stdin.close(); p.wait()

if __name__ == '__main__':
    main()
