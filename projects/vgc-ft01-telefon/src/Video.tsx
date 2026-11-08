import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Sequence, continueRender, delayRender, staticFile, useCurrentFrame} from 'remotion';
import {C, FPS} from './theme';
import {SCENES} from './data';
import {SceneCtx} from './lib/ui';
import {S1} from './scenes/S1'; import {S2} from './scenes/S2'; import {S3} from './scenes/S3'; import {S4} from './scenes/S4';
import {S5} from './scenes/S5'; import {S6} from './scenes/S6'; import {S7} from './scenes/S7'; import {S8} from './scenes/S8';

const COMP = [S1, S2, S3, S4, S5, S6, S7, S8];

const useFonts = () => {
  const [h] = useState(() => delayRender('fonts'));
  useEffect(() => {
    const faces = [
      new FontFace('Caveat Brush', `url(${staticFile('fonts/caveat-brush-latin-400-normal.woff2')})`, {weight: '400'}),
      new FontFace('Inter', `url(${staticFile('fonts/inter-latin-600-normal.woff2')})`, {weight: '600'}),
      new FontFace('Inter', `url(${staticFile('fonts/inter-latin-700-normal.woff2')})`, {weight: '700'}),
    ];
    Promise.all(faces.map((f) => f.load())).then((l) => { l.forEach((f) => document.fonts.add(f)); continueRender(h); });
  }, [h]);
};

export const Video: React.FC = () => {
  useFonts();
  const f = useCurrentFrame();
  const seed = Math.floor(f / 3) % 7 + 1; // "line boil" halus
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <svg width={0} height={0} style={{position: 'absolute'}}>
        <defs>
          <filter id="rough" x="-2%" y="-2%" width="104%" height="104%">
            <feTurbulence type="fractalNoise" baseFrequency="0.014" numOctaves={2} seed={seed} result="n" />
            <feDisplacementMap in="SourceGraphic" in2="n" scale={4} xChannelSelector="R" yChannelSelector="G" />
          </filter>
        </defs>
      </svg>
      {SCENES.map((s, i) => {
        const Comp = COMP[i];
        const from = Math.round(s.start * FPS), to = i === SCENES.length - 1 ? Math.round(s.end * FPS) : Math.round(SCENES[i + 1].start * FPS);
        return (
          <Sequence key={s.id} from={from} durationInFrames={to - from}>
            <SceneCtx.Provider value={{start: from / FPS, end: to / FPS, first: i === 0, last: i === SCENES.length - 1}}>
              <Comp />
            </SceneCtx.Provider>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
