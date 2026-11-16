#!/usr/bin/env python3
"""Diarization guna Resemblyzer embedding per kumpulan perkataan -> work/diar.json
Guna: diarize_emb.py [bilangan_speaker]"""
import sys, types, json, numpy as np
sys.modules['webrtcvad'] = types.ModuleType('webrtcvad')  # tak diperlukan (kita bagi segmen sendiri)
import librosa
from resemblyzer import VoiceEncoder
from sklearn.cluster import KMeans

y, sr = librosa.load("work/A.mp3", sr=16000)
S = json.load(open("work/A.json"))
enc = VoiceEncoder("cpu")
units = []
for si, s in enumerate(S):
    cur = None
    for w in s["words"]:
        if cur and w["s"] - cur["e"] < 0.35:
            cur["e"] = w["e"]; cur["t"] += w["w"]
        else:
            if cur: units.append(cur)
            cur = {"s": w["s"], "e": w["e"], "t": w["w"], "seg": si}
    if cur: units.append(cur)
E = []; keep = []
for u in units:
    a, b = int(u["s"] * sr), int(u["e"] * sr)
    if b - a < sr * 0.5: continue
    E.append(enc.embed_utterance(y[a:b].astype(np.float32))); keep.append(u)
E = np.array(E); k = int(sys.argv[1]) if len(sys.argv) > 1 else 3
lab = KMeans(k, n_init=30, random_state=1).fit_predict(E)
for u, l in zip(keep, lab): u["spk"] = int(l)
json.dump(keep, open("work/diar.json", "w"), ensure_ascii=False, indent=1)
for c in range(k):
    us = [u for u in keep if u["spk"] == c]
    print("cluster", c, len(us), "dur", round(sum(u["e"] - u["s"] for u in us), 1))
for u in keep: print(f'{u["s"]:6.1f}-{u["e"]:6.1f} S{u["spk"]} {u["t"].strip()}')
