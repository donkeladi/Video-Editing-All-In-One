import React from 'react';
import {C, F} from '../theme';
import {EV, W} from '../data';
import {Shell, Line, Tag, useT, Stroke, Pop} from '../lib/ui';
import {Phone, Icon} from '../lib/art';

export const S3: React.FC = () => {
  const t = useT();
  return (
    <Shell>
      <div style={{position: 'absolute', left: 60, width: 900, top: 262}}>
        <Line toks={[{t: 'Rupanya…', at: W('L3', 0)}, {t: 'tindakan', at: W('L3', 1)}, {t: 'ni', at: W('L3', 2)}, {t: 'ada', at: W('L3', 3)}, {t: 'nama:', at: W('L3', 4)}]} size={66} color={C.faint} />
      </div>
      <div style={{position: 'absolute', left: 60, width: 900, top: 380}}>
        <Line toks={[{t: 'spontaneous', at: W('L3', 5), slam: true}]} size={148} />
        <Line toks={[{t: 'smartphone', at: W('L3', 6), slam: true}]} size={148} />
        <Line toks={[{t: 'checking', at: W('L3', 7), slam: true, hl: W('L3', 7) + 0.1}]} size={148} />
      </div>
      <div style={{position: 'absolute', left: 60, width: 900, top: 905}}>
        <Line toks={[{t: 'Perhatian', at: W('L3', 8)}, {t: 'tertarik', at: W('L3', 9)}, {t: 'ke', at: W('L3', 10)}, {t: 'telefon,', at: W('L3', 11)}]} size={64} />
        <Line toks={[{t: 'tanpa', at: W('L3', 12)}, {t: 'notifikasi,', at: W('L3', 13)}]} size={64} />
        <Line toks={[{t: 'tanpa', at: W('L3', 14)}, {t: 'tujuan', at: W('L3', 15)}, {t: 'khusus.', at: W('L3', 16)}]} size={64} />
      </div>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <Icon kind="eye" x={170} y={1330} size={170} t={t} at={EV.s3_eye} />
        <Stroke d="M270 1330 Q330 1300 390 1330" t={t} s={EV.s3_eye + 0.15} dur={0.4} w={7} />
        <Stroke d="M372 1306 L394 1332 L364 1344" t={t} s={EV.s3_eye + 0.5} dur={0.15} w={7} />
        <Phone x={520} y={1330} s={0.46} t={t} draw={EV.s3_eye - 0.1} lit={EV.s3_eye + 0.6} content="none" />
        <Icon kind="bell" x={830} y={1250} size={110} t={t} at={EV.s3_bell} cross={EV.s3_x1} />
        <Icon kind="target" x={850} y={1400} size={110} t={t} at={EV.s3_tgt} cross={EV.s3_x2} />
      </svg>
      <Tag text="Berntsen et al., 2023" at={W('L3', 14)} style={{left: 60, width: 900, textAlign: 'center', top: 1478}} />
    </Shell>
  );
};
