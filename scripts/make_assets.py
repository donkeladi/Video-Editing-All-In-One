#!/usr/bin/env python3
"""Jana SFX (numpy) dan sticker meme (PIL) -> assets/sfx/*.wav, assets/memes/*.png. Tiada kredit digunakan."""
import os, wave, numpy as np
from PIL import Image, ImageDraw, ImageFont

SR = 44100
os.makedirs("assets/sfx", exist_ok=True)
os.makedirs("assets/memes", exist_ok=True)
rng = np.random.default_rng(7)


def T(d): return np.arange(int(SR * d)) / SR


def save(name, y, peak=0.9):
    y = y / (np.abs(y).max() + 1e-9) * peak
    with wave.open(f"assets/sfx/{name}.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype("<i2").tobytes())


def hp(x, a=0.95):  # high-pass kasar
    y = np.zeros_like(x); p = 0; q = 0
    for i, v in enumerate(x):
        y[i] = a * (y[i - 1] + v - q) if i else v; q = v
    return y


# boom (vine-boom)
t = T(1.4); f = 35 + 60 * np.exp(-t * 9)
boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2) + 0.5 * rng.standard_normal(len(t)) * np.exp(-t * 28)
save("boom", boom)
# boing
t = T(0.8); f = 260 + 520 * np.exp(-t * 5) + 40 * np.sin(2 * np.pi * 22 * t)
save("boing", np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5))
# air horn
t = T(1.1); y = 0
for f0 in (440, 554, 659):
    for k in (1, 2, 3, 4):
        y = y + np.sin(2 * np.pi * f0 * k * t * (1 + 0.003 * np.sin(2 * np.pi * 6 * t))) / k
env = np.minimum(t / 0.03, 1) * np.minimum((1.1 - t) / 0.2, 1)
save("airhorn", y * env)
# ba dum tss
t = T(1.6); y = np.zeros_like(t)
for st in (0.0, 0.2):
    m = t >= st; tt = (t - st)[m]
    y[m] += np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 14)
m = t >= 0.5; tt = (t - 0.5)[m]
y[m] += 0.45 * hp(rng.standard_normal(len(tt))) * np.exp(-tt * 3.2)
save("badumtss", y)
# ding
t = T(1.4)
save("ding", (np.sin(2 * np.pi * 988 * t) + 0.5 * np.sin(2 * np.pi * 1976 * t) + 0.25 * np.sin(2 * np.pi * 2960 * t)) * np.exp(-t * 3.5))
# sad trombone
y = np.zeros(int(SR * 2.2)); pos = 0
for f0, d in ((233, .45), (220, .45), (208, .45), (196, .85)):
    t = T(d); fr = f0 * (1 + 0.02 * np.sin(2 * np.pi * 5 * t)) * (1 - (0.08 * (t / d) if f0 == 196 else 0))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    s = sum(np.sin(ph * k) / k for k in range(1, 7)) * np.minimum(t / 0.05, 1) * np.minimum((d - t) / 0.06, 1)
    y[pos:pos + len(t)] += s; pos += len(t)
save("sadtrombone", y)
# record scratch
t = T(0.55); f = 900 * np.exp(-t * 3) + 200
save("scratch", (hp(rng.standard_normal(len(t))) * 0.6 + np.sin(2 * np.pi * np.cumsum(f * (1 + .5 * np.sin(40 * t))) / SR)) * np.exp(-t * 4))
# pop
t = T(0.14); save("pop", np.sin(2 * np.pi * np.cumsum(500 + 1800 * t / 0.14) / SR) * np.exp(-t * 30))
# whoosh
t = T(0.45); n = rng.standard_normal(len(t)); k = 1 + (np.sin(np.pi * t / 0.45)) * 30
y = np.convolve(n, np.ones(8) / 8, "same") * np.sin(np.pi * t / 0.45) ** 2
save("whoosh", y, 0.7)

# ---- sticker meme ----
INTER = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"


def emoji_img(e, size=220):
    im = Image.new("RGBA", (136 * len(e), 128), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), e, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    bb = im.getbbox() or (0, 0, 1, 1); im = im.crop(bb)
    return im.resize((int(im.width * size / im.height), size), Image.LANCZOS)


def sticker(name, text, emo, fill=(255, 255, 255), rot=0):
    W = 960; f = ImageFont.truetype(INTER, 118)
    lines = text.split("\n"); im = Image.new("RGBA", (W, 560), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    e = emoji_img(emo, 210); im.alpha_composite(e, ((W - e.width) // 2, 0))
    y = 235
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text(((W - w) / 2, y), ln, font=f, fill=fill, stroke_width=14, stroke_fill=(0, 0, 0))
        y += 135
    im = im.crop(im.getbbox()); pad = 30
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0)); out.alpha_composite(im, (pad, pad))
    if rot: out = out.rotate(rot, resample=Image.BICUBIC, expand=True)
    out.save(f"assets/memes/{name}.png")


YEL = (255, 232, 60)
sticker("haha", "AHAHAHA", "😂🤣😂", rot=-4)
sticker("wah", "WAH GILA!", "🔥😱", YEL, rot=3)
sticker("serius", "SERIUS KE??", "😳", rot=-3)
sticker("bruh", "BRUHHH", "💀💀💀", YEL, rot=4)
sticker("malu", "MALU AKU", "🙈", rot=-3)
sticker("ngapa", "NGAPA TU?", "😭😭", YEL, rot=3)
sticker("loading", "OTAK\nLOADING...", "🧠", rot=-4)
sticker("genius", "GENIUS!", "🤓☝️", YEL, rot=3)
sticker("siapatanya", "SIAPA TANYA?", "🤨", rot=-3)
sticker("takut", "ADA TAKUT!!", "😱", YEL, rot=4)
sticker("kayuapi", "KAYU API!", "🪵🔥", rot=-3)
sticker("sigma", "SIGMA MOVE", "😎", YEL, rot=3)
sticker("noway", "NO WAY", "😳🤯", rot=-4)
sticker("mati", "MATI AKU", "☠️😂", YEL, rot=3)
sticker("lagi", "TRY LAGI!", "💪", rot=-3)
print("siap:", sorted(os.listdir("assets/sfx")), sorted(os.listdir("assets/memes")))
