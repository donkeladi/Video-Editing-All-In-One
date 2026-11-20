import React from 'react';
import {Composition} from 'remotion';
import {Main} from './Main';
import cues from './cues.json';
export const FPS = 30;
export const Root: React.FC = () => (
  <Composition id="Main" component={Main} durationInFrames={Math.ceil(cues.duration * FPS)} fps={FPS} width={1080} height={1920} />
);
