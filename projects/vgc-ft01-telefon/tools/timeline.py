"""Bina src/vo.json + src/events.json (sumber kebenaran masa) dari VO sebenar. Semua masa dalam saat, mutlak."""
import json, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parent.parent
lines = json.loads((ROOT/"docs/vo-lines.json").read_text())
align = json.loads((ROOT/"work/vo/align.json").read_text())
dur = lambda f: float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],capture_output=True,text=True).stdout)
GAP = {"L1":0.15,"L2":0.22,"L3":0.45,"L4":0.45,"L5":0.45,"L6":0.45,"L7":0.45,"L8":0.45,"L9":0.30}
vo, t = {}, 0.0
for lid, text in lines.items():
    t += GAP[lid]
    d = dur(ROOT/f"work/vo/clean/{lid}.wav")
    ref = text.split(); asr = align[lid]["words"]
    words = []
    for i, w in enumerate(ref):
        j = round(i*(len(asr)-1)/max(1,len(ref)-1))
        words.append({"w": w, "t": round(t + asr[j][1], 3)})
    vo[lid] = {"start": round(t,3), "end": round(t+d,3), "words": words}
    t += d
END = round(vo["L9"]["end"] + 2.5, 2)
W = lambda L,i: vo[L]["words"][i]["t"]
S = {  # sempadan babak (tengah jeda)
 "S1":(0.0,(vo["L1"]["end"]+vo["L2"]["start"])/2), "S2":None,"S3":None,"S4":None,"S5":None,"S6":None,"S7":None,"S8":None}
b = [0.0]+[round((vo[a]["end"]+vo[c]["start"])/2,3) for a,c in [("L1","L2"),("L2","L3"),("L3","L4"),("L4","L5"),("L5","L6"),("L6","L7"),("L7","L8")]]+[END]
scenes = [{"id":f"S{i+1}","start":b[i],"end":b[i+1]} for i in range(8)]
E = {}
def ev(name, time, sfx=None, vol=1.0): E[name] = {"t": round(time,3), **({"sfx":sfx,"vol":vol} if sfx else {})}
ev("s1_title",0.02,"impact",0.8); ev("s1_phone",0.0,"stroke",0.5); ev("s1_msg",W("L1",2),"tick"); ev("s1_tap",W("L1",7)-0.1,"tap")
ev("s1_light",W("L1",7)+0.12,"pop"); 
ev("s2_i1",W("L2",3),"pop"); ev("s2_x1",W("L2",3)+0.4,"tick"); ev("s2_i2",W("L2",4),"pop"); ev("s2_x2",W("L2",4)+0.4,"tick")
ev("s2_i3",W("L2",7),"pop"); ev("s2_x3",W("L2",7)+0.4,"tick"); ev("s2_none",W("L2",7)+0.95,"impact",0.5)
ev("s3_term",W("L3",5),"impact",0.7); ev("s3_eye",W("L3",8),"stroke",0.6); ev("s3_bell",W("L3",13),"pop"); ev("s3_x1",W("L3",13)+0.4,"tick")
ev("s3_tgt",W("L3",15),"pop"); ev("s3_x2",W("L3",15)+0.4,"tick")
ev("s4_arrow",W("L4",7),"stroke",0.7); ev("s4_bell",W("L4",12),"pop"); ev("s4_x",W("L4",12)+0.4,"tick")
ev("s5_n1",W("L5",3),"pop"); ev("s5_n2",W("L5",8),"pop"); ev("s5_n3",W("L5",11),"pop"); ev("s5_loop",W("L5",12),"stroke",0.7)
ev("s5_strong",W("L5",14),"impact",0.6); ev("s5_swap",W("L5",15)-0.12,"whoosh",0.7); ev("s5_bored",W("L5",18),"pop")
ev("s6_c1",scenes[5]["start"]+0.06,"pop"); ev("s6_c2",W("L6",5)-0.14,"whoosh",0.8); ev("s6_c3",W("L6",10)-0.12,"whoosh",0.8)
ev("s6_t1",W("L6",4),"tap"); ev("s6_t2",W("L6",9),"tap"); ev("s6_t3",W("L6",12),"tap")
ev("s7_x",W("L7",7)+0.1,"tick"); ev("s7_ok",W("L7",12),"chime",0.8)
ev("s8_box",W("L8",12),"impact",0.8); ev("s8_swap",vo["L9"]["start"]-0.2,"whoosh",0.7); ev("s8_eyes",W("L9",11),"pop")
ev("s8_credit",vo["L9"]["end"]-0.5,"pop"); ev("s8_chime",vo["L9"]["end"]+0.45,"chime",1.0)
for sc in scenes[:-1]: ev(f"cut_{sc['id']}",sc["end"]-0.2,"whoosh",0.8)
(ROOT/"src/vo.json").write_text(json.dumps(vo,ensure_ascii=False,indent=1))
(ROOT/"src/events.json").write_text(json.dumps({"duration":END,"scenes":scenes,"events":E},indent=1))
print("END",END); [print(s["id"],round(s["start"],2),round(s["end"],2)) for s in scenes]
