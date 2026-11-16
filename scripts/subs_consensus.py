#!/usr/bin/env python3
"""Subtitle konsensus: simpan perkataan yang dipersetujui >=2 transkrip (A3 large-v3, A2 medium, A1 small).
Yang tak jelas dikosongkan. -> work/subw.json  [{"w","s","e"}]"""
import json, re, difflib

def load(p): return [dict(w=w["w"].strip(), s=w["s"], e=w["e"], p=w.get("p", 0)) for sg in json.load(open(p)) for w in sg["words"]]
M = {"A3": load("work/A3.json"), "A2": load("work/A2.json"), "A1": load("work/A.json")}
DIG = {"1": "satu", "2": "dua", "3": "tiga"}
HASHA = {"syah", "aisyah", "hishan", "islan", "hasha", "azia", "aisya"}

def norm(w):
    w = re.sub(r"[^\w]", "", w.lower().replace("-", ""))
    w = DIG.get(w, w)
    if w in ("ok", "okay"): w = "okey"
    if w == "bijak": w = "pija"
    if w in HASHA: w = "hasha"
    return w

def sim(a, b):
    a, b = norm(a), norm(b)
    if not a or not b: return False
    return a == b or difflib.SequenceMatcher(None, a, b).ratio() >= .78

def near(w, other, tol=.5):
    c = (w["s"] + w["e"]) / 2
    return [o for o in other if abs((o["s"] + o["e"]) / 2 - c) <= tol and sim(w["w"], o["w"])]

import sys
PMIN = float(sys.argv[1]) if len(sys.argv) > 1 else 0.85
acc = []
def covered(w): return any(abs((a["s"] + a["e"]) / 2 - (w["s"] + w["e"]) / 2) < .4 and sim(a["w"], w["w"]) for a in acc)
order = ["A3", "A2", "A1"]
for k, m in enumerate(order):
    others = [M[x] for x in order if x != m]
    for w in M[m]:
        if not norm(w["w"]) or covered(w): continue
        sup = sum(1 for o in others if near(w, o))
        if sup >= 2 or (sup >= 1 and m == "A3" and w["p"] >= PMIN): acc.append(dict(w=w["w"], s=w["s"], e=w["e"], src=m, sup=sup))
acc.sort(key=lambda w: w["s"])
ded = []
for w in acc:        # buang pendua (perkataan sama dalam 0.7s)
    if ded and sim(ded[-1]["w"], w["w"]) and abs((ded[-1]["s"] + ded[-1]["e"]) / 2 - (w["s"] + w["e"]) / 2) < .7:
        if w["src"] == "A3" and ded[-1]["src"] != "A3": ded[-1] = w
        continue
    ded.append(w)
acc = ded
for w in acc:        # teks paparan
    n = norm(w["w"]); raw = w["w"].strip()
    t = {"pija": "Pija", "hasha": "Hasha"}.get(n) or (n if raw.strip(".,?!").isdigit() else raw.strip(".,?!…").lstrip("-"))
    w["t"] = t + ("?" if raw.endswith("?") else "!" if raw.endswith("!") else "")
json.dump(acc, open("work/subw.json", "w"), ensure_ascii=False, indent=1)
tot = len([w for w in M["A3"] if norm(w["w"])])
print(f"diterima {len(acc)} perkataan (A3 asal {tot})")
line = []; last = -9
for w in acc:
    if w["s"] - last > 1.2 and line: print(f"{line[0][0]:6.1f}  " + " ".join(x[1] for x in line)); line = []
    line.append((w["s"], w["w"].strip())); last = w["e"]
if line: print(f"{line[0][0]:6.1f}  " + " ".join(x[1] for x in line))
