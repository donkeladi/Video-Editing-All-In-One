#!/usr/bin/env python3
"""Anggar masa perkataan tanpa ASR: kesan chunk ucapan (silencedetect) lalu agih perkataan skrip
ke chunk secara DP (suku kata ≈ tempoh). Output JSON [{w,start,end}].
Guna: align_script.py <video> <script.txt> <out.json>   (anggaran — ganti dengan ElevenLabs bila ada transkrip)"""
import sys, re, json, subprocess
vid, scr, out = sys.argv[1:4]
r = subprocess.run(['ffmpeg','-hide_banner','-i',vid,'-af','silencedetect=noise=-30dB:d=0.15','-f','null','-'],capture_output=True,text=True).stderr
st=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',r)]; en=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',r)]
dur=float(re.search(r'time=(\d+):(\d+):([\d.]+)',r.split('\n')[-2] if False else r).group(0).split('=')[1].split(':')[2]) if False else None
# chunk ucapan = antara silence_end[i] → silence_start[i+1]
chunks=[]; 
starts=[0.0]+en          # permulaan ucapan
ends=st+[None]
for a,b in zip(starts,ends):
    pass
# silence pertama bermula ~0 → ucapan bermula pada en[0]
sp=[(en[i], st[i+1]) for i in range(len(en)-1) if i+1<len(st)]
sp=[(a,b) for a,b in sp if b-a>0.12]
words=re.findall(r"\S+",open(scr).read())
NUM={'89.9%':'lapan puluh sembilan perpuluhan sembilan peratus','8':'lapan','20':'dua puluh'}
def syl(w):
    w=NUM.get(w.strip('.,:;?!'),w).lower()
    return max(1,len(re.findall(r'[aeiou]+',w)))
S=[syl(w) for w in words]
n,m=len(words),len(sp); D=[b-a for a,b in sp]
tot=sum(S); rate=tot/sum(D)
import functools
@functools.lru_cache(None)
def f(i,j):   # words[i:] ke chunks[j:]
    if j==m: return (0,()) if i==n else (1e9,())
    best=(1e9,())
    for k in range(i,n+1):
        c=sum(S[i:k]); cost=((D[j]-c/rate)/max(D[j],0.3))**2*D[j]
        if k==i: cost=0.5+D[j]*0  # chunk kosong (penalti)
        if k>i and k<n and words[k-1][-1] not in ',.:?!': cost+=0.6
        sub=f(k,j+1)
        if cost+sub[0]<best[0]: best=(cost+sub[0],(k,)+sub[1])
    return best
cuts=f(0,0)[1]; i=0; res=[]
for j,k in enumerate(cuts):
    ws=words[i:k]; a,b=sp[j]; tot_s=sum(S[i:k]) or 1; t=a
    for w,s_ in zip(ws,S[i:k]):
        d=(b-a)*s_/tot_s; res.append(dict(w=w,start=round(t,3),end=round(t+d,3))); t+=d
    i=k
json.dump(dict(words=res,chunks=sp),open(out,'w'),ensure_ascii=False,indent=0)
print(len(res),'perkataan,',len(sp),'chunk, kadar',round(rate,2),'suku kata/s')
for j,(a,b) in enumerate(sp): print(f"{a:6.2f}-{b:6.2f}",' '.join(w['w'] for w in res if a-1e-3<=w['start']<b))
