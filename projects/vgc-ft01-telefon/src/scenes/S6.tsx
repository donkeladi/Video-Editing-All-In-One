import React from 'react';
import {C, F} from '../theme';
import {EV, W, SCENES} from '../data';
import {Shell, Line, useT, Stroke, rr, eo, eob, prog} from '../lib/ui';
import {Person} from '../lib/art';

const card1 = SCENES[5].start, card2 = EV.s6_c2 + 0.14, card3 = EV.s6_c3 + 0.12;

export const S6: React.FC = () => {
  const t = useT();
  const idx = t >= card3 ? 2 : t >= card2 ? 1 : 0;
  const start = [card1, card2, card3][idx];
  const lt = t - start;
  const land = eob(prog(lt, 0, 0.3));
  const caps = [['Tunggu lif', 'Tangan dah capai.', W('L6', 0), W('L6', 2)], ['Rehat sekejap', 'Skrin dah nyala.', W('L6', 5), W('L6', 7)], ['Sebelum tidur', '“Satu minit je…”', W('L6', 10), W('L6', 12)]] as const;
  const cap = caps[idx];
  const tapT = [EV.s6_t1, EV.s6_t2, EV.s6_t3][idx] - start;
  return (
    <Shell>
      <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: 1920, transform: `translateY(${(1 - land) * 60}px) rotate(${(1 - land) * (idx % 2 ? 2 : -2)}deg)`}}>
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          <Stroke d={rr(150, 300, 780, 860, 40, 7, 4)} t={lt} s={0} dur={0.3} w={8} fill={C.paper} />
          <g transform="translate(540 1070)">
            {idx === 0 && <>
              <Stroke d={rr(-330, -560, 260, 560, 8, 11)} t={lt} s={0.05} dur={0.3} w={7} />
              <Stroke d="M-200 -560 L-200 0" t={lt} s={0.2} dur={0.2} w={5} />
              <Stroke d="M-40 -330 L-10 -330 L-25 -360 Z" t={lt} s={0.3} dur={0.2} w={5} fill={C.accentSoft} />
              <g transform="translate(120 0)"><Person pose="stand" t={lt} s={0.92} lit={tapT + 0.0} tap={tapT - 0.05} /></g>
            </>}
            {idx === 1 && <>
              <g transform="translate(-30 0)"><Person pose="sit" t={lt} s={0.92} lit={tapT} tap={tapT - 0.05} /></g>
              <Stroke d="M190 -120 L330 -120 M260 -120 L260 0" t={lt} s={0.2} dur={0.25} w={7} />
              <Stroke d="M215 -120 L225 -190 L305 -190 L315 -120" t={lt} s={0.3} dur={0.25} w={7} fill={C.accentSoft} />
              <Stroke d="M240 -215 Q225 -240 245 -262 M270 -215 Q255 -240 275 -262" t={lt} s={0.45} dur={0.3} w={5} />
            </>}
            {idx === 2 && <>
              <Stroke d="M-290 -300 a46 46 0 1 0 60 70 a38 38 0 1 1 -60 -70 Z" t={lt} s={0.3} dur={0.4} fill={C.accent} w={6} />
              <Stroke d="M230 -430 l0.1 0 M300 -380 l0.1 0 M170 -360 l0.1 0" t={lt} s={0.5} dur={0.2} w={14} color={C.accent} />
              <g transform="translate(40 -40)"><Person pose="lie" t={lt} s={0.95} lit={tapT} tap={tapT - 0.05} /></g>
            </>}
          </g>
        </svg>
        <div style={{position: 'absolute', left: 190, top: 330, fontFamily: F.label, fontWeight: 700, fontSize: 28, color: C.faint, border: `3px solid ${C.faint}`, borderRadius: 20, padding: '2px 16px'}}>Ilustrasi</div>
      </div>
      <div style={{position: 'absolute', left: 60, width: 900, top: 1215}}>
        <Line key={'a' + idx} toks={[{t: cap[0].split(' ')[0], at: cap[2]}, {t: cap[0].split(' ')[1], at: cap[2] + 0.2, hl: cap[2] + 0.3}]} size={116} />
      </div>
      <div style={{position: 'absolute', left: 60, width: 900, top: 1370}}>
        <Line key={'b' + idx} toks={cap[1].split(' ').map((w, i) => ({t: w, at: cap[3] + i * 0.2}))} size={64} color={C.faint} />
      </div>
    </Shell>
  );
};
