#!/usr/bin/env bash
# Buang bahagian senyap. Guna: cut_silence.sh in.mp4 [noise_dB=-35] [min_sec=0.4]
set -euo pipefail
in="$1"; db="${2:--35}"; d="${3:-0.4}"
mkdir -p output
python3 - "$in" "$db" "$d" <<'PY'
import subprocess, re, sys, os
inp, db, d = sys.argv[1], sys.argv[2], float(sys.argv[3])
log = subprocess.run(["ffmpeg","-i",inp,"-af",f"silencedetect=noise={db}dB:d={d}","-f","null","-"],capture_output=True,text=True).stderr
h,m,s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", log).groups(); dur = int(h)*3600+int(m)*60+float(s)
starts=[float(x) for x in re.findall(r"silence_start: ([\d.]+)",log)]
ends=[float(x) for x in re.findall(r"silence_end: ([\d.]+)",log)]
keep=[]; t=0.0
for i,s0 in enumerate(starts):
    if s0-t>0.05: keep.append((t,s0))
    t = ends[i] if i<len(ends) else dur
if dur-t>0.05: keep.append((t,dur))
pad=0.08
sel="+".join(f"between(t,{max(a-pad,0):.3f},{b+pad:.3f})" for a,b in keep)
out=os.path.join("output",os.path.basename(inp).rsplit(".",1)[0]+"_cut.mp4")
subprocess.run(["ffmpeg","-y","-i",inp,"-vf",f"select='{sel}',setpts=N/FRAME_RATE/TB","-af",f"aselect='{sel}',asetpts=N/SR/TB","-c:v","libx264","-crf","18","-c:a","aac","-b:a","192k",out],check=True)
print(out)
PY
