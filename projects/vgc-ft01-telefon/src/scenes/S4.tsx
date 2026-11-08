import React from 'react';
import {C, F} from '../theme';
import {EV, W} from '../data';
import {Shell, Line, Tag, useT, Stroke, eo, prog} from '../lib/ui';
import {Phone, Icon} from '../lib/art';

export const S4: React.FC = () => {
  const t = useT();
  const lab = (text: string, at: number, x: number, y: number) => (
    <div style={{position: 'absolute', left: x - 150, width: 300, top: y, textAlign: 'center', fontFamily: F.label, fontWeight: 700, fontSize: 38, color: C.ink, opacity: eo(prog(t, at, 0.3))}}>{text}</div>
  );
  return (
    <Shell>
      <div style={{position: 'absolute', left: 60, width: 900, top: 262}}>
        <Line toks={[{t: 'Satu', at: W('L4', 1)}, {t: 'kajian', at: W('L4', 2)}, {t: 'kecil:', at: W('L4', 3)}]} size={80} color={C.faint} />
      </div>
      <div style={{position: 'absolute', left: 60, width: 900, top: 380}}>
        <Line toks={[{t: 'kebanyakan', at: W('L4', 4)}, {t: 'interaksi', at: W('L4', 5)}]} size={112} />
        <Line toks={[{t: 'telefon', at: W('L4', 6)}, {t: 'dimulakan', at: W('L4', 7), hl: W('L4', 7) + 0.1}]} size={112} />
        <Line toks={[{t: 'pengguna', at: W('L4', 9)}, {t: 'sendiri.', at: W('L4', 10)}]} size={112} />
        <div style={{height: 20}} />
        <Line toks={[{t: 'Bukan', at: W('L4', 11)}, {t: 'notifikasi.', at: W('L4', 12)}]} size={96} color={C.faint} />
      </div>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {/* pengguna */}
        <g transform="translate(200 1190)">
          <Stroke d="M-40 -40 a40 40 0 1 0 80 0 a40 40 0 1 0 -80 0" t={t} s={EV.s4_arrow - 0.4} dur={0.3} fill={C.paper} />
          <Stroke d="M-80 90 Q-80 20 0 20 Q80 20 80 90 Z" t={t} s={EV.s4_arrow - 0.3} dur={0.35} fill={C.accentSoft} />
        </g>
        <Stroke d="M300 1200 L580 1200" t={t} s={EV.s4_arrow} dur={0.5} w={18} />
        <Stroke d="M540 1150 L600 1200 L540 1250" t={t} s={EV.s4_arrow + 0.45} dur={0.2} w={18} />
        <Phone x={760} y={1200} s={0.58} t={t} draw={EV.s4_arrow - 0.2} lit={EV.s4_arrow + 0.55} content="none" />
        <Icon kind="bell" x={850} y={1010} size={90} t={t} at={EV.s4_bell} cross={EV.s4_x} />
        <Stroke d="M840 1062 L805 1095" t={t} s={EV.s4_bell + 0.1} dur={0.2} w={4} />
      </svg>
      {lab('Pengguna', EV.s4_arrow, 200, 1310)}
      {lab('Notifikasi', EV.s4_bell + 0.1, 850, 925)}
      <Tag text="Heitmayer & Lahlou, 2021" at={W('L4', 9)} style={{left: 60, width: 900, textAlign: 'center', top: 1478}} />
    </Shell>
  );
};
