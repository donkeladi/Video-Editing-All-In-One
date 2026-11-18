#!/usr/bin/env python3
"""Rough cut: ambil segmen ucapan terpilih, buang senyap, hflip (video rakaman mod cermin)."""
import subprocess, re, sys
inp, out = sys.argv[1], sys.argv[2]
# segmen yang dikekalkan (saat) - hasil semakan transkrip; buang ambilan cermin 59.9-64.2 & jeda panjang
SEGS = [(0.78,5.10,1),(8.85,26.95,1),(29.00,42.95,1),(43.70,52.95,1),(55.10,60.52,0),(64.62,77.12,1)]  # flag 1 = hflip (klip mirror-selfie); 0 = klip cermin (sudah betul)
DB, MIN_SIL, PAD = -33, 0.32, 0.10
log = subprocess.run(["ffmpeg","-i",inp,"-af",f"silencedetect=noise={DB}dB:d={MIN_SIL}","-f","null","-"],capture_output=True,text=True).stderr
st=[float(x) for x in re.findall(r"silence_start: ([\d.]+)",log)]
en=[float(x) for x in re.findall(r"silence_end: ([\d.]+)",log)]
sil=list(zip(st,en))
keep=[]
for a,b,fl in SEGS:
    t=a
    for s,e in sil:
        if e<=a or s>=b: continue
        s=max(s,a); e=min(e,b)
        if s-t>0.05: keep.append((t,s+PAD,fl))
        t=e-PAD
    if b-t>0.05: keep.append((t,b,fl))
keep=[(max(a,0),b,fl) for a,b,fl in keep if b-a>0.15]
fc=[]; n=len(keep)
for i,(a,b,fl) in enumerate(keep):
    fc.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS{',hflip' if fl else ''}[v{i}];[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={b-a-0.01:.3f}:d=0.01[a{i}]")
fc.append("".join(f"[v{i}][a{i}]" for i in range(n))+f"concat=n={n}:v=1:a=1[v][a]")
open("work/rough.filter","w").write(";".join(fc))
open("work/rough_keep.txt","w").write("\n".join(f"{a:.3f} {b:.3f} {fl}" for a,b,fl in keep))
subprocess.run(["ffmpeg","-y","-i",inp,"-filter_complex_script","work/rough.filter","-map","[v]","-map","[a]","-c:v","libx264","-crf","18","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",out],check=True,stderr=subprocess.DEVNULL)
print(n,"klip", sum(b-a for a,b,_ in keep),"saat")
