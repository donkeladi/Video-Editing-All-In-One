#!/usr/bin/env python3
"""Bina video aktiviti 2 kamera (A=visual+audio, B=visual sahaja) -> 9:16 HD, SATU kali kod (tiada generasi perantaraan).

Input : work/edl.json  [{"f0","f1","cam","z","cx","cy"}]  (bingkai 30fps pada garis masa A)
        work/fx.json   {"sfx":[{"t","file","vol"}]}      work/subs.ass
Output: output/aktiviti_tiktok.mp4  libx264 slow CRF15, aac 256k, -14 LUFS, warna bt709 dikekalkan
Video & audio dipotong dengan sempadan bingkai/sampel yang sama (44100/30 = 1470 sampel setiap bingkai) -> sync tepat.
Env: CRF, PRESET, OUT, LIMIT (hanya N shot pertama, untuk ujian pantas)
"""
import json, os, subprocess as sp, sys

W, H, FPS, SPF = 1080, 1920, 30, 1470
os.makedirs("output", exist_ok=True)
CRF = os.environ.get("CRF", "15")
PRESET = os.environ.get("PRESET", "slow")
OUT = os.environ.get("OUT", "output/aktiviti_tiktok.mp4")


def size(cam):
    o = sp.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                         "stream=width,height", "-of", "csv=p=0", f"input/{cam}.mp4"], text=True).strip()
    return tuple(map(int, o.split(",")))


SIZE = {c: size(c) for c in "AB"}
edl = json.load(open("work/edl.json"))
if os.environ.get("LIMIT"): edl = edl[:int(os.environ["LIMIT"])]
fx = json.load(open("work/fx.json")) if os.path.exists("work/fx.json") else {}
N = len(edl)
idx = {"A": [i for i, e in enumerate(edl) if e["cam"] == "A"], "B": [i for i, e in enumerate(edl) if e["cam"] == "B"]}

fc = []
for k, cam in enumerate("AB"):        # pecah aliran sumber (A=input 0, B=input 1)
    if idx[cam]:
        fc.append(f"[{k}:v]split={len(idx[cam])}" + "".join(f"[s{cam}{j}]" for j in range(len(idx[cam]))))
for i, e in enumerate(edl):
    cam = e["cam"]; sw, sh = SIZE[cam]; z = e["z"]
    cw = sw / z; ch = cw * H / W
    if ch > sh: ch = sh; cw = ch * W / H
    cx = min(max(e["cx"] * sw - cw / 2, 0), sw - cw); cy = min(max(e["cy"] * sh - ch / 2, 0), sh - ch)
    lab = f"s{cam}{idx[cam].index(i)}"
    dn = "hqdn3d=1.5:1.2:3:2.5," if z > 1.0 else ""            # denoise ringan sebelum naik skala (kurangkan blok)
    fc.append(f"[{lab}]trim=start_frame={e['f0']}:end_frame={e['f1']},setpts=PTS-STARTPTS,{dn}"
              f"crop={round(cw)}:{round(ch)}:{round(cx)}:{round(cy)},scale={W}:{H}:flags=lanczos,setsar=1[v{i}]")
fc.append("".join(f"[v{i}]" for i in range(N)) + f"concat=n={N}:v=1:a=0[vc]")
vlast = "[vc]"
if os.path.exists("work/subs.ass"):
    fc.append("[vc]ass=work/subs.ass[vout]"); vlast = "[vout]"

# audio dari A, dipotong ikut sempadan sampel yang sama; fade 10ms hanya di lompatan sebenar
fc.append(f"[0:a]asplit={N}" + "".join(f"[x{i}]" for i in range(N)))
for i, e in enumerate(edl):
    n = e["f1"] - e["f0"]; f = []
    if i > 0 and edl[i - 1]["f1"] != e["f0"]: f.append("afade=t=in:st=0:d=0.01")
    if i < N - 1 and edl[i + 1]["f0"] != e["f1"]: f.append(f"afade=t=out:st={n / FPS - 0.01:.4f}:d=0.01")
    fc.append(f"[x{i}]atrim=start_sample={e['f0'] * SPF}:end_sample={e['f1'] * SPF},asetpts=PTS-STARTPTS"
              + ("," + ",".join(f) if f else "") + f"[p{i}]")
fc.append("".join(f"[p{i}]" for i in range(N)) + f"concat=n={N}:v=0:a=1[abase]")

starts = []; acc = 0                  # peta masa A -> masa output
for e in edl: starts.append(acc); acc += e["f1"] - e["f0"]


def to_out(t):
    f = t * FPS
    for e, s in zip(edl, starts):
        if e["f0"] <= f <= e["f1"]: return (s + f - e["f0"]) / FPS
    return None


inputs = ["-i", "input/A.mp4", "-i", "input/B.mp4"]
mix = ["[abase]"]
for sfx in fx.get("sfx", []):
    ot = to_out(sfx["t"])
    if ot is None: continue
    inputs += ["-i", sfx["file"]]
    k = len(inputs) // 2 - 1
    ms = int(ot * 1000)
    fc.append(f"[{k}:a]adelay={ms}|{ms},volume={sfx.get('vol', .8)}[s{k}]"); mix.append(f"[s{k}]")
fc.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")

open("work/fc.txt", "w").write(";\n".join(fc))
cmd = ["ffmpeg", "-y", *inputs, "-filter_complex_script", "work/fc.txt", "-map", vlast, "-map", "[aout]",
       "-r", str(FPS), "-c:v", "libx264", "-preset", PRESET, "-crf", CRF, "-profile:v", "high", "-pix_fmt", "yuv420p",
       "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
       "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", OUT]
r = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE, text=True)
if r.returncode: sys.exit(r.stderr[-2500:])
print("siap ->", OUT)
