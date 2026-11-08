import React from 'react';
import {C, F} from '../theme';
import {EV, W} from '../data';
import {Shell, Line, useT, eo, prog} from '../lib/ui';
import {Icon} from '../lib/art';

export const S2: React.FC = () => {
  const t = useT();
  const labels: [string, number, number][] = [['Mesej', EV.s2_i1, 215], ['Panggilan', EV.s2_i2, 540], ['Notifikasi', EV.s2_i3, 865]];
  const none = eo(prog(t, EV.s2_none, 0.3));
  return (
    <Shell>
      <div style={{position: 'absolute', left: 60, width: 900, top: 262}}>
        <Line toks={[{t: 'Kenapa', at: W('L2', 0)}, {t: 'kita', at: W('L2', 1)}]} size={118} />
        <Line toks={[{t: 'buka', at: W('L2', 2)}, {t: 'telefon', at: W('L2', 3)}]} size={118} />
        <Line toks={[{t: 'walaupun', at: W('L2', 4)}, {t: 'tak', at: W('L2', 5)}, {t: 'ada', at: W('L2', 6)}]} size={118} />
        <Line toks={[{t: 'notifikasi?', at: W('L2', 7), hl: W('L2', 7) + 0.1}]} size={118} />
      </div>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <Icon kind="bubble" x={215} y={1010} size={190} t={t} at={EV.s2_i1} cross={EV.s2_x1} />
        <Icon kind="call" x={540} y={1010} size={190} t={t} at={EV.s2_i2} cross={EV.s2_x2} />
        <Icon kind="bell" x={865} y={1010} size={190} t={t} at={EV.s2_i3} cross={EV.s2_x3} />
      </svg>
      {labels.map(([l, at, x]) => (
        <div key={l} style={{position: 'absolute', top: 1130, left: x - 150, width: 300, textAlign: 'center', fontFamily: F.label, fontWeight: 700, fontSize: 38, color: C.ink, opacity: eo(prog(t, at + 0.1, 0.3))}}>{l}</div>
      ))}
      <div style={{position: 'absolute', left: 60, width: 900, top: 1260, textAlign: 'center', opacity: none, transform: `scale(${0.9 + 0.1 * none})`}}>
        <span style={{fontFamily: F.hand, fontSize: 104, color: C.ink}}>Semuanya tiada.</span>
      </div>
    </Shell>
  );
};
