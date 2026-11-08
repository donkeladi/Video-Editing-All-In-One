import React from 'react';
import {Composition} from 'remotion';
import {Video} from './Video';
import {Proof3D} from './three/Proof3D';
import {DURATION} from './data';
import {FPS, H, W} from './theme';

export const Root: React.FC = () => (
  <>
  <Composition id="Proof3D" component={Proof3D} durationInFrames={150} fps={FPS} width={W} height={H} />
  <Composition id="Main" component={Video} durationInFrames={Math.round(DURATION * FPS)} fps={FPS} width={W} height={H} />
  </>
);
