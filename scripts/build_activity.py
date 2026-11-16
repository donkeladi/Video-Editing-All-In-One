#!/usr/bin/env python3
"""Bina video aktiviti 2 kamera (A=audio+visual, B=visual sahaja) -> 9:16 TikTok.

Input  : work/edl.json  = [{"t0":..,"t1":..,"cam":"A"|"B","z":1.0,"cx":0.5,"cy":0.4}, ...]
                          (masa ikut garis masa A; z=zoom, cx/cy=pusat crop 0..1)
         work/fx.json   = {"memes":[{"t":..,"d":..,"png":"assets/memes/x.png","x":..,"y":..,"w":..}],
                           "sfx":[{"t":..,"file":"assets/sfx/x.wav","vol":0.8}],
                           "mute":[[t0,t1],...]}            (senyapkan suara videographer)
         work/subs.ass  (pilihan)
Output : output/aktiviti_tiktok.mp4   (libx264 CRF18, aac 192k, -14 LUFS)
Audio sentiasa dari A, dipotong ikut EDL yang sama supaya kekal sync.
"""
import json, os, subprocess as sp, sys

W, H, FPS = 1080, 1920, 30
SEG = "work/seg"
os.makedirs(SEG, exist_ok=True)
os.makedirs("output", exist_ok=True)


def run(*a):
    r = sp.run(a, stdout=sp.PIPE, stderr=sp.PIPE, text=True)
    if r.returncode:
        sys.exit(r.stderr[-1500:])


def probe(cam):
    o = sp.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                         "stream=width,height", "-of", "csv=p=0", f"input/{cam}.mp4"], text=True).strip()
    w, h = map(int, o.split(","))
    return w, h


SIZE = {c: probe(c) for c in "AB"}
edl = json.load(open("work/edl.json"))
fx = json.load(open("work/fx.json")) if os.path.exists("work/fx.json") else {}

# 1. render tiap shot (video dari kamera dipilih, audio dari A)
parts = []
REUSE = "--reuse" in sys.argv
for i, s in enumerate(edl):
    sw, sh = SIZE[s["cam"]]
    z = s.get("z", 1.0)
    cw = sw / z
    ch = cw * H / W
    if ch > sh:
        ch = sh
        cw = ch * W / H
    cx = min(max(s.get("cx", .5) * sw - cw / 2, 0), sw - cw)
    cy = min(max(s.get("cy", .5) * sh - ch / 2, 0), sh - ch)
    out = f"{SEG}/{i:03d}.mp4"
    d = s["t1"] - s["t0"]
    vf = f"crop={cw:.0f}:{ch:.0f}:{cx:.0f}:{cy:.0f},scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1,format=yuv420p"
    if not REUSE:
        run("ffmpeg", "-y", "-ss", f"{s['t0']:.3f}", "-t", f"{d:.3f}", "-i", f"input/{s['cam']}.mp4",
            "-an", "-frames:v", str(round(d * FPS)), "-vf", vf, "-c:v", "libx264", "-crf", "16", "-preset", "fast", out)
    parts.append(out)

lst = f"{SEG}/list.txt"
open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
if not REUSE:
    run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "work/base.mp4")

# peta masa asal -> masa output (untuk letak meme/sfx/mute)
tmap = []
acc = 0.0
for s in edl:
    tmap.append((s["t0"], s["t1"], acc))
    acc += s["t1"] - s["t0"]


def to_out(t):
    for a, b, o in tmap:
        if a <= t <= b:
            return o + t - a
    return None


# 2. overlay meme + subtitle
inputs = ["-i", "work/base.mp4", "-i", "input/A.mp4"]
chain = []
last = "[0:v]"
n = 2
for m in fx.get("memes", []):
    ot = to_out(m["t"])
    if ot is None:
        continue
    inputs += ["-loop", "1", "-t", f"{m['d']:.2f}", "-i", m["png"]]
    lbl = f"[v{n}]"
    chain.append(f"[{n}:v]scale={m.get('w', 500)}:-1,format=rgba,fade=t=in:st=0:d=0.1:alpha=1,"
                 f"setpts=PTS-STARTPTS+{ot:.3f}/TB[m{n}]")
    chain.append(f"{last}[m{n}]overlay={m.get('x', '(W-w)/2')}:{m.get('y', 300)}:"
                 f"enable='between(t,{ot:.3f},{ot + m['d']:.3f})':eof_action=pass{lbl}")
    last = lbl
    n += 1
if os.path.exists("work/subs.ass"):
    chain.append(f"{last}ass=work/subs.ass[vout]")
    last = "[vout]"

# 3. audio: mute videographer + sfx + loudnorm
achain = [f"[1:a]atrim={e['t0']:.3f}:{e['t1']:.3f},asetpts=PTS-STARTPTS[p{i}]" for i, e in enumerate(edl)]
achain.append("".join(f"[p{i}]" for i in range(len(edl))) + f"concat=n={len(edl)}:v=0:a=1[abase]")
a_last = "[abase]"
mutes = [to_out(a) for a, b in fx.get("mute", [])]
for (a, b) in fx.get("mute", []):
    oa, ob = to_out(a), to_out(b)
    if oa is None or ob is None:
        continue
    achain.append(f"{a_last}volume=enable='between(t,{oa:.3f},{ob:.3f})':volume=0[am{len(achain)}]")
    a_last = f"[am{len(achain) - 1}]"
amix_in = [a_last]
for sfx in fx.get("sfx", []):
    ot = to_out(sfx["t"])
    if ot is None:
        continue
    inputs += ["-i", sfx["file"]]
    idx = len(inputs.count("-i") * [0]) + 0
    k = inputs.count("-i") - 1
    ms = int(ot * 1000)
    achain.append(f"[{k}:a]adelay={ms}|{ms},volume={sfx.get('vol', .8)}[s{k}]")
    amix_in.append(f"[s{k}]")
achain.append("".join(amix_in) + f"amix=inputs={len(amix_in)}:normalize=0:duration=first,"
              "loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

open("work/fc.txt", "w").write(";".join(chain + achain))
cmd = ["ffmpeg", "-y", *inputs, "-filter_complex_script", "work/fc.txt", "-map", last, "-map", "[aout]",
       "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "output/aktiviti_tiktok.mp4"]
run(*cmd)
print("siap -> output/aktiviti_tiktok.mp4")
