"""ASR setempat (faster-whisper small) -> masa perkataan + semakan kejelasan VO."""
import json, pathlib, re, difflib, subprocess
import numpy as np
from faster_whisper import WhisperModel
ROOT = pathlib.Path(__file__).resolve().parent.parent
lines = json.loads((ROOT/"docs/vo-lines.json").read_text())
m = WhisperModel(str(ROOT/"models/whisper-small"), device="cpu", compute_type="int8")
norm = lambda s: re.sub(r"[^a-z0-9 ]","",s.lower()).split()
res = {}
for lid in lines:
    raw = subprocess.run(["ffmpeg","-v","error","-i",str(ROOT/f"work/vo/clean/{lid}.wav"),"-f","f32le","-ac","1","-ar","16000","-"],capture_output=True,check=True).stdout
    audio = np.frombuffer(raw, dtype=np.float32)
    segs, info = m.transcribe(audio, language="ms", word_timestamps=True, beam_size=5)
    words = [(w.word.strip(), round(w.start,3), round(w.end,3)) for s in segs for w in s.words]
    hyp = norm(" ".join(w[0] for w in words)); ref = norm(lines[lid])
    sim = difflib.SequenceMatcher(None, ref, hyp).ratio()
    res[lid] = {"words": words, "similarity": round(sim,3), "hyp": " ".join(hyp), "ref": " ".join(ref)}
    print(lid, f"similarity={sim:.2f}\n  ref: {' '.join(ref)}\n  asr: {' '.join(hyp)}")
(ROOT/"work/vo/align.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
