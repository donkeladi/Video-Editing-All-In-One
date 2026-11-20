#!/usr/bin/env python3
"""Auto-edit: buang senyap, jump-cut dengan dissolve halus, zoom in/out bergilir, subtitle dibakar.
Guna: auto_edit.py <video> <words.json> [corrections.json]
 - words.json: output faster-whisper (work/<nama>.json) dengan word timestamps
 - corrections.json: {"index": "teks pengganti"}  (indeks perkataan; "" = buang)
Output: work/<nama>.srt, work/<nama>.ass, work/<nama>_edit.mp4 (belum normalize audio)
"""
import json, subprocess, sys, os

vid, wj = sys.argv[1], sys.argv[2]
corr = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
name = os.path.splitext(os.path.basename(vid))[0]
FPS, XF, GAP = 30, 0.12, 0.30
PAD_IN, PAD_OUT = 0.12, 0.20
FX, FY = 0.55, 0.35          # titik pivot zoom (muka di atas-tengah)

dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",vid]))
words = [x for s in json.load(open(wj)) for x in s["words"]]
for i, w in enumerate(words):
    w["t"] = corr.get(str(i), w["w"].strip())

# 1) kumpul perkataan jadi segmen bercakap (pisah di jurang >= GAP)
groups, cur = [], [0]
for i in range(1, len(words)):
    if words[i]["s"] - words[i-1]["e"] >= GAP: groups.append(cur); cur = []
    cur.append(i)
groups.append(cur)
segs = []
for k, g in enumerate(groups):
    a = max(words[g[0]]["s"] - PAD_IN, 0)
    b = words[g[-1]]["e"] + (0.35 if k == len(groups)-1 else PAD_OUT)
    segs.append((a, min(b, dur), g))

# 2) garis masa output (xfade overlap XF)
offs, cum = [], 0.0
for i, (a, b, g) in enumerate(segs):
    L = b - a
    if i == 0: offs.append(0.0); cum = L
    else: offs.append(cum - XF); cum += L - XF
total = cum

# 3) zoom bergilir: masuk / keluar dengan paras berbeza supaya cut nampak seperti punch
ZOOMS = [(1.00,1.12),(1.16,1.04),(1.04,1.18),(1.14,1.00),(1.00,1.15),(1.18,1.06)]
vf, af = [], []
for i, (a, b, g) in enumerate(segs):
    z0, z1 = ZOOMS[i % len(ZOOMS)]
    n = max(int(round((b-a)*FPS)), 1)
    z = f"{z0}+({z1}-{z0})*on/{n}"
    vf.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,fps={FPS},scale=2160:3840:flags=bicubic,"
              f"zoompan=z='{z}':x='{FX}*(iw-iw/zoom)':y='{FY}*(ih-ih/zoom)':d=1:s=1080x1920:fps={FPS},setsar=1[v{i}]")
    af.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,aresample=48000[a{i}]")
last = "v0"
for i in range(1, len(segs)):
    vf.append(f"[{last}][v{i}]xfade=transition=fade:duration={XF}:offset={offs[i]:.3f}[x{i}]"); last = f"x{i}"
vlast = last
last = "a0"
for i in range(1, len(segs)):
    af.append(f"[{last}][a{i}]acrossfade=d={XF}:c1=tri:c2=tri[y{i}]"); last = f"y{i}"
alast = last

# 4) subtitle (cue pendek, ikut perkataan sebenar)
cues = []
for si, (a, b, g) in enumerate(segs):
    toks = [(words[i]["t"], words[i]["s"], words[i]["e"]) for i in g if words[i]["t"]]
    chunk = []
    def flush():
        if not chunk: return
        t0 = offs[si] + chunk[0][1] - a
        t1 = offs[si] + chunk[-1][2] - a
        cues.append([t0, t1, " ".join(c[0] for c in chunk)])
        chunk.clear()
    for t, s, e in toks:
        chunk.append((t, s, e))
        txt = " ".join(c[0] for c in chunk)
        if t[-1] in ".?!," or len(chunk) >= 4 or len(txt) >= 26: flush()
    flush()
# sambung cue rapat & elak overlap
for k in range(len(cues)-1):
    if cues[k+1][0] - cues[k][1] < 0.35: cues[k][1] = cues[k+1][0]
    cues[k][1] = min(cues[k][1], cues[k+1][0])
cues[-1][1] = min(cues[-1][1] + 0.2, total)

def ts(t, sep):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02}:{int(m):02}:{int(s):02}{sep}{int(round((s-int(s))*1000)):03}" if int(round((s-int(s))*1000))<1000 else ts(t+0.001,sep)
os.makedirs("work", exist_ok=True); os.makedirs("output", exist_ok=True)
with open(f"work/{name}.srt","w") as f:
    for k,(t0,t1,tx) in enumerate(cues,1): f.write(f"{k}\n{ts(t0,',')} --> {ts(t1,',')}\n{tx}\n\n")
def ats(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60); return f"{int(h)}:{int(m):02}:{s:05.2f}"
with open(f"work/{name}.ass","w") as f:
    f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n"
            "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
            "Style: Default,DejaVu Sans,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,2,2,70,70,430,1\n\n"
            "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    for t0,t1,tx in cues:
        f.write(f"Dialogue: 0,{ats(t0)},{ats(t1)},Default,,0,0,0,,{{\\fad(40,0)\\fscx88\\fscy88\\t(0,120,\\fscx100\\fscy100)}}{tx}\n")

fc = ";".join(vf+af) + f";[{vlast}]ass=work/{name}.ass[vout]"
out = f"work/{name}_edit.mp4"
cmd = ["ffmpeg","-y","-v","error","-stats","-i",vid,"-filter_complex",fc,"-map","[vout]","-map",f"[{alast}]",
       "-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",out]
print(f"{len(segs)} segmen, {total:.1f}s (asal {dur:.1f}s), {len(cues)} cue")
subprocess.run(cmd, check=True); print(out)
