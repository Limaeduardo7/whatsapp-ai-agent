import React from 'react';
import {AbsoluteFill, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

const BG: React.CSSProperties = {
  background: 'radial-gradient(circle at 20% 20%, #1f2a68 0%, #0b0f24 40%, #06070f 100%)',
};

const Character: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const bob = Math.sin(frame / 8) * 18;
  const breathe = 1 + Math.sin(frame / 18) * 0.02;
  const entrance = spring({frame, fps, config: {damping: 14, stiffness: 90}});

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        transform: `translateY(${(1 - entrance) * 220 + bob}px) scale(${breathe})`,
      }}
    >
      <Img
        src={staticFile('pixel.jpg')}
        style={{
          width: 920,
          height: 1635,
          objectFit: 'contain',
          borderRadius: 24,
          boxShadow: '0 0 80px rgba(93, 184, 255, 0.35)',
        }}
      />
    </div>
  );
};

const ReactBitsCard: React.FC<{title: string; l1: string; l2?: string; start: number}> = ({title, l1, l2, start}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const local = frame - start;
  const inAnim = spring({frame: local, fps, config: {damping: 18, stiffness: 110}});
  const out = interpolate(local, [95, 115], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <div
      style={{
        position: 'absolute',
        left: 60,
        right: 60,
        bottom: 120,
        padding: '34px 36px',
        borderRadius: 28,
        background: 'linear-gradient(135deg, rgba(10,10,22,.68), rgba(20,24,50,.75))',
        border: '1px solid rgba(255,255,255,.18)',
        backdropFilter: 'blur(8px)',
        transform: `translateY(${(1 - inAnim) * 140}px) scale(${0.96 + inAnim * 0.04})`,
        opacity: inAnim * out,
      }}
    >
      <div style={{fontSize: 42, color: '#8ed1ff', fontWeight: 800, marginBottom: 16}}>{title}</div>
      <div style={{fontSize: 64, color: 'white', fontWeight: 700, lineHeight: 1.12}}>{l1}</div>
      {l2 ? <div style={{fontSize: 58, color: 'white', fontWeight: 700, lineHeight: 1.15, marginTop: 8}}>{l2}</div> : null}
    </div>
  );
};

export const Video: React.FC = () => {
  const frame = useCurrentFrame();
  const glow = 0.3 + Math.sin(frame / 14) * 0.1;

  return (
    <AbsoluteFill style={BG}>
      <div style={{position: 'absolute', inset: 0, background: `radial-gradient(circle at 80% 10%, rgba(59,130,246,${glow}), transparent 40%)`}} />
      <Character />

      <Sequence from={0} durationInFrames={120}>
        <ReactBitsCard title="Slide 1" l1="Prazer, eu sou o Pixel." l2="Mascote da V-8." start={0} />
      </Sequence>

      <Sequence from={120} durationInFrames={120}>
        <ReactBitsCard title="Slide 2" l1="A V-8 agora está com você" l2="24h por dia." start={120} />
      </Sequence>

      <Sequence from={240} durationInFrames={120}>
        <ReactBitsCard title="Slide 3" l1="Mais conteúdo, informação" l2="e entretenimento no seu trajeto." start={240} />
      </Sequence>
    </AbsoluteFill>
  );
};
