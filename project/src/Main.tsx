import React from 'react';
import {AbsoluteFill, OffthreadVideo, Img, staticFile, useCurrentFrame, spring, interpolate, Easing} from 'remotion';
import cues from './cues.json';

const FPS = 30;
// Warna: ikut kotak produk DS Pharma (ungu + teal)
const C = {bg: '#1b0f3a', purple: '#5b2d9e', accent: '#5be3d6', white: '#ffffff'};
const FONT = 'Inter, "Inter Display", sans-serif';
const SIZES: Record<string, {fs: number; w: number; ls: number}> = {
  big: {fs: 124, w: 900, ls: -3}, huge: {fs: 210, w: 900, ls: -6}, kick: {fs: 46, w: 800, ls: 2}, sub: {fs: 44, w: 500, ls: 0},
};
const sp = (f: number, t: number, cfg = {damping: 15, stiffness: 190, mass: 0.7}) =>
  spring({frame: f - t * FPS, fps: FPS, config: cfg});

// *kata* => warna accent
const Rich: React.FC<{text: string}> = ({text}) => (
  <>{text.split('*').map((p, i) => (i % 2 ? <span key={i} style={{color: C.accent}}>{p}</span> : <span key={i}>{p}</span>))}</>
);

const Line: React.FC<{l: any; t1: number; f: number}> = ({l, t1, f}) => {
  const end = Math.min(l.until ?? t1, t1);
  const s = SIZES[l.size];
  const plain = l.text.replace(/\*/g, '');
  const avail = 900;
  const fs = Math.min(s.fs, avail / (plain.length * (l.size === 'sub' ? 0.5 : 0.68)));
  const inP = sp(f, l.t);
  const outP = interpolate(f, [end * FPS - 6, end * FPS], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic)});
  if (f < l.t * FPS - 1 || f > end * FPS) return null;
  const ty = interpolate(inP, [0, 1], [110, 0]) - outP * 110;
  const isKick = l.size === 'kick';
  return (
    <div style={{overflow: 'hidden', paddingTop: 6, paddingBottom: l.size === 'sub' ? 4 : 10, marginLeft: -4}}>
      <div style={{transform: `translateY(${ty}%) scale(${interpolate(inP, [0, 1], [1.06, 1])})`, transformOrigin: 'left bottom',
        fontFamily: FONT, fontWeight: s.w, fontSize: fs, letterSpacing: s.ls, lineHeight: 1.0, whiteSpace: 'nowrap',
        color: isKick ? C.accent : C.white, textTransform: l.size === 'sub' ? 'none' : 'uppercase',
        textShadow: '0 4px 24px rgba(10,4,30,.65)'}}>
        <Rich text={l.text} />
      </div>
    </div>
  );
};

const Title: React.FC<{t: any; f: number}> = ({t, f}) => {
  if (f < t.t0 * FPS - 1 || f > t.t1 * FPS) return null;
  const chipIn = sp(f, t.chipT);
  const chipOut = interpolate(f, [t.t1 * FPS - 6, t.t1 * FPS], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: 64, top: 96, width: 960}}>
      {t.lines.map((l: any, i: number) => <Line key={i} l={l} t1={t.t1} f={f} />)}
      {t.chip && f >= t.chipT * FPS && (
        <div style={{marginTop: 14, display: 'inline-block', fontFamily: FONT, fontWeight: 700, fontSize: 34, color: C.bg, background: C.accent,
          padding: '8px 22px', borderRadius: 40, transform: `scale(${chipIn}) translateX(${-chipOut * 400}px)`, transformOrigin: 'left center'}}>
          {t.chip}
        </div>
      )}
    </div>
  );
};

const Card: React.FC<{c: any; f: number}> = ({c, f}) => {
  if (f < c.t0 * FPS - 1 || f > c.t1 * FPS + 8) return null;
  const inP = sp(f, c.t0, {damping: 13, stiffness: 150, mass: 0.8});
  const out = interpolate(f, [c.t1 * FPS, c.t1 * FPS + 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic)});
  const x = interpolate(inP, [0, 1], [520, 0]) + out * 520;
  const float = Math.sin((f - c.t0 * FPS) / 14) * 6;
  const rot = c.rot + interpolate(inP, [0, 1], [10, 0]);
  return (
    <div style={{position: 'absolute', right: 40, top: 380 + float, width: c.w, transform: `translateX(${x}px) rotate(${rot}deg)`,
      borderRadius: 30, overflow: 'hidden', background: '#fff', border: '6px solid #fff', boxShadow: '0 24px 60px rgba(10,4,30,.55)'}}>
      <Img src={staticFile(`media/${c.img}.jpg`)} style={{width: '100%', display: 'block'}} />
    </div>
  );
};

const Caption: React.FC<{c: any; f: number}> = ({c, f}) => {
  if (f < c.t0 * FPS || f >= c.t1 * FPS) return null;
  const p = sp(f, c.t0, {damping: 16, stiffness: 260, mass: 0.5});
  return (
    <div style={{position: 'absolute', left: 60, right: 60, bottom: 310, display: 'flex', justifyContent: 'center'}}>
      <div style={{transform: `translateY(${interpolate(p, [0, 1], [28, 0])}px) scale(${interpolate(p, [0, 1], [0.9, 1])})`, opacity: Math.min(1, p * 3),
        background: 'rgba(27,15,58,.78)', borderRadius: 30, padding: '16px 30px', fontFamily: FONT, fontWeight: 800, fontSize: 60, lineHeight: 1.15,
        color: C.white, textAlign: 'center', maxWidth: 960}}>
        <Rich text={c.text} />
      </div>
    </div>
  );
};

export const Main: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  // Punch-in: selang tiap potongan jump-cut (1.0 / 1.1) + tolak perlahan
  const si = Math.max(0, cues.segs.findIndex((s: any) => t >= s.t0 && t < s.t1));
  const seg: any = cues.segs[si] ?? cues.segs[0];
  const base = si % 2 ? 1.1 : 1.0;
  const push = interpolate(t, [seg.t0, seg.t1], [0, 0.035], {extrapolateRight: 'clamp'});
  const pop = interpolate(t - seg.t0, [0, 0.18], [0.03, 0], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const scale = base + push + pop;
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <AbsoluteFill style={{transform: `scale(${scale})`, transformOrigin: '45% 38%'}}>
        <OffthreadVideo src={staticFile('media/cut.mp4')} volume={0} />
      </AbsoluteFill>
      <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: 700, background: 'linear-gradient(180deg, rgba(27,15,58,.86) 0%, rgba(27,15,58,.55) 45%, rgba(27,15,58,0) 100%)'}} />
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 620, background: 'linear-gradient(0deg, rgba(27,15,58,.8) 0%, rgba(27,15,58,0) 100%)'}} />
      {cues.cards.map((c: any, i: number) => <Card key={i} c={c} f={f} />)}
      {cues.titles.map((tt: any, i: number) => <Title key={i} t={tt} f={f} />)}
      {cues.caps.map((c: any, i: number) => <Caption key={i} c={c} f={f} />)}
    </AbsoluteFill>
  );
};
