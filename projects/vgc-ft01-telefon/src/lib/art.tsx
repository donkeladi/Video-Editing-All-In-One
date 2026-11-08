import React from 'react';
import {C} from '../theme';
import {Stroke, Pop, rr, prog, eo, clamp} from './ui';

/** Telefon lukisan tangan. Pusat pada (x,y), saiz asas 220x420. */
export const Phone: React.FC<{x: number; y: number; s?: number; rot?: number; t: number; draw?: number; lit?: number; tap?: number; content?: 'lock' | 'eyes' | 'q' | 'none'}> = ({x, y, s = 1, rot = 0, t, draw = 0, lit, tap, content = 'lock'}) => {
  const L = lit !== undefined && t >= lit ? eo(prog(t, lit, 0.25)) : 0;
  const shake = lit !== undefined && t >= lit && t < lit + 0.3 ? Math.sin((t - lit) * 90) * 5 * (1 - (t - lit) / 0.3) : 0;
  return (
    <g transform={`translate(${x + shake} ${y}) rotate(${rot}) scale(${s})`}>
      {L > 0 && [...Array(8)].map((_, i) => {
        const a = (i / 8) * Math.PI * 2 + 0.2, r1 = 250 + 10 * L, r2 = r1 + 40 * L;
        return <line key={i} x1={Math.cos(a) * r1 * 0.62} y1={Math.sin(a) * r1 * 0.9} x2={Math.cos(a) * r2 * 0.62} y2={Math.sin(a) * r2 * 0.9} stroke={C.accent} strokeWidth={9} strokeLinecap="round" opacity={clamp(1.6 - L * 0.6) * L} />;
      })}
      <Stroke d={rr(-110, -210, 220, 420, 36, 3)} t={t} s={draw} dur={0.5} w={8} fill={C.paper} />
      <Stroke d={rr(-92, -184, 184, 368, 18, 5, 2)} t={t} s={draw + 0.25} dur={0.35} w={4} />
      <Stroke d="M-26 -198 L26 -198" t={t} s={draw + 0.4} dur={0.15} w={5} />
      {L > 0 && <rect x={-90} y={-182} width={180} height={364} rx={16} fill={C.accent} opacity={0.35 * L} />}
      {L > 0 && content === 'lock' && <g opacity={L}><circle cx={0} cy={-90} r={30} fill="none" stroke={C.ink} strokeWidth={6} /><path d="M0 -90 L0 -108 M0 -90 L14 -82" stroke={C.ink} strokeWidth={6} strokeLinecap="round" /><path d="M-60 0 Q-30 -10 0 0 T60 0" fill="none" stroke={C.ink} strokeWidth={6} strokeLinecap="round" /><path d="M-60 40 Q-30 30 0 40 T40 40" fill="none" stroke={C.ink} strokeWidth={6} strokeLinecap="round" /></g>}
      {content === 'q' && L > 0 && <text x={0} y={50} textAnchor="middle" fontFamily='"Caveat Brush"' fontSize={230} fill={C.ink} opacity={L}>?</text>}
      {content === 'eyes' && L > 0 && <g opacity={L}><circle cx={-42} cy={-10} r={34} fill="#fff" stroke={C.ink} strokeWidth={6} /><circle cx={42} cy={-10} r={34} fill="#fff" stroke={C.ink} strokeWidth={6} /><circle cx={-34 + 6 * Math.sin(t * 2)} cy={-4} r={13} fill={C.ink} /><circle cx={50 + 6 * Math.sin(t * 2)} cy={-4} r={13} fill={C.ink} /></g>}
      {tap !== undefined && t >= tap && [0, 0.12].map((d, i) => {
        const p = prog(t, tap + d, 0.5);
        return <circle key={i} cx={20} cy={80} r={14 + 70 * eo(p)} fill="none" stroke={C.ink} strokeWidth={6} opacity={(1 - p) * (p > 0 ? 1 : 0)} />;
      })}
    </g>
  );
};

type IconKind = 'bubble' | 'call' | 'bell' | 'spark' | 'eye' | 'target' | 'clock' | 'hand';
const ICONS: Record<IconKind, string[]> = {
  bubble: ['M12 18 Q12 10 20 10 L80 10 Q88 10 88 18 L88 58 Q88 66 80 66 L44 66 L26 86 L28 66 L20 66 Q12 66 12 58 Z', 'M34 38 L35 38 M50 38 L51 38 M66 38 L67 38'],
  call: ['M22 14 Q30 8 36 18 L42 30 Q44 36 38 40 Q36 42 42 52 Q50 62 58 64 Q62 62 64 60 Q68 56 74 60 L84 68 Q92 74 84 84 Q74 92 56 84 Q30 72 16 46 Q8 28 22 14 Z'],
  bell: ['M50 10 C30 10 26 28 26 44 C26 58 20 64 14 72 L86 72 C80 64 74 58 74 44 C74 28 70 10 50 10 Z', 'M40 82 Q50 94 60 82'],
  spark: ['M50 6 Q55 44 94 50 Q55 56 50 94 Q45 56 6 50 Q45 44 50 6 Z'],
  eye: ['M6 50 Q50 6 94 50 Q50 94 6 50 Z', 'M50 34 a16 16 0 1 0 0.1 0 Z'],
  target: ['M50 8 a42 42 0 1 0 0.1 0 Z', 'M50 28 a22 22 0 1 0 0.1 0 Z', 'M50 46 a4 4 0 1 0 0.1 0 Z'],
  clock: ['M50 8 a42 42 0 1 0 0.1 0 Z', 'M50 50 L50 24 M50 50 L70 60'],
  hand: ['M30 90 L30 44 Q30 36 38 38 L40 22 Q42 14 50 18 L52 20 Q60 12 66 20 L68 26 Q76 20 80 28 L82 58 Q82 80 64 90 Z'],
};
/** Ikon lukisan tangan (kotak 100x100). Pusat (x,y), saiz size px. cross = masa pangkah. */
export const Icon: React.FC<{kind: IconKind; x: number; y: number; size?: number; t: number; at: number; cross?: number; fill?: string; w?: number}> = ({kind, x, y, size = 160, t, at, cross, fill = C.accentSoft, w = 6}) => {
  const k = size / 100;
  return (
    <g transform={`translate(${x - size / 2} ${y - size / 2}) scale(${k})`}>
      <Pop t={t} s={at}>
        {ICONS[kind].map((d, i) => <Stroke key={i} d={d} t={t} s={at} dur={0.35} w={w / k * 1.0 + 1} fill={i === 0 ? fill : undefined} />)}
      </Pop>
      {cross !== undefined && <>
        <Stroke d="M8 12 L92 90" t={t} s={cross} dur={0.14} w={11} />
        <Stroke d="M92 10 L10 90" t={t} s={cross + 0.1} dur={0.14} w={11} />
      </>}
    </g>
  );
};

/** Orang ringkas (pandangan hadapan). pose: stand | sit | lie. Origin di tapak kaki (0,0). */
export const Person: React.FC<{pose: 'stand' | 'sit' | 'lie'; t: number; s: number; lit?: number; tap?: number}> = ({pose, t, s, lit, tap}) => {
  const hair = 'M-44 -448 Q-34 -494 0 -490 Q36 -494 44 -450 Q20 -470 -4 -464 Q-26 -462 -44 -448 Z';
  const face = (dy = 0, bored = false) => <g>
    <path d={`M-16 ${-440 + dy} l0.1 0 M16 ${-440 + dy} l0.1 0`} stroke={C.ink} strokeWidth={11} strokeLinecap="round" />
    <path d={bored ? `M-10 ${-418 + dy} L10 ${-418 + dy}` : `M-11 ${-420 + dy} Q0 ${-412 + dy} 11 ${-420 + dy}`} stroke={C.ink} strokeWidth={5} strokeLinecap="round" fill="none" />
  </g>;
  if (pose === 'lie') {
    return (
      <g transform={`scale(${s})`}>
        <Stroke d="M-330 -30 L330 -30 L330 20 L-330 20 Z" t={t} s={0} dur={0.3} fill={C.accentSoft} />
        <Stroke d="M-330 -30 L-330 -100" t={t} s={0.15} dur={0.2} />
        <Stroke d="M-318 -100 Q-250 -76 -150 -92 L-150 -44 L-318 -44 Z" t={t} s={0.2} dur={0.3} fill={C.paper} />
        <Stroke d="M-130 -50 Q-90 -170 40 -140 Q200 -150 320 -40 Z" t={t} s={0.35} dur={0.4} fill={C.accentSoft} />
        <g transform="translate(-230 -90) rotate(-90)">
          <Stroke d="M-40 -150 a40 40 0 1 0 0.1 0" t={t} s={0.3} dur={0.35} fill={C.paper} />
        </g>
        <Stroke d="M-250 -128 Q-248 -150 -214 -146" t={t} s={0.55} dur={0.2} w={9} />
        <circle cx={-246} cy={-92} r={5} fill={C.ink} /><circle cx={-216} cy={-92} r={5} fill={C.ink} />
        <Stroke d="M-212 -52 Q-190 -150 -210 -250" t={t} s={0.6} dur={0.3} w={8} />
        <Phone x={-205} y={-300} s={0.4} rot={6} t={t} draw={0.6} lit={lit} tap={tap} content="lock" />
      </g>
    );
  }
  const stool = pose === 'sit';
  return (
    <g transform={`scale(${s})`}>
      {stool && <><Stroke d="M-110 -170 L110 -170" t={t} s={0} dur={0.25} w={9} /><Stroke d="M-80 -170 L-90 0 M80 -170 L90 0" t={t} s={0.1} dur={0.25} /></>}
      <Stroke d={`M-28 ${stool ? -170 : -214} L-32 0 M28 ${stool ? -170 : -214} L32 0 M-54 0 L-12 0 M12 0 L54 0`} t={t} s={0.05} dur={0.35} />
      <Stroke d="M-56 -392 Q0 -412 56 -392 L66 -214 L-66 -214 Z" t={t} s={0.15} dur={0.4} fill={C.accentSoft} />
      <Stroke d="M-56 -380 Q-90 -300 -78 -228" t={t} s={0.3} dur={0.3} />
      <Stroke d="M56 -380 Q100 -330 44 -296" t={t} s={0.35} dur={0.3} />
      <Stroke d="M-42 -440 a42 42 0 1 0 84 0 a42 42 0 1 0 -84 0" t={t} s={0.25} dur={0.35} fill={C.paper} />
      <Stroke d={hair} t={t} s={0.4} dur={0.3} fill={C.ink} />
      {t > 0.5 && face(0, pose === 'stand' && false)}
      <Phone x={30} y={-326} s={0.36} rot={-8} t={t} draw={0.45} lit={lit} tap={tap} content="lock" />
    </g>
  );
};
