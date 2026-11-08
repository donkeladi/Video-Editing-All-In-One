import React from 'react';
import {C, F} from '../theme';
import {EV, W} from '../data';
import {Shell, Line, Tag, useT, Stroke, Pop, eo, prog, clamp} from '../lib/ui';
import {Phone, Icon} from '../lib/art';

export const S5: React.FC = () => {
  const t = useT();
  const B = t >= EV.s5_swap + 0.12; // bahagian B: bosan
  const strong = t >= EV.s5_strong ? 1 + 0.5 * Math.max(0, 1 - (t - EV.s5_strong) / 0.4) : 1;
  const lab = (text: string, at: number, x: number, y: number, size = 60) => (
    <div style={{position: 'absolute', left: x - 200, width: 400, top: y, textAlign: 'center', fontFamily: F.hand, fontSize: size, color: C.ink, opacity: eo(prog(t, at, 0.3)), lineHeight: 1}}>{text}</div>
  );
  if (!B) {
    const wk = (c: boolean) => (c ? C.accent : C.ink);
    return (
      <Shell>
        <div style={{position: 'absolute', left: 60, width: 900, top: 262}}>
          <Line toks={[{t: 'Semakan', at: W('L5', 0)}, {t: 'singkat,', at: W('L5', 3)}, {t: 'berulang.', at: W('L5', 5)}]} size={104} />
        </div>
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          <Phone x={540} y={760} s={0.4} t={t} draw={W('L5', 0)} lit={EV.s5_n1} content="none" />
          <Icon kind="spark" x={790} y={1060} size={140} t={t} at={EV.s5_n2} />
          <Icon kind="clock" x={290} y={1060} size={140} t={t} at={EV.s5_n3} />
          <Stroke d="M610 870 Q760 900 790 975" t={t} s={EV.s5_n2 - 0.4} dur={0.45} w={9} />
          <Stroke d="M762 948 L792 986 L742 994" t={t} s={EV.s5_n2 - 0.0} dur={0.15} w={9} />
          <Stroke d="M760 1290 Q540 1420 320 1290" t={t} s={EV.s5_n3 - 0.4} dur={0.45} w={9} />
          <Stroke d="M352 1318 L318 1288 L372 1262" t={t} s={EV.s5_n3 - 0.0} dur={0.15} w={9} />
          <Stroke d="M290 975 Q310 880 460 830" t={t} s={EV.s5_loop} dur={0.55} w={9 * strong} color={t >= EV.s5_strong ? C.accent : C.ink} />
          <Stroke d="M430 790 L466 828 L414 848" t={t} s={EV.s5_loop + 0.5} dur={0.15} w={9 * strong} color={t >= EV.s5_strong ? C.accent : C.ink} />
        </svg>
        {lab('Semak', EV.s5_n1, 540, 930)}
        {lab('Kandungan baharu', EV.s5_n2, 770, 1150, 52)}
        {lab('Tabiat', EV.s5_n3, 300, 1150)}
        <div style={{position: 'absolute', left: 60, width: 900, top: 1370, textAlign: 'center', opacity: eo(prog(t, W('L5', 14), 0.3))}}>
          <Line toks={[{t: 'makin', at: W('L5', 13)}, {t: 'kuat', at: W('L5', 14), hl: W('L5', 14) + 0.05}]} size={88} />
        </div>
        <Tag text="Oulasvirta et al., 2012" at={W('L5', 11)} style={{left: 60, width: 900, textAlign: 'center', top: 1478}} />
      </Shell>
    );
  }
  const bs = EV.s5_swap + 0.12;
  return (
    <Shell>
      <div style={{position: 'absolute', left: 60, width: 900, top: 262}}>
        <Line toks={[{t: 'Mungkin', at: W('L5', 15)}, {t: 'juga', at: W('L5', 16)}]} size={104} />
        <Line toks={[{t: 'sebab', at: W('L5', 17)}, {t: 'bosan,', at: W('L5', 18), hl: W('L5', 18) + 0.1}]} size={104} />
      </div>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <Icon kind="clock" x={760} y={900} size={200} t={t} at={bs} />
        <g transform="translate(330 960)">
          <Stroke d="M-110 0 a110 110 0 1 0 220 0 a110 110 0 1 0 -220 0" t={t} s={bs + 0.05} dur={0.45} fill={C.paper} w={8} />
          <Stroke d="M-52 -18 l0.1 0 M52 -18 l0.1 0" t={t} s={bs + 0.4} dur={0.1} w={14} />
          <Stroke d="M-40 42 L40 42" t={t} s={bs + 0.45} dur={0.2} w={7} />
        </g>
        <Pop t={t} s={EV.s5_bored}>
          <Stroke d={`M470 1090 Q520 1010 600 1060 Q690 1030 700 1110 Q770 1160 690 1215 Q640 1270 570 1230 Q500 1280 470 1210 Q400 1170 470 1090 Z`} t={t} s={EV.s5_bored} dur={0.4} fill={C.accentSoft} w={7} />
          <text x={585} y={1190} textAnchor="middle" fontFamily='"Caveat Brush"' fontSize={120} fill={C.ink}>?</text>
        </Pop>
      </svg>
      <div style={{position: 'absolute', left: 60, width: 900, top: 1320}}>
        <Line toks={[{t: 'tapi', at: W('L5', 19)}, {t: 'tak', at: W('L5', 20)}, {t: 'semestinya', at: W('L5', 21)}]} size={90} color={C.faint} />
        <Line toks={[{t: 'semua', at: W('L5', 22)}, {t: 'orang.', at: W('L5', 23)}]} size={90} color={C.faint} />
      </div>
      <Tag text="Eastwood et al., 2012 (definisi bosan)" at={W('L5', 19)} style={{left: 60, width: 900, textAlign: 'center', top: 1478}} />
    </Shell>
  );
};
