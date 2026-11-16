#!/usr/bin/env python3
"""Transkrip tempatan (faster-whisper) dengan timestamp setiap perkataan. Guna: transcribe_local.py in.wav out.json [bahasa]"""
import sys, json, wave, numpy as np
from faster_whisper import WhisperModel
wf=wave.open(sys.argv[1]); a=np.frombuffer(wf.readframes(wf.getnframes()),np.int16).astype(np.float32)/32768
m=WhisperModel(sys.argv[4] if len(sys.argv)>4 else 'small',compute_type='int8')
seg,_=m.transcribe(a,language=(sys.argv[3] if len(sys.argv)>3 else 'ms'),word_timestamps=True,
  initial_prompt='Video Bahasa Melayu santai, ada sebutan English: screen time, blue light, social media, 20-20-20.')
W=[(round(w.start,2),round(w.end,2),w.word.strip()) for s in seg for w in s.words]
json.dump(W,open(sys.argv[2],'w'),ensure_ascii=False)
for w in W: print(w)
