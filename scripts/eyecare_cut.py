#!/usr/bin/env python3
"""Potong jeda senyap (kekalkan ~0.2s) + buang retake. Guna: eyecare_cut.py in.mov out.mp4"""
import subprocess, re, sys
inp, out = sys.argv[1], sys.argv[2]
START, END = 1.85, 62.85          # buang bunyi awal & hujung
CUTS = [(46.36, 48.00)]           # retake "dia ada MAL," (diulang)
KEEP = 0.10                       # jeda dikekalkan di setiap sisi
log = subprocess.run(["ffmpeg","-i",inp,"-af","silencedetect=noise=-35dB:d=0.4","-f","null","-"],capture_output=True,text=True).stderr
ss=[float(x) for x in re.findall(r"silence_start: ([\d.]+)",log)]
se=[float(x) for x in re.findall(r"silence_end: ([\d.]+)",log)]
rm=list(CUTS)
for a,b in zip(ss,se):
    if a>START and b<END and b-a>2*KEEP+0.1: rm.append((a+KEEP,b-KEEP))
rm.sort()
keep=[];t=START
for a,b in rm:
    if a>t: keep.append((t,a))
    t=max(t,b)
keep.append((t,END))
print(keep)
v="".join(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.01:.3f}:d=0.01[a{i}];" for i,(a,b) in enumerate(keep))
cat="".join(f"[v{i}][a{i}]" for i in range(len(keep)))+f"concat=n={len(keep)}:v=1:a=1[v][a]"
subprocess.run(["ffmpeg","-y","-v","error","-i",inp,"-filter_complex",v+cat,"-map","[v]","-map","[a]","-r","30","-c:v","libx264","-crf","16","-preset","fast","-c:a","aac","-b:a","192k",out],check=True)
