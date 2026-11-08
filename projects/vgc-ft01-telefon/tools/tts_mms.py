"""VO setempat: facebook/mms-tts-zlm (VITS, Bahasa Melayu) guna transformers sahaja, tanpa kod luar.
Lesen model: CC-BY-NC 4.0 (bukan komersial). Guna: python tools/tts_mms.py L1,L2,... [seed] [speed]
Output: work/vo/mms/<Lx>.wav (16 kHz mono)."""
import json, sys, time, pathlib
import numpy as np, soundfile as sf, torch
from transformers import VitsModel, AutoTokenizer
ROOT = pathlib.Path(__file__).resolve().parent.parent
ids = sys.argv[1].split(",")
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 11
speed = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
lines = json.loads((ROOT / "docs" / "vo-lines.json").read_text())
out = ROOT / "work" / "vo" / "mms"; out.mkdir(parents=True, exist_ok=True)
tok = AutoTokenizer.from_pretrained(str(ROOT / "models/mms-zlm"))
model = VitsModel.from_pretrained(str(ROOT / "models/mms-zlm")).eval()
model.speaking_rate = speed
sr = model.config.sampling_rate
for lid in ids:
    torch.manual_seed(seed)
    enc = tok(lines[lid].lower(), return_tensors="pt")
    t0 = time.time()
    with torch.no_grad():
        wav = model(**enc).waveform[0].cpu().numpy()
    sf.write(out / f"{lid}.wav", wav, sr)
    print(f"{lid}: {len(wav)/sr:.2f}s @ {sr} Hz, {time.time()-t0:.1f}s compute", flush=True)
