"""Jump-cut: buang jeda panjang berdasarkan tenaga audio. Guna: jumpcut_words.py in.mov out.mp4 map.json"""
import sys,json,subprocess,numpy as np
src,dst,mp=sys.argv[1:4]
START,END,THR,MINGAP,KEEP=0.88,76.0,-40,0.22,0.12
a=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',src,'-f','s16le','-ac','1','-ar','16000','-']),np.int16).astype(float)/32768
h=160;n=len(a)//h
db=20*np.log10(np.sqrt((a[:n*h].reshape(n,h)**2).mean(1))+1e-6)
low=db<THR;gaps=[];i=0
while i<n:
    if low[i]:
        j=i
        while j<n and low[j]:j+=1
        if (j-i)*.01>=MINGAP and i*.01>START and j*.01<END: gaps.append((i*.01,j*.01))
        i=j
    else:i+=1
keep=[];t=START
for g0,g1 in gaps:
    keep.append((t,g0+KEEP/2)); t=g1-KEEP/2
keep.append((t,END))
fc=[];cat=''
F=0.012
for k,(s,e) in enumerate(keep):
    d=e-s
    fc.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS[v{k}]")
    fc.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,afade=t=in:d={F},afade=t=out:st={d-F:.3f}:d={F}[a{k}]")
    cat+=f"[v{k}][a{k}]"
fc.append(f"{cat}concat=n={len(keep)}:v=1:a=1[v][a]")
subprocess.check_call(['ffmpeg','-y','-v','error','-i',src,'-filter_complex',';'.join(fc),'-map','[v]','-map','[a]','-r','30','-c:v','libx264','-crf','18','-preset','medium','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',dst])
m=[];o=0
for s,e in keep: m.append({'src':s,'end':e,'out':o});o+=e-s
json.dump({'segments':m,'duration':o},open(mp,'w'),indent=1)
print(len(keep),'segmen; durasi baru %.2fs (asal 77.93s)'%o)
