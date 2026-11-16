#!/usr/bin/env python3
"""Transkrip ketepatan lebih tinggi (model medium + petunjuk kosa kata) -> work/A2.json"""
import sys, json, subprocess, numpy as np
from faster_whisper import WhisperModel
raw = subprocess.run(["ffmpeg","-v","error","-i","work/A.mp3","-f","f32le","-ac","1","-ar","16000","-"],capture_output=True,check=True).stdout
aud = np.frombuffer(raw, np.float32)
m = WhisperModel(sys.argv[1] if len(sys.argv)>1 else "medium", device="cpu", compute_type="int8")
prompt = "Hai, hari ini Hasha dengan Bijak nak buat chemistry challenge. Satu, dua, tiga. Warna merah. Pokok. Kereta. Kayu. Api. Takut. Okey, next. Tak apa, kita try lagi. Korang boleh komen kat bawah."
segs,_ = m.transcribe(aud, language="ms", word_timestamps=True, vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=300, threshold=0.35), beam_size=5, initial_prompt=prompt, condition_on_previous_text=False)
out=[{"start":s.start,"end":s.end,"text":s.text.strip(),"words":[{"w":w.word,"s":w.start,"e":w.end} for w in s.words]} for s in segs]
json.dump(out, open("work/A2.json","w"), ensure_ascii=False, indent=1)
for s in out: print(f"{s['start']:7.2f} {s['end']:7.2f} {s['text']}")
