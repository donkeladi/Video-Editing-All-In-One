import sys,json
from faster_whisper import WhisperModel
m=WhisperModel('small',compute_type='int8')
import numpy as np,subprocess
aud=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',sys.argv[1],'-f','s16le','-ac','1','-ar','16000','-']),np.int16).astype(np.float32)/32768
seg,info=m.transcribe(aud,language='ms',word_timestamps=True,vad_filter=False,initial_prompt="DS Pharma Eye Care, lobak merah, goji, avokado, eyebright, MAL22076147T")
out=[]
for s in seg:
    out.append({'s':s.start,'e':s.end,'t':s.text,'w':[{'w':w.word,'s':w.start,'e':w.end} for w in s.words]})
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
for o in out: print(f"{o['s']:.2f}-{o['e']:.2f} {o['t']}")
