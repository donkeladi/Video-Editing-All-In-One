import React, {createContext, useContext} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, F} from '../theme';

export const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const eo = (x: number) => 1 - Math.pow(1 - clamp(x), 3);
export const eob = (x: number) => { const c1 = 2.0, c3 = c1 + 1, p = clamp(x); return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
export const prog = (t: number, s: number, d: number) => clamp((t - s) / d);

export const SceneCtx = createContext({start: 0, end: 1, first: false, last: false});
/** masa mutlak (saat) pada garis masa video */
export const useT = () => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig(); const c = useContext(SceneCtx);
  return c.start + f / fps;
};

/** Pembungkus babak: zoom-through masuk/keluar, slow push, rupa lukisan tangan (filter). */
export const Shell: React.FC<{children: React.ReactNode}> = ({children}) => {
  const t = useT(); const {start, end, first, last} = useContext(SceneCtx);
  const lt = t - start, dur = end - start;
  const inP = first ? 1 : eo(prog(lt, 0, 0.28));
  const outP = last ? 0 : clamp((lt - (dur - 0.14)) / 0.14);
  const sc = (1 + 0.035 * (lt / dur)) * (1 + 0.1 * (1 - inP)) * (1 + 0.08 * eo(outP));
  const blur = 8 * (1 - inP) + 6 * outP;
  return (
    <AbsoluteFill style={{transform: `scale(${sc})`, filter: `blur(${blur.toFixed(2)}px) url(#rough)`}}>{children}</AbsoluteFill>
  );
};

export type Tok = {t: string; at: number; hl?: number; c?: string; slam?: boolean};
/** Baris teks tulisan tangan: perkataan masuk ikut masa (atau instan jika at <= mula babak). */
export const Line: React.FC<{toks: Tok[]; size: number; font?: string; color?: string; weight?: number; gap?: number; lh?: number}> = ({toks, size, font = F.hand, color = C.ink, weight = 400, gap, lh = 1.05}) => {
  const t = useT(); const {start} = useContext(SceneCtx);
  return (
    <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', columnGap: gap ?? size * 0.26, rowGap: 0, lineHeight: lh}}>
      {toks.map((k, i) => {
        const instant = k.at <= start + 0.05;
        const p = instant ? 1 : prog(t, k.at, 0.28);
        const sp = k.slam ? prog(t, k.at, 0.2) : 0;
        const scale = k.slam ? (t < k.at ? 1.3 : 1 + 0.3 * (1 - eo(sp))) : 0.86 + 0.14 * eob(p);
        const op = instant ? 1 : clamp(p * 8);
        const hl = k.hl !== undefined ? eo(prog(t, k.hl, 0.4)) : 0;
        return (
          <span key={i} style={{position: 'relative', display: 'inline-block', opacity: op, transform: `translateY(${(1 - eo(p)) * (instant ? 0 : 16)}px) scale(${scale})`}}>
            {k.hl !== undefined && <span style={{position: 'absolute', left: -10, right: -10, top: '50%', bottom: '2%', background: C.accent, opacity: 0.55, borderRadius: 6, transform: `scaleX(${hl}) skewX(-4deg)`, transformOrigin: 'left center'}} />}
            <span style={{position: 'relative', fontFamily: font, fontSize: size, color: k.c ?? color, fontWeight: weight}}>{k.t}</span>
          </span>
        );
      })}
    </div>
  );
};

/** Label sumber / ilustrasi (Inter, >= 26px). */
export const Tag: React.FC<{text: string; at: number; style?: React.CSSProperties}> = ({text, at, style}) => {
  const t = useT(); const p = eo(prog(t, at, 0.3));
  return <div style={{position: 'absolute', fontFamily: F.label, fontWeight: 600, fontSize: 28, color: C.faint, opacity: p, ...style}}>{text}</div>;
};

/** Bentuk tangan dengan jitter ringan (rr = rounded rect). */
const rnd = (n: number) => { const x = Math.sin(n * 127.1) * 43758.5453; return x - Math.floor(x); };
export const rr = (x: number, y: number, w: number, h: number, r: number, seed = 1, j = 3) => {
  const o = (i: number) => (rnd(seed * 13 + i) - 0.5) * j;
  return `M${x + r + o(1)} ${y + o(2)} L${x + w - r + o(3)} ${y + o(4)} Q${x + w + o(5)} ${y + o(6)} ${x + w + o(7)} ${y + r} L${x + w + o(8)} ${y + h - r} Q${x + w} ${y + h} ${x + w - r} ${y + h + o(9)} L${x + r} ${y + h + o(10)} Q${x} ${y + h} ${x + o(11)} ${y + h - r} L${x + o(12)} ${y + r} Q${x} ${y} ${x + r + 2} ${y + 1}`;
};

/** Garis yang dilukis (stroke-dash). t = masa mutlak, s = masa mula. */
export const Stroke: React.FC<{d: string; t: number; s: number; dur?: number; color?: string; w?: number; fill?: string; op?: number; dash?: string}> = ({d, t, s, dur = 0.45, color = C.ink, w = 7, fill, op = 1, dash}) => {
  const p = eo(prog(t, s, dur));
  if (p <= 0.001) return null;
  return (
    <g opacity={op}>
      {fill && <path d={d} fill={fill} opacity={clamp((p - 0.55) / 0.45)} transform="translate(5 4)" />}
      <path d={d} fill="none" stroke={color} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={dash ?? '1 1'} strokeDashoffset={dash ? 0 : 1 - p} opacity={dash ? p : 1} />
    </g>
  );
};

/** Pop masuk dengan overshoot (SVG). */
export const Pop: React.FC<{t: number; s: number; children: React.ReactNode; from?: number}> = ({t, s, children, from = 0.45}) => {
  const p = prog(t, s, 0.32);
  if (t < s) return null;
  const sc = from + (1 - from) * eob(p);
  return <g style={{transformBox: 'fill-box', transformOrigin: 'center', transform: `scale(${sc})`, opacity: clamp(p * 6)}}>{children}</g>;
};
