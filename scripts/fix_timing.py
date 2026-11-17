#!/usr/bin/env python3
"""ASR (asr_np.json) → betulkan ejaan, gabung token, snap permulaan perkataan ke onset ucapan (silencedetect).
Guna: fix_timing.py <video> <asr.json> <out timing.json>"""
import sys, re, json, subprocess
vid, asr, out = sys.argv[1:4]
W=json.load(open(asr))
REP={'ini':'ni','konsis':'kongsi','simpter':'simptom','screen.':'skrin.','Street':'Straits','Tan':'Times','Pulak':'pulak','Lapo':'lapor,',
 'Matahari':'Mata','kering':'kering,','pedeh':'pedih,','kabur':'kabur.','familiar':'Familiar','menit':'minit','Palmer':'Pharma','routing.':'rutin.','saja':'je','sekurang':'sekurang-kurangnya'}
res=[]
for x in W:
    w=x['w']
    if w in ('video','-kurangnya','%','-89'): continue
    if w=='saya' and 27<x['start']<28.5: continue
    if w=='89': res.append(dict(w='89.9%',start=x['start'],end=12.2)); continue
    res.append(dict(w=REP.get(w,w),start=x['start'],end=x['end']))
# snap ke onset ucapan
r=subprocess.run(['ffmpeg','-hide_banner','-i',vid,'-af','silencedetect=noise=-30dB:d=0.15','-f','null','-'],capture_output=True,text=True).stderr
ons=[float(v) for v in re.findall(r'silence_end: ([\d.]+)',r)]
for s in ons:
    c=min(res,key=lambda x:abs(x['start']-s))
    if abs(c['start']-s)<=0.4: c['start']=s
# intro: "ni" bermula selepas jeda 3.56
for x in res:
    if x['w']=='ni': x['start']=3.58
    if x['w']=='Student,': x['start']=2.4
res.sort(key=lambda x:x['start'])
for a,b in zip(res,res[1:]): a['end']=round(min(a['end'],b['start']) if a['end']>b['start'] else a['end'],3); a['end']=max(a['end'],a['start']+0.12)
json.dump(dict(words=res),open(out,'w'),ensure_ascii=False,indent=0)
print(' '.join(f"{x['w']}[{x['start']:.1f}]" for x in res))
