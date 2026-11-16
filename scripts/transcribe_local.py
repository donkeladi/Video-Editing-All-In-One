#!/usr/bin/env python3
"""Transkrip lokal (faster-whisper) -> JSON perkataan + SRT. Guna: transcribe_local.py work/A.mp3 [lang]"""
import sys, json, subprocess, numpy as np
from faster_whisper import WhisperModel
p=sys.argv[1]; lang=sys.argv[2] if len(sys.argv)>2 else "ms"
m=WhisperModel("small",device="cpu",compute_type="int8")
raw=subprocess.run(["ffmpeg","-v","error","-i",p,"-f","f32le","-ac","1","-ar","16000","-"],capture_output=True,check=True).stdout
aud=np.frombuffer(raw,np.float32)
segs,info=m.transcribe(aud,language=lang,word_timestamps=True,vad_filter=True,beam_size=5)
out=[]
for s in segs:
    out.append({"start":s.start,"end":s.end,"text":s.text.strip(),"words":[{"w":w.word,"s":w.start,"e":w.end} for w in s.words]})
json.dump(out,open(p.rsplit(".",1)[0]+".json","w"),ensure_ascii=False,indent=1)
for s in out: print(f"{s['start']:7.2f} {s['end']:7.2f} {s['text']}")
