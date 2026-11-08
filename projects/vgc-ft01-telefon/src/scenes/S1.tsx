import React from 'react';
import {AbsoluteFill} from 'remotion';
import {C, F} from '../theme';
import {EV, W} from '../data';
import {Shell, Line, useT, Stroke, eo, prog, clamp} from '../lib/ui';
import {Phone} from '../lib/art';

export const S1: React.FC = () => {
  const t = useT();
  const chip = eo(prog(t, EV.s1_msg, 0.3));
  const strike = prog(t, EV.s1_msg + 0.3, 0.2);
  const flash = t >= EV.s1_light ? clamp(0.35 * (1 - (t - EV.s1_light) / 0.3)) : 0;
  return (
    <Shell>
      <div style={{position: 'absolute', left: 60, width: 900, top: 255, textAlign: 'center'}}>
        <Line toks={[{t: 'Tiada', at: 0, slam: true}]} size={200} />
        <Line toks={[{t: 'notifikasi.', at: 0.12, slam: true, hl: 0.35}]} size={200} />
      </div>
      <div style={{position: 'absolute', left: 0, width: 1080, top: 680, display: 'flex', justifyContent: 'center', opacity: chip, transform: `scale(${0.9 + 0.1 * chip})`}}>
        <div style={{position: 'relative', fontFamily: F.label, fontWeight: 700, fontSize: 44, color: C.ink, border: `4px solid ${C.ink}`, borderRadius: 40, padding: '6px 28px', background: C.paper}}>
          Tiada mesej.
          <div style={{position: 'absolute', left: 14, top: '52%', height: 6, width: `${strike * 92}%`, background: C.ink, borderRadius: 3}} />
        </div>
      </div>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <Phone x={540} y={1060} s={1.12} t={t} draw={0} lit={EV.s1_light} tap={EV.s1_tap} />
      </svg>
      <div style={{position: 'absolute', left: 60, width: 900, top: 1335}}>
        <Line toks={[{t: 'Tapi', at: W('L1', 4)}, {t: 'tangan', at: W('L1', 5)}, {t: 'kita,', at: W('L1', 6)}]} size={80} />
        <Line toks={[{t: 'tetap', at: W('L1', 7), hl: W('L1', 7) + 0.05}, {t: 'capai', at: W('L1', 8)}, {t: 'telefon.', at: W('L1', 9)}]} size={80} />
      </div>
      <AbsoluteFill style={{background: C.accent, mixBlendMode: 'screen', opacity: flash}} />
    </Shell>
  );
};
