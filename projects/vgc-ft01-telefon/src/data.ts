import vo from './vo.json';
import events from './events.json';
export const DURATION: number = events.duration;
export const SCENES = events.scenes as {id: string; start: number; end: number}[];
export const EV = Object.fromEntries(Object.entries(events.events).map(([k, v]) => [k, (v as {t: number}).t])) as Record<string, number>;
export const VO = vo as Record<string, {start: number; end: number; words: {w: string; t: number}[]}>;
/** masa mula perkataan ke-i (indeks teks skrin) bagi baris L */
export const W = (line: string, i: number): number => VO[line].words[i].t;
