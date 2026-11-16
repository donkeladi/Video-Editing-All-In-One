#!/usr/bin/env python3
"""Potong bahagian senyap/tak perlu (video kelip mata). Guna: blink_cut.py src.mov work/blink"""
import subprocess, sys, json, os
src, wd = sys.argv[1], sys.argv[2]
DUR = 42.933
REMOVE = [(3.12,3.30),(13.30,14.08),(35.30,35.50),(36.05,36.70),(37.61,37.91),(40.20,40.38),(41.40,DUR)]
keep=[]; t=0.0
for a,b in REMOVE:
    if a>t: keep.append((t,a))
    t=b
if t<DUR: keep.append((t,DUR))
json.dump({"keep":keep}, open(os.path.join(wd,"cuts.json"),"w"))
v="".join(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b-a-0.012:.3f}:d=0.012[a{i}];" for i,(a,b) in enumerate(keep))
v+="".join(f"[v{i}][a{i}]" for i in range(len(keep)))+f"concat=n={len(keep)}:v=1:a=1[v][a]"
subprocess.run(["ffmpeg","-y","-v","error","-i",src,"-filter_complex",v,"-map","[v]","-map","[a]","-r","30","-c:v","libx264","-crf","10","-preset","fast","-c:a","pcm_s16le",os.path.join(wd,"cut.mov")],check=True)
print(keep)
