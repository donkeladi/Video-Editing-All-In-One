import React from 'react';
import {C, F} from '../theme';
import {EV, W, VO} from '../data';
import {Shell, Line, useT, Stroke, rr, eo, eob, prog} from '../lib/ui';
import {Phone} from '../lib/art';

export const S8: React.FC = () => {
  const t = useT();
  const B = t >= EV.s8_swap + 0.2;
  const box = eob(prog(t, W('L8', 12), 0.3));
  if (!B) {
    return (
      <Shell>
        <div style={{position: 'absolute', left: 60, width: 900, top: 262}}>
          <Line toks={[{t: 'Lain', at: W('L8', 0)}, {t: 'kali', at: W('L8', 1)}, {t: 'bila', at: W('L8', 2)}, {t: 'tangan', at: W('L8', 3)}, {t: 'korang', at: W('L8', 4)}]} size={86} />
          <Line toks={[{t: 'automatik', at: W('L8', 5), hl: W('L8', 5) + 0.05}, {t: 'capai', at: W('L8', 6)}, {t: 'telefon,', at: W('L8', 7)}]} size={86} />
          <Line toks={[{t: 'cuba', at: W('L8', 8)}, {t: 'tanya', at: W('L8', 9)}, {t: 'diri', at: W('L8', 10)}, {t: 'sendiri:', at: W('L8', 11)}]} size={86} />
        </div>
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          <g style={{transformBox: 'fill-box', transformOrigin: 'center', transform: `scale(${t < W('L8', 12) ? 0 : 0.7 + 0.3 * box})`}}>
            <Stroke d={rr(110, 840, 760, 290, 36, 31)} t={t} s={W('L8', 12)} dur={0.3} w={8} fill={C.accentSoft} />
          </g>
          <Phone x={540} y={1360} s={0.5} t={t} draw={W('L8', 5)} lit={W('L8', 12) + 0.3} content="q" />
        </svg>
        <div style={{position: 'absolute', left: 110, width: 760, top: 866, textAlign: 'center'}}>
          <Line toks={[{t: 'Aku', at: W('L8', 12)}, {t: 'sebenarnya', at: W('L8', 13)}]} size={104} />
          <Line toks={[{t: 'nak', at: W('L8', 14)}, {t: 'cari', at: W('L8', 15)}, {t: 'apa?', at: W('L8', 16), hl: W('L8', 16) + 0.05}]} size={104} />
        </div>
      </Shell>
    );
  }
  const cred = eob(prog(t, EV.s8_credit, 0.35)), pulse = t >= EV.s8_chime ? 1 + 0.06 * Math.max(0, 1 - (t - EV.s8_chime) / 0.3) : 1;
  return (
    <Shell>
      <div style={{position: 'absolute', left: 60, width: 900, top: 262}}>
        <Line toks={[{t: 'Kalau', at: W('L9', 0)}, {t: 'korang', at: W('L9', 1)}, {t: 'selalu', at: W('L9', 2)}, {t: 'buat', at: W('L9', 3)}, {t: 'benda', at: W('L9', 4)}, {t: 'ni,', at: W('L9', 5)}]} size={92} />
        <Line toks={[{t: 'mungkin', at: W('L9', 6)}, {t: 'video', at: W('L9', 7)}, {t: 'ini', at: W('L9', 8)}, {t: 'memang', at: W('L9', 9)}]} size={92} />
        <Line toks={[{t: 'tentang', at: W('L9', 10)}, {t: 'korang.', at: W('L9', 11), hl: W('L9', 11) + 0.05}]} size={92} />
      </div>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <Phone x={540} y={1000} s={0.62} t={t} draw={EV.s8_swap} lit={EV.s8_eyes} content="eyes" />
      </svg>
      <div style={{position: 'absolute', left: 0, width: 1080, top: 1330, display: 'flex', justifyContent: 'center', opacity: eo(cred * 1.2), transform: `scale(${(0.8 + 0.2 * cred) * pulse})`}}>
        <div style={{background: C.accentSoft, border: `5px solid ${C.ink}`, borderRadius: 40, padding: '8px 40px 14px', textAlign: 'center'}}>
          <div style={{fontFamily: F.label, fontWeight: 700, fontSize: 30, color: C.ink, letterSpacing: 2}}>CREDIT</div>
          <div style={{fontFamily: F.hand, fontSize: 104, color: C.ink, lineHeight: 1}}>@pidotmael</div>
        </div>
      </div>
    </Shell>
  );
};
