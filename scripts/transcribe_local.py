#!/usr/bin/env python3
"""ASR tempatan (faster-whisper) → JSON perkataan bermasa. Guna: transcribe_local.py <video> <model_dir> <out.json> [prompt.txt]"""
import sys, json, subprocess, numpy as np
from faster_whisper import WhisperModel
vid, md, out = sys.argv[1:4]
prompt = open(sys.argv[4]).read() if len(sys.argv)>4 else None
aud = np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',vid,'-vn','-ac','1','-ar','16000','-f','f32le','-'],capture_output=True).stdout,dtype=np.float32)
m = WhisperModel(md, device='cpu', compute_type='int8')
segs,_ = m.transcribe(aud, language='ms', word_timestamps=True, initial_prompt=prompt, vad_filter=False, beam_size=5)
W=[dict(w=w.word.strip(), start=round(w.start,3), end=round(w.end,3)) for s in segs for w in s.words]
json.dump(W, open(out,'w'), ensure_ascii=False, indent=0)
print(' '.join(f"{x['w']}[{x['start']:.1f}]" for x in W))
