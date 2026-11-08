"""Bina VO terbaik: cuba varian ejaan sebutan x seed, pilih ikut kesamaan ASR dengan teks skrin."""
import json, pathlib, re, difflib, subprocess, sys
import numpy as np, soundfile as sf, torch
from transformers import VitsModel, AutoTokenizer
from faster_whisper import WhisperModel
ROOT = pathlib.Path(__file__).resolve().parent.parent
lines = json.loads((ROOT/"docs/vo-lines.json").read_text())
variants = json.loads((ROOT/"docs/vo-tts-variants.json").read_text())
SPEED, SEEDS = 1.12, [11, 12, 13, 14]
tok = AutoTokenizer.from_pretrained(str(ROOT/"models/mms-zlm"))
tts = VitsModel.from_pretrained(str(ROOT/"models/mms-zlm")).eval(); tts.speaking_rate = SPEED
asr = WhisperModel(str(ROOT/"models/whisper-small"), device="cpu", compute_type="int8")
norm = lambda s: re.sub(r"[^a-z0-9 ]","",s.lower()).split()
tmp = ROOT/"work/vo/cand"; tmp.mkdir(parents=True, exist_ok=True)
def clean(src, dst):
    subprocess.run(["ffmpeg","-y","-v","error","-i",str(src),"-af","silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,highpass=f=70,loudnorm=I=-18:TP=-2:LRA=7,aresample=48000","-ac","1",str(dst)],check=True)
def score(path, ref):
    raw = subprocess.run(["ffmpeg","-v","error","-i",str(path),"-f","f32le","-ac","1","-ar","16000","-"],capture_output=True,check=True).stdout
    segs,_ = asr.transcribe(np.frombuffer(raw,dtype=np.float32), language="ms", beam_size=5)
    hyp = norm(" ".join(s.text for s in segs))
    return difflib.SequenceMatcher(None, norm(ref), hyp).ratio(), " ".join(hyp)
chosen = {}
for lid, ref in lines.items():
    best = None
    for vi, text in enumerate(variants.get(lid, [ref])):
        for seed in SEEDS:
            torch.manual_seed(seed)
            with torch.no_grad():
                w = tts(**tok(text.lower(), return_tensors="pt")).waveform[0].numpy()
            raw = tmp/f"{lid}_v{vi}_s{seed}_raw.wav"; sf.write(raw, w, 16000)
            c = tmp/f"{lid}_v{vi}_s{seed}.wav"; clean(raw, c)
            sc, hyp = score(c, ref)
            if best is None or sc > best[0]: best = (sc, c, hyp, vi, seed)
    sc, c, hyp, vi, seed = best
    subprocess.run(["cp", str(c), str(ROOT/f"work/vo/clean/{lid}.wav")], check=True)
    chosen[lid] = {"variant": vi, "seed": seed, "similarity": round(sc,3), "asr": hyp}
    print(lid, f"v{vi} seed{seed} sim={sc:.2f}\n   asr: {hyp}", flush=True)
(ROOT/"work/vo/chosen.json").write_text(json.dumps(chosen, ensure_ascii=False, indent=1))
