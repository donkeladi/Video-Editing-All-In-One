"""Cue sheet (masa dalam video ASAL) -> dipetakan ke masa video selepas jump-cut -> project/src/cues.json"""
import json
mp=json.load(open('work/map.json'));S=mp['segments'];DUR=mp['duration']
import numpy as np,subprocess
_a=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i','work/main.wav','-f','s16le','-ac','1','-ar','16000','-']),np.int16).astype(float)/32768
_db=20*np.log10(np.sqrt((_a[:len(_a)//160*160].reshape(-1,160)**2).mean(1))+1e-6)
ONS=[];_i=0
while _i<len(_db):
    if _db[_i]<-38:
        _j=_i
        while _j<len(_db) and _db[_j]<-38:_j+=1
        if (_j-_i)>=18 and _j<len(_db):ONS.append(_j*.01)
        _i=_j
    else:_i+=1
def snap(t):
    c=[o for o in ONS if abs(o-t)<0.4]
    return min(c,key=lambda o:abs(o-t))-0.04 if c else t
def m(t):
    t=snap(t)
    for s in S:
        if s['src']<=t<s['end']: return round(s['out']+t-s['src'],3)
    for s in S:
        if s['src']>t: return round(s['out'],3)
    return round(DUR,3)
END=76.0
def L(text,t,until=None,size='big',sub=False): return dict(text=text,t=m(t),until=m(until) if until else None,size=size)
def T(t0,t1,lines,chip=None,chipT=None): return dict(t0=m(t0),t1=m(t1),lines=lines,chip=chip,chipT=m(chipT or t0))
def C(t0,t1,img,side='r',rot=3,w=340): return dict(t0=m(t0),t1=m(t1),img=img,rot=rot,w=w)
titles=[
 T(0.88,6.4,[L('NAK AMBIL',0.88,size='kick'),L('*LOBAK MERAH*',1.36,2.32),L('GOJI',2.32,2.62),L('*AVOKADO*',2.62,3.90),L('EYEBRIGHT',3.90,4.58),L('MAKANAN HARIAN',4.58)]),
 T(6.4,7.98,[L('SAYA ADA',6.4,size='kick'),L('*3 CARA* SENANG',6.8)]),
 T(7.98,12.58,[L('01 · TUMIS LOBAK MERAH',7.98,size='kick'),L('DENGAN SEDIKIT *MINYAK*',9.36,10.5),L('KAROTENOID',10.5),L('larut dalam minyak',11.04,size='sub')]),
 T(12.58,19.10,[L('MANUAL MSD',12.58,14.22),L('PALING BAIK',14.22),L('*DISERAP*',14.74),L('sayur dimasak dengan sedikit lemak / minyak',15.66,size='sub')],chip='Sumber: MSD Manual',chipT=12.58),
 T(19.10,22.92,[L('02 · GOJI',19.10,size='kick'),L('GOJI DALAM *SUP*',20.18),L('secara tradisional',21.34,size='sub')]),
 T(22.92,31.0,[L('DIMASAK',24.22,24.92),L('DALAM *SUP*',24.92,26.82),L('*TEH HERBA*',29.92),L('diamalkan di China',28.26,size='sub')],chip='Sumber: Orami Indonesia',chipT=22.92),
 T(31.0,36.0,[L('03 · AVOKADO',31.0,size='kick'),L('LEMAK *BAIK*',34.62)]),
 T(36.0,42.76,[L('BERITA HARIAN',36.0,37.76),L('BANTU SERAP',37.76),L('*LEMAK LARUT*',38.66)],chip='Sumber: Berita Harian, 2019',chipT=36.0),
 T(42.76,48.5,[L('*TAPI INGAT*',42.76,43.71),L('MAKANAN CUKUP',43.71,45.42),L('PEMERIKSAAN MATA',45.42,46.42),L('*BERKALA*',46.42)]),
 T(48.5,54.78,[L('PAKAR SYOR',48.5,size='kick'),L('PEMERIKSAAN MATA ASAS',49.44,51.70),L('BILA UMUR',51.70,53.16),L('*40 TAHUN*',53.16,size='huge')],chip='Sumber: Mayo Clinic; AAO',chipT=48.5),
 T(54.78,60.73,[L('SOKONGAN HARIAN',55.36,57.4,size='kick'),L('TAMBAHAN',56.96,58.52),L('DS PHARMA',58.52,59.68),L('*EYE CARE*',59.68)]),
 T(60.73,66.25,[L('ADA JUGA',60.73,size='kick'),L('*EYEBRIGHT*',61.08),L('bunga Eropah, digunakan secara tradisional untuk mata',62.2,size='sub')]),
 T(66.25,71.4,[L('BERDAFTAR',66.25,size='kick'),L('*MAL22076147T*',67.24),L('digunakan secara tradisional untuk kesihatan mata',67.5,size='sub')]),
 T(71.4,END,[L('NAK DAPATKAN?',71.6,size='kick'),L('*TENGOK PROFIL*',72.76,74.0),L('CEK *BEG KUNING*',74.0)]),
]
cards=[C(1.36,2.32,'carrot'),C(2.32,2.62,'goji',rot=-3),C(2.62,3.90,'avocado'),C(3.90,5.2,'eyebright',rot=-3),
 C(7.98,15.66,'carrot'),C(19.10,31.0,'goji',rot=-3),C(31.0,42.76,'avocado'),
 C(58.52,60.73,'product',w=380),C(60.73,66.25,'eyebright',rot=-3),C(66.4,71.4,'kkm',w=380),C(71.5,END,'product',w=420)]
caps=[(0.88,2.6,"Nak ambil *lobak merah*, *goji*,"),(2.6,4.58,"*avokado* dan juga *eyebright*"),(4.58,6.4,"dalam makanan harian?"),
(6.4,7.98,"Saya ada *3 cara* senang."),(7.98,10.5,"*Satu*, tumis lobak merah dengan sedikit minyak"),(10.5,12.58,"*Karotenoid* larut dalam minyak"),
(12.58,15.12,"*Manual MSD* cakap ia paling baik diserap"),(15.12,19.10,"daripada sayur yang dimasak dengan sedikit lemak ataupun minyak"),
(19.10,21.34,"*Kedua*, letak goji dalam sup"),(21.34,22.92,"secara tradisional"),(22.92,25.9,"Goji memang dah pernah dimasak dalam sup"),
(25.9,31.0,"tapi banyak diamalkan di China ataupun dibuat sebagai *teh herba*"),(31.0,36.0,"*Yang ketiga*, kita ada sisip avokado sebagai lemak baik"),
(36.0,39.4,"*Berita Harian* tulis, avokado bantu serap lemak larut"),(39.4,42.76,"dalam Berita Harian around 2019 macam itu"),
(42.76,46.42,"*Tapi ingat*, makanan cukup dan pemeriksaan mata"),(46.42,48.5,"berkala tetap asas"),(48.5,51.7,"Pakar syor pemeriksaan mata asas"),
(51.7,54.78,"bila umur dah meningkat *40 tahun*"),(54.78,58.02,"Kalau nak sokongan harian tambahan"),(58.02,60.73,"ada *DS Pharma Eye Care*"),
(60.73,62.2,"Ada *eyebright* juga,"),(62.2,66.25,"bunga Eropah yang digunakan secara tradisional untuk mata"),
(66.25,67.5,"*Berdaftar* dengan MAL22076147T"),(67.5,71.4,"digunakan secara tradisional untuk kesihatan mata"),
(71.4,73.6,"Jadi kalau nak dapatkan ni, boleh tengok dekat *profil*"),(73.6,75.4,"ataupun cek *beg kuning* sekarang")]
caps=[dict(t0=m(a),t1=m(b),text=t) for a,b,t in caps]
for i in range(len(caps)-1):
    if caps[i+1]['t0']-caps[i]['t1']<0.8: caps[i]['t1']=caps[i+1]['t0']
segs=[dict(t0=s['out'],t1=(S[i+1]['out'] if i+1<len(S) else DUR)) for i,s in enumerate(S)]
json.dump(dict(duration=DUR,titles=titles,cards=cards,caps=caps,segs=segs),open('project/src/cues.json','w'),ensure_ascii=False,indent=1)
print('duration',DUR)
