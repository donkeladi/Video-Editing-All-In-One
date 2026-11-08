import React, {useMemo} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';
import {useFonts} from '../Video';
import * as THREE from 'three';
import {RoundedBoxGeometry} from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import {C, F} from '../theme';

const SKIN = '#e9b48c', HOODIE = '#d29c36', JEANS = '#3b5a63', INK = '#263c3d', SHOE = '#f4efe2';
const ease = (a: number, b: number, t: number, e = Easing.inOut(Easing.cubic)) => interpolate(t, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: e});
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;

const Phone: React.FC<{lit: number}> = ({lit}) => {
  const body = useMemo(() => new RoundedBoxGeometry(0.17, 0.34, 0.025, 4, 0.025), []);
  const glass = useMemo(() => new RoundedBoxGeometry(0.15, 0.31, 0.004, 4, 0.018), []);
  return (
    <group>
      <mesh geometry={body} castShadow><meshStandardMaterial color="#1f2d2e" roughness={0.35} metalness={0.5} /></mesh>
      <mesh geometry={glass} position={[0, 0, 0.0135]}>
        <meshStandardMaterial color={lit > 0.01 ? '#ffd37a' : '#0b1214'} emissive={'#ffb938'} emissiveIntensity={lit * 1.4} roughness={0.15} metalness={0.2} />
      </mesh>
    </group>
  );
};

const Eye: React.FC<{x: number; look: THREE.Vector2; blink: number}> = ({x, look, blink}) => (
  <group position={[x, 0.03, 0.27]} scale={[1, Math.max(0.08, blink), 1]}>
    <mesh><sphereGeometry args={[0.062, 24, 24]} /><meshStandardMaterial color="#ffffff" roughness={0.25} /></mesh>
    <mesh position={[look.x * 0.02, look.y * 0.02, 0.045]}><sphereGeometry args={[0.032, 20, 20]} /><meshStandardMaterial color="#1b2a2b" roughness={0.2} /></mesh>
    <mesh position={[look.x * 0.02 + 0.012, look.y * 0.02 + 0.014, 0.072]}><sphereGeometry args={[0.009, 12, 12]} /><meshBasicMaterial color="#fff" /></mesh>
  </group>
);

const Character: React.FC<{t: number}> = ({t}) => {
  const bob = Math.sin(t * 2.4) * 0.012;
  const raise = ease(1.2, 2.0, t);               // lengan naik
  const tap = t > 2.6 ? Math.max(0, 1 - Math.abs(((t - 2.6) % 0.5) - 0.12) / 0.12) : 0; // ketuk
  const headDown = ease(1.6, 2.2, t);
  const lookAround = Math.sin(t * 1.6) * (1 - raise);
  const blink = ((t * 1000) % 3100) < 120 ? 0.1 : 1;
  const lit = ease(2.7, 2.95, t);
  // lengan kanan (watak): bahu → siku
  const shoulderX = lerp(0.05, -1.05, raise);
  const elbowX = lerp(-0.1, -1.55, raise);
  const handTap = tap * 0.05;
  const sleeveMat = <meshStandardMaterial color={HOODIE} roughness={0.8} />;
  const skin = <meshStandardMaterial color={SKIN} roughness={0.55} />;
  return (
    <group position={[0, bob, 0]} rotation={[0, lerp(-0.25, 0.1, raise), 0]}>
      {/* kaki */}
      {[-0.13, 0.13].map((x) => (
        <group key={x} position={[x, 0.55, 0]}>
          <mesh position={[0, -0.27, 0]} castShadow><capsuleGeometry args={[0.095, 0.4, 8, 16]} /><meshStandardMaterial color={JEANS} roughness={0.85} /></mesh>
          <mesh position={[0, -0.56, 0.05]} castShadow scale={[1, 0.6, 1.5]}><sphereGeometry args={[0.105, 16, 16]} /><meshStandardMaterial color={SHOE} roughness={0.6} /></mesh>
        </group>
      ))}
      {/* badan */}
      <mesh position={[0, 0.95, 0]} castShadow scale={[1.05, 1, 0.82]}><capsuleGeometry args={[0.24, 0.38, 10, 24]} />{sleeveMat}</mesh>
      <mesh position={[0, 0.84, 0.19]} castShadow><boxGeometry args={[0.2, 0.09, 0.03]} />{sleeveMat}</mesh>
      {/* leher + kepala */}
      <mesh position={[0, 1.27, 0]}><cylinderGeometry args={[0.07, 0.08, 0.1, 16]} />{skin}</mesh>
      <group position={[0, 1.5, 0]} rotation={[headDown * 0.38, lookAround * 0.45, lookAround * 0.06]}>
        <mesh castShadow><sphereGeometry args={[0.29, 40, 40]} />{skin}</mesh>
        <mesh position={[0, 0.045, -0.01]} rotation={[-0.12, 0, 0]} castShadow><sphereGeometry args={[0.31, 40, 40, 0, Math.PI * 2, 0, Math.PI * 0.52]} /><meshStandardMaterial color={INK} roughness={0.7} /></mesh>
        <mesh position={[0.2, 0.0, -0.04]} castShadow><sphereGeometry args={[0.13, 20, 20]} /><meshStandardMaterial color={INK} roughness={0.7} /></mesh>
        <mesh position={[-0.285, -0.02, 0.0]} scale={[0.5, 1, 0.6]}><sphereGeometry args={[0.06, 16, 16]} />{skin}</mesh>
        <mesh position={[0.285, -0.02, 0.0]} scale={[0.5, 1, 0.6]}><sphereGeometry args={[0.06, 16, 16]} />{skin}</mesh>
        <Eye x={-0.105} look={new THREE.Vector2(lookAround * 0.6, -headDown * 0.8)} blink={blink} />
        <Eye x={0.105} look={new THREE.Vector2(lookAround * 0.6, -headDown * 0.8)} blink={blink} />
        {[-0.105, 0.105].map((x) => <mesh key={x} position={[x, 0.115, 0.265]} rotation={[0, 0, x * 0.5 * (raise > 0.5 ? 1 : -0.4)]}><boxGeometry args={[0.1, 0.018, 0.02]} /><meshStandardMaterial color={INK} /></mesh>)}
        <mesh position={[0, -0.1, 0.275]} rotation={[0, 0, Math.PI]}><torusGeometry args={[0.04, 0.009, 8, 20, Math.PI]} /><meshStandardMaterial color="#8a4b3a" /></mesh>
        {[-0.17, 0.17].map((x) => <mesh key={x} position={[x, -0.055, 0.235]} scale={[1, 0.7, 0.3]}><sphereGeometry args={[0.05, 16, 16]} /><meshStandardMaterial color="#f2a08a" roughness={0.9} transparent opacity={0.55} /></mesh>)}
      </group>
      {/* lengan kiri (tergantung) */}
      <group position={[-0.27, 1.15, 0]} rotation={[0.05, 0, 0.12]}>
        <mesh position={[0, -0.2, 0]} castShadow><capsuleGeometry args={[0.07, 0.3, 8, 16]} />{sleeveMat}</mesh>
        <mesh position={[0, -0.47, 0]} castShadow><sphereGeometry args={[0.07, 16, 16]} />{skin}</mesh>
      </group>
      {/* lengan kanan (pegang telefon) */}
      <group position={[0.27, 1.15, 0.02]} rotation={[shoulderX, 0, -0.12]}>
        <mesh position={[0, -0.2, 0]} castShadow><capsuleGeometry args={[0.07, 0.3, 8, 16]} />{sleeveMat}</mesh>
        <group position={[0, -0.4, 0]} rotation={[elbowX, 0, 0]}>
          <mesh position={[0, -0.18, 0]} castShadow><capsuleGeometry args={[0.062, 0.26, 8, 16]} />{sleeveMat}</mesh>
          <mesh position={[0, -0.38, 0]} castShadow><sphereGeometry args={[0.07, 16, 16]} />{skin}</mesh>
          <group position={[0, -0.5 + handTap * -1, 0.1]} rotation={[-(shoulderX + elbowX) - 0.22 * raise, 0, 0]}><Phone lit={lit} /></group>
        </group>
      </group>
    </group>
  );
};

const LookAt: React.FC<{y: number}> = ({y}) => {
  const {camera} = useThree();
  camera.lookAt(0, y, 0);
  return null;
};

export const Proof3D: React.FC = () => {
  useFonts();
  const frame = useCurrentFrame(); const {fps, width, height} = useVideoConfig();
  const t = frame / fps;
  const cam = lerp(6.2, 5.0, ease(0, 3.4, t, Easing.out(Easing.quad)));
  const camY = lerp(1.15, 1.25, ease(1.2, 3, t));
  const flash = t > 2.7 ? Math.max(0, 1 - (t - 2.7) / 0.35) * 0.35 : 0;
  return (
    <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 38%, #fff8e6 0%, ${C.bg} 55%, #e9dfc4 100%)`}}>
      <ThreeCanvas width={width} height={height} shadows camera={{position: [0, camY, cam], fov: 32, near: 0.1, far: 50}} gl={{antialias: true}}>
        <ambientLight intensity={0.55} />
        <hemisphereLight args={['#fff4dc', '#cdbf9c', 0.65]} />
        <directionalLight position={[2.5, 4.5, 3.5]} intensity={2.4} castShadow shadow-mapSize={[2048, 2048]} shadow-camera-left={-2} shadow-camera-right={2} shadow-camera-top={3} shadow-camera-bottom={-1} shadow-bias={-0.0004} shadow-radius={5} />
        <directionalLight position={[-3, 2, -2.5]} intensity={1.1} color="#ffd9a0" />
        <pointLight position={[0.35, 1.3, 0.9]} intensity={lerp(0, 2.2, ease(2.7, 2.95, t))} color="#ffbf4d" distance={2.4} />
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow><circleGeometry args={[3.2, 64]} /><meshStandardMaterial color="#efe6cf" roughness={1} /></mesh>
        <LookAt y={lerp(1.25, 1.18, ease(1.2, 3, t))} />
        <Character t={t} />
      </ThreeCanvas>
      <AbsoluteFill style={{background: C.accent, mixBlendMode: 'screen', opacity: flash}} />
      <div style={{position: 'absolute', left: 60, width: 960, top: 240, textAlign: 'center', fontFamily: F.hand, fontSize: 170, lineHeight: 1, color: C.ink}}>Tiada<br />notifikasi.</div>
    </AbsoluteFill>
  );
};
