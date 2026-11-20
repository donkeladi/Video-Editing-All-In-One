"""Jana muzik instrumental + SFX secara prosedur (numpy). Tiada muzik komersial. Guna: make_audio.py cues.json out_music.wav out_sfx.wav"""
import sys,json,wave,numpy as np
SR=44100;cues=json.load(open(sys.argv[1]));D=cues['duration']+0.5;N=int(D*SR)
rng=np.random.default_rng(7)
def T(n):return np.arange(n)/SR
def env(n,a,r,k=3):
    t=T(n);e=np.minimum(t/max(a,1e-4),1)*np.exp(-t*k/max(r,1e-4));return e
def lp(x,fc):
    a=np.exp(-2*np.pi*fc/SR);y=np.zeros_like(x);s=0.0
    for i in range(len(x)):
        s=(1-a)*x[i]+a*s;y[i]=s
    return y
def add(buf,x,t0,g=1.0):
    i=int(t0*SR)
    if i>=len(buf):return
    j=min(len(buf),i+len(x));buf[i:j]+=x[:j-i]*g
# ---- muzik ----
bpm=96;beat=60/bpm;m=np.zeros((N,2))
chords=[(57,[57,60,64]),(53,[53,57,60]),(48,[48,52,55]),(55,[55,59,62])] # Am F C G
mf=lambda n:440*2**((n-69)/12)
def inten(t):  # perkembangan: hook sparse -> isi -> klimaks CTA
    if t<5.96:return 0.45
    if t<cues['titles'][-1]['t0']:return 0.8
    return 1.1
bar=beat*4
for b in range(int(D/bar)+1):
    t0=b*bar;ch=chords[b//2%4];n=int(bar*SR)+int(0.4*SR)
    if t0>=D:break
    pad=np.zeros(n);t=T(n)
    for note in ch[1]:
        for det in (-0.003,0,0.003):
            f=mf(note)*(1+det);pad+=np.sin(2*np.pi*f*t)+0.3*np.sin(4*np.pi*f*t)
    pad*=0.05*np.minimum(t/0.5,1)*np.minimum((bar+0.4-t)/0.4,1)
    pad=lp(pad,1400)
    L=pad*inten(t0);add(m[:,0],L,t0);add(m[:,1],L*0.95,t0)
    if t0>=5.9:   # bass + kick
        for k in range(4):
            tb=t0+k*beat;nb=int(beat*SR);tt=T(nb)
            bass=np.sin(2*np.pi*mf(ch[0]-12)*tt)*env(nb,0.01,beat*0.9,2.5)*0.12*inten(tb)
            add(m[:,0],bass,tb);add(m[:,1],bass,tb)
            kk=np.sin(2*np.pi*(55+90*np.exp(-tt*30))*tt)*env(nb,0.002,0.18,9)*0.16*inten(tb)
            if k%2==0 or tb>cues['titles'][-1]['t0']: add(m[:,0],kk,tb);add(m[:,1],kk,tb)
    if t0>=12:    # hat 8th
        for k in range(8):
            th=t0+k*beat/2;nh=int(0.05*SR);hh=rng.standard_normal(nh)
            hh=(hh-lp(hh,6000))*env(nh,0.001,0.04,6)*0.05*(1.4 if k%2 else 0.8)
            add(m[:,0],hh,th);add(m[:,1],hh,th+0.004)
    if t0>=24 and b%2==0:   # arpeggio lembut
        for k in range(8):
            ta=t0+k*beat/2;na=int(0.3*SR);tt=T(na);note=ch[1][k%3]+12
            a_=np.sin(2*np.pi*mf(note)*tt)*env(na,0.004,0.25,7)*0.035*inten(ta)
            add(m[:,0],a_,ta);add(m[:,1],a_*0.8,ta+0.01)
fade=np.minimum(1,(D-T(N))/1.5)
m*=fade[:,None]
# riser sebelum CTA
tc=cues['titles'][-1]['lines'][-1]['t']
nr=int(1.6*SR);tt=T(nr);rs=rng.standard_normal(nr);rs=lp(rs,3000)-lp(rs,300);rs*=(tt/1.6)**2*0.09
add(m[:,0],rs,tc-1.6);add(m[:,1],rs,tc-1.6)
# ---- sfx ----
s=np.zeros((N,2));last=-9
def click(t,g=1):
    n=int(0.06*SR);tt=T(n);x=np.sin(2*np.pi*1500*tt)*env(n,0.0005,0.03,8)*0.5+(rng.standard_normal(n)-lp(rng.standard_normal(n),2500))*env(n,0.0003,0.012,8)*0.25
    add(s[:,0],x,t,g*0.5);add(s[:,1],x,t,g*0.5)
def pop(t,g=1):
    n=int(0.12*SR);tt=T(n);x=np.sin(2*np.pi*(420+700*np.exp(-tt*40))*tt)*env(n,0.001,0.08,8)*0.6
    add(s[:,0],x,t,g*0.45);add(s[:,1],x,t,g*0.45)
def whoosh(t,g=1,up=True):
    n=int(0.4*SR);tt=T(n);x=rng.standard_normal(n);x=lp(x,5000)-lp(x,500);e=np.sin(np.pi*np.minimum(tt/0.4,1))**2
    x=x*e*0.25;add(s[:,0],x,t-0.12,g*0.5);add(s[:,1],x[::-1] if not up else x,t-0.12,g*0.5)
def impact(t):
    n=int(0.8*SR);tt=T(n);x=np.sin(2*np.pi*(48+60*np.exp(-tt*14))*tt)*env(n,0.002,0.5,5)*0.7
    add(s[:,0],x,t,0.6);add(s[:,1],x,t,0.6)
for ti in cues['titles']:
    for l in ti['lines']:
        if l['size'] in('big','huge') and l['t']-last>0.3: click(l['t']);last=l['t']
        elif l['size']=='kick' and l['t']-last>0.3: pop(l['t'],0.6);last=l['t']
lastc=-9
for c in cues['cards']:
    if c['t0']-lastc>0.45: whoosh(c['t0']);lastc=c['t0']
huge=[l['t'] for ti in cues['titles'] for l in ti['lines'] if l['size']=='huge']
for h in huge: impact(h)
for x,name in ((m,sys.argv[2]),(s,sys.argv[3])):
    pk=np.abs(x).max();print(name,'peak',round(pk,3))
    y=np.clip(x*0.9/max(pk,1e-6),-1,1)  # normalisasi puncak 0.9; tahap akhir dikawal masa mix
    w=wave.open(name,'wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((y*32767).astype('<i2').tobytes());w.close()
