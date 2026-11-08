import React from 'react';
import {C, F} from '../theme';
import {EV, W} from '../data';
import {Shell, Line, useT, Stroke, rr, eo, eob, prog} from '../lib/ui';

export const S7: React.FC = () => {
  const t = useT();
  const a = EV.s7_x - 0.25, b = EV.s7_ok - 0.2;
  const ca = eob(prog(t, a, 0.3)), cb = eob(prog(t, b, 0.3));
  return (
    <Shell>
      <div style={{position: 'absolute', left: 60, width: 900, top: 262}}>
        <Line toks={[{t: 'Kadangkala', at: W('L7', 0)}, {t: 'kita', at: W('L7', 1)}, {t: 'membuka', at: W('L7', 2)}]} size={92} />
        <Line toks={[{t: 'telefon', at: W('L7', 3)}, {t: 'bukan', at: W('L7', 4), c: C.faint}, {t: 'kerana', at: W('L7', 5), c: C.faint}, {t: 'ada', at: W('L7', 6), c: C.faint}]} size={92} />
        <Line toks={[{t: 'keperluan,', at: W('L7', 7), c: C.faint}, {t: 'tetapi', at: W('L7', 8)}, {t: 'kerana', at: W('L7', 9)}]} size={92} />
        <Line toks={[{t: 'kita', at: W('L7', 10)}, {t: 'sudah', at: W('L7', 11)}, {t: 'terbiasa', at: W('L7', 12), hl: W('L7', 12) + 0.05}]} size={92} />
        <Line toks={[{t: 'melakukannya.', at: W('L7', 13)}]} size={92} />
      </div>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <g style={{transformBox: 'fill-box', transformOrigin: 'center', transform: `scale(${t < a ? 0 : 0.6 + 0.4 * ca})`}}>
          <Stroke d={rr(80, 1180, 390, 230, 30, 21)} t={t} s={a} dur={0.3} w={7} fill={C.paper} />
          <Stroke d="M130 1200 L420 1390 M420 1200 L130 1390" t={t} s={EV.s7_x} dur={0.3} w={12} color={C.ink} op={0.0 + 1} />
        </g>
        <g style={{transformBox: 'fill-box', transformOrigin: 'center', transform: `scale(${t < b ? 0 : 0.6 + 0.4 * cb})`}}>
          <Stroke d={rr(560, 1180, 390, 230, 30, 23)} t={t} s={b} dur={0.3} w={7} fill={C.accentSoft} />
          <Stroke d="M840 1340 L880 1380 L940 1270" t={t} s={EV.s7_ok} dur={0.3} w={12} color={C.ink} />
        </g>
      </svg>
      <div style={{position: 'absolute', left: 80, width: 390, top: 1062, textAlign: 'center', fontFamily: F.hand, fontSize: 76, color: C.ink, opacity: eo(prog(t, a + 0.1, 0.25))}}>Keperluan</div>
      <div style={{position: 'absolute', left: 560, width: 390, top: 1062, textAlign: 'center', fontFamily: F.hand, fontSize: 76, color: C.ink, opacity: eo(prog(t, b + 0.1, 0.25))}}>Terbiasa</div>
    </Shell>
  );
};
