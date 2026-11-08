import React from 'react';
import {Composition} from 'remotion';
import {Video} from './Video';
import {DURATION} from './data';
import {FPS, H, W} from './theme';

export const Root: React.FC = () => (
  <Composition id="Main" component={Video} durationInFrames={Math.round(DURATION * FPS)} fps={FPS} width={W} height={H} />
);
