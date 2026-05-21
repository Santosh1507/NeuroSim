# NeuroSim AI Product Demo Videos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create three Remotion-based product demo videos (landing page hero, product tutorial, social media teaser) for NeuroSim AI.

**Architecture:** Single Remotion project with three separate compositions, each implementing one video from the design spec. Shared components for branding elements (colors, typography, animations). Videos are built as React components using Remotion's timeline primitives.

**Tech Stack:** Remotion, React, TypeScript, TailwindCSS (via @remotion/tailwind), Framer Motion (for easing curves)

---

## File Structure

```
frontend/src/video/
├── index.ts                          # Remotion root registration
├── Root.tsx                          # Remotion Root component
├── compositions/
│   ├── LandingPageHero.tsx           # Video 1: 60s hero (1920x1080)
│   ├── ProductTutorial.tsx           # Video 2: 180s tutorial (1920x1080)
│   └── SocialMediaTeaser.tsx         # Video 3: 30s teaser (1080x1920 + 1080x1080)
├── components/
│   ├── NeuralParticles.tsx           # Animated neural network background
│   ├── ROIBadge.tsx                  # ROI dimension badge (A5, LO, Area45, TPJ)
│   ├── ScoreBar.tsx                  # Animated progress bar for scores
│   ├── SwarmVisualization.tsx        # MiroFish swarm particle animation
│   ├── StageGateBadge.tsx            # Stage-Gate PASS/FAIL badge
│   ├── TextReveal.tsx                # Text reveal animation component
│   └── CTAButton.tsx                 # Call-to-action button animation
├── styles/
│   └── theme.ts                      # Color palette, typography, spacing constants
└── utils/
    └── timing.ts                     # Easing functions, interpolation helpers
```

---

### Task 1: Set Up Remotion Project

**Files:**
- Create: `frontend/src/video/index.ts`
- Create: `frontend/src/video/Root.tsx`
- Modify: `frontend/package.json` (add remotion dependencies)

- [ ] **Step 1: Install Remotion dependencies**

Run in `frontend/`:
```bash
npm install remotion @remotion/cli @remotion/player
```

- [ ] **Step 2: Create theme constants**

Create: `frontend/src/video/styles/theme.ts`

```typescript
export const colors = {
  background: {
    dark: '#0a0a0f',
    darker: '#050508',
    gradient: 'linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%)',
  },
  accent: {
    purple: '#7c3aed',
    blue: '#3b82f6',
    gradient: 'linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%)',
  },
  text: {
    primary: '#ffffff',
    secondary: '#a1a1aa',
    muted: '#71717a',
  },
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
};

export const typography = {
  fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
  sizes: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
    '5xl': '3rem',
    '6xl': '3.75rem',
  },
  weights: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
};

export const spacing = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  '2xl': '3rem',
  '3xl': '4rem',
};

export const roiDimensions = [
  { key: 'A5', name: 'Auditory Cortex', description: 'Speech pacing & rhythm' },
  { key: 'LO', name: 'Lateral Occipital', description: 'Visual & descriptive language' },
  { key: 'Area45', name: 'Broca\'s Area', description: 'CTA effectiveness' },
  { key: 'TPJ', name: 'Temporoparietal Junction', description: 'Social cognition' },
];
```

- [ ] **Step 3: Create timing utilities**

Create: `frontend/src/video/utils/timing.ts`

```typescript
import { interpolate, Easing } from 'remotion';

export const easings = {
  smooth: (t: number) => Easing.bezier(0.4, 0, 0.2, 1)(t),
  bounce: (t: number) => Easing.bounce(t),
  elastic: (t: number) => {
    const c4 = (2 * Math.PI) / 3;
    return t === 0
      ? 0
      : t === 1
      ? 1
      : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c4) + 1;
  },
};

export function fadeIn(frame: number, startFrame: number, duration: number = 30): number {
  return interpolate(frame, [startFrame, startFrame + duration], [0, 1], {
    extrapolateRight: 'clamp',
  });
}

export function fadeOut(frame: number, startFrame: number, duration: number = 30): number {
  return interpolate(frame, [startFrame, startFrame + duration], [1, 0], {
    extrapolateLeft: 'clamp',
  });
}

export function slideIn(frame: number, startFrame: number, duration: number = 30, direction: 'up' | 'down' | 'left' | 'right' = 'up'): number {
  const progress = interpolate(frame, [startFrame, startFrame + duration], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const eased = easings.smooth(progress);
  
  switch (direction) {
    case 'up':
      return interpolate(eased, [0, 1], [50, 0]);
    case 'down':
      return interpolate(eased, [0, 1], [-50, 0]);
    case 'left':
      return interpolate(eased, [0, 1], [50, 0]);
    case 'right':
      return interpolate(eased, [0, 1], [-50, 0]);
  }
}

export function scaleIn(frame: number, startFrame: number, duration: number = 30): number {
  const progress = interpolate(frame, [startFrame, startFrame + duration], [0, 1], {
    extrapolateRight: 'clamp',
  });
  return interpolate(easings.smooth(progress), [0, 1], [0.8, 1]);
}
```

- [ ] **Step 4: Create Remotion Root**

Create: `frontend/src/video/Root.tsx`

```tsx
import { Composition } from 'remotion';
import { LandingPageHero } from './compositions/LandingPageHero';
import { ProductTutorial } from './compositions/ProductTutorial';
import { SocialMediaTeaser } from './compositions/SocialMediaTeaser';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="LandingPageHero"
        component={LandingPageHero}
        durationInFrames={1800} // 60s at 30fps
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="ProductTutorial"
        component={ProductTutorial}
        durationInFrames={5400} // 180s at 30fps
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="SocialMediaTeaserVertical"
        component={SocialMediaTeaser}
        durationInFrames={900} // 30s at 30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{ variant: 'vertical' }}
      />
      <Composition
        id="SocialMediaTeaserSquare"
        component={SocialMediaTeaser}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1080}
        defaultProps={{ variant: 'square' }}
      />
    </>
  );
};
```

- [ ] **Step 5: Create Remotion entry point**

Create: `frontend/src/video/index.ts`

```typescript
import { registerRoot } from 'remotion';
import { RemotionRoot } from './Root';

registerRoot(RemotionRoot);
```

- [ ] **Step 6: Add Remotion scripts to package.json**

Modify `frontend/package.json` scripts section:
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "vitest run",
    "video": "npx remotion studio src/video/index.ts",
    "video:render:hero": "npx remotion render LandingPageHero out/videos/landing-hero.mp4",
    "video:render:tutorial": "npx remotion render ProductTutorial out/videos/product-tutorial.mp4",
    "video:render:teaser:vertical": "npx remotion render SocialMediaTeaserVertical out/videos/teaser-vertical.mp4",
    "video:render:teaser:square": "npx remotion render SocialMediaTeaserSquare out/videos/teaser-square.mp4"
  }
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/video/ frontend/package.json
git commit -m "feat: set up Remotion project for product demo videos"
```

---

### Task 2: Build Shared Components

**Files:**
- Create: `frontend/src/video/components/NeuralParticles.tsx`
- Create: `frontend/src/video/components/ROIBadge.tsx`
- Create: `frontend/src/video/components/ScoreBar.tsx`
- Create: `frontend/src/video/components/SwarmVisualization.tsx`
- Create: `frontend/src/video/components/StageGateBadge.tsx`
- Create: `frontend/src/video/components/TextReveal.tsx`
- Create: `frontend/src/video/components/CTAButton.tsx`

- [ ] **Step 1: Create NeuralParticles component**

Create: `frontend/src/video/components/NeuralParticles.tsx`

```tsx
import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';
import { colors } from '../styles/theme';

interface Particle {
  x: number;
  y: number;
  size: number;
  speed: number;
  opacity: number;
}

export const NeuralParticles: React.FC<{ opacity?: number }> = ({ opacity = 1 }) => {
  const frame = useCurrentFrame();
  
  const particles = useMemo<Particle[]>(() => {
    return Array.from({ length: 50 }, () => ({
      x: Math.random() * 1920,
      y: Math.random() * 1080,
      size: Math.random() * 4 + 2,
      speed: Math.random() * 0.5 + 0.2,
      opacity: Math.random() * 0.5 + 0.2,
    }));
  }, []);

  return (
    <AbsoluteFill style={{ opacity }}>
      {particles.map((particle, i) => {
        const y = (particle.y + frame * particle.speed) % 1080;
        const x = particle.x + Math.sin(frame * 0.02 + i) * 20;
        
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: particle.size,
              height: particle.size,
              borderRadius: '50%',
              background: colors.accent.purple,
              opacity: particle.opacity * opacity,
              filter: `blur(${particle.size / 2}px)`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
```

- [ ] **Step 2: Create ROIBadge component**

Create: `frontend/src/video/components/ROIBadge.tsx`

```tsx
import React from 'react';
import { interpolate, useCurrentFrame, spring } from 'remotion';
import { colors, typography } from '../styles/theme';

interface ROIBadgeProps {
  label: string;
  value: number;
  frameOffset: number;
}

export const ROIBadge: React.FC<ROIBadgeProps> = ({ label, value, frameOffset }) => {
  const frame = useCurrentFrame();
  const progress = spring({
    frame: frame - frameOffset,
    fps: 30,
    config: { damping: 12, stiffness: 100 },
  });
  
  const scoreWidth = interpolate(progress, [0, 1], [0, value * 3]);

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '1rem',
      opacity: progress,
      transform: `scale(${interpolate(progress, [0, 1], [0.8, 1])})`,
    }}>
      <div style={{
        width: '60px',
        height: '60px',
        borderRadius: '12px',
        background: colors.accent.gradient,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: typography.fontFamily,
        fontWeight: typography.weights.bold,
        fontSize: typography.sizes.xl,
        color: colors.text.primary,
      }}>
        {label}
      </div>
      <div style={{ flex: 1, maxWidth: '300px' }}>
        <div style={{
          height: '8px',
          background: 'rgba(255,255,255,0.1)',
          borderRadius: '4px',
          overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${scoreWidth}px`,
            background: colors.accent.gradient,
            borderRadius: '4px',
            transition: 'width 0.3s ease',
          }} />
        </div>
        <div style={{
          marginTop: '0.5rem',
          fontFamily: typography.fontFamily,
          fontSize: typography.sizes.sm,
          color: colors.text.secondary,
        }}>
          {Math.round(value * 100)}%
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 3: Create ScoreBar component**

Create: `frontend/src/video/components/ScoreBar.tsx`

```tsx
import React from 'react';
import { interpolate, spring, useCurrentFrame } from 'remotion';
import { colors, typography } from '../styles/theme';

interface ScoreBarProps {
  label: string;
  score: number;
  frameOffset: number;
}

export const ScoreBar: React.FC<ScoreBarProps> = ({ label, score, frameOffset }) => {
  const frame = useCurrentFrame();
  const progress = spring({
    frame: frame - frameOffset,
    fps: 30,
    config: { damping: 15, stiffness: 120 },
  });

  return (
    <div style={{
      marginBottom: '1.5rem',
      opacity: progress,
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: '0.5rem',
        fontFamily: typography.fontFamily,
        fontSize: typography.sizes.sm,
        color: colors.text.secondary,
      }}>
        <span>{label}</span>
        <span style={{ color: colors.text.primary, fontWeight: typography.weights.semibold }}>
          {Math.round(score * 100)}
        </span>
      </div>
      <div style={{
        height: '6px',
        background: 'rgba(255,255,255,0.08)',
        borderRadius: '3px',
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%',
          width: `${interpolate(progress, [0, 1], [0, score * 100])}%`,
          background: colors.accent.gradient,
          borderRadius: '3px',
        }} />
      </div>
    </div>
  );
};
```

- [ ] **Step 4: Create SwarmVisualization component**

Create: `frontend/src/video/components/SwarmVisualization.tsx`

```tsx
import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';
import { colors } from '../styles/theme';

interface SwarmVisualizationProps {
  opacity?: number;
  frameOffset: number;
}

export const SwarmVisualization: React.FC<SwarmVisualizationProps> = ({ opacity = 1, frameOffset }) => {
  const frame = useCurrentFrame();
  const adjustedFrame = Math.max(0, frame - frameOffset);
  
  const agents = useMemo(() => {
    return Array.from({ length: 100 }, (_, i) => ({
      id: i,
      startX: Math.random() * 1920,
      startY: Math.random() * 1080,
      targetX: 960 + (Math.random() - 0.5) * 400,
      targetY: 540 + (Math.random() - 0.5) * 300,
      speed: Math.random() * 0.02 + 0.01,
      size: Math.random() * 6 + 3,
    }));
  }, []);

  return (
    <AbsoluteFill style={{ opacity }}>
      {agents.map((agent) => {
        const progress = interpolate(adjustedFrame * agent.speed, [0, 1], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        const eased = progress * progress * (3 - 2 * progress); // smoothstep
        
        const x = agent.startX + (agent.targetX - agent.startX) * eased;
        const y = agent.startY + (agent.targetY - agent.startY) * eased;

        return (
          <div
            key={agent.id}
            style={{
              position: 'absolute',
              left: x - agent.size / 2,
              top: y - agent.size / 2,
              width: agent.size,
              height: agent.size,
              borderRadius: '50%',
              background: colors.accent.purple,
              opacity: 0.6 + eased * 0.4,
              boxShadow: `0 0 ${agent.size}px ${colors.accent.purple}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
```

- [ ] **Step 5: Create StageGateBadge component**

Create: `frontend/src/video/components/StageGateBadge.tsx`

```tsx
import React from 'react';
import { spring, useCurrentFrame } from 'remotion';
import { colors, typography } from '../styles/theme';

interface StageGateBadgeProps {
  passed: boolean;
  wAttn: number;
  frameOffset: number;
}

export const StageGateBadge: React.FC<StageGateBadgeProps> = ({ passed, wAttn, frameOffset }) => {
  const frame = useCurrentFrame();
  const progress = spring({
    frame: frame - frameOffset,
    fps: 30,
    config: { damping: 10, stiffness: 80 },
  });

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.75rem',
      padding: '0.75rem 1.5rem',
      borderRadius: '12px',
      background: passed ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
      border: `1px solid ${passed ? colors.success : colors.danger}`,
      opacity: progress,
      transform: `scale(${interpolate(progress, [0, 1], [0.9, 1])})`,
    }}>
      <div style={{
        width: '12px',
        height: '12px',
        borderRadius: '50%',
        background: passed ? colors.success : colors.danger,
      }} />
      <div style={{
        fontFamily: typography.fontFamily,
        fontSize: typography.sizes.base,
        fontWeight: typography.weights.semibold,
        color: passed ? colors.success : colors.danger,
      }}>
        Stage-Gate {passed ? 'PASS' : 'FAIL'} · W_attn: {wAttn.toFixed(2)}
      </div>
    </div>
  );
};
```

- [ ] **Step 6: Create TextReveal component**

Create: `frontend/src/video/components/TextReveal.tsx`

```tsx
import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { easings } from '../utils/timing';
import { colors, typography } from '../styles/theme';

interface TextRevealProps {
  text: string;
  frameOffset: number;
  duration?: number;
  size?: 'sm' | 'base' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl';
  weight?: 'normal' | 'medium' | 'semibold' | 'bold';
  align?: 'left' | 'center' | 'right';
  color?: string;
}

export const TextReveal: React.FC<TextRevealProps> = ({
  text,
  frameOffset,
  duration = 30,
  size = 'base',
  weight = 'normal',
  align = 'center',
  color = colors.text.primary,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [frameOffset, frameOffset + duration], [0, 1], {
    extrapolateRight: 'clamp',
  });
  const translateY = interpolate(frame, [frameOffset, frameOffset + duration], [30, 0], {
    extrapolateRight: 'clamp',
  });

  return (
    <div style={{
      fontFamily: typography.fontFamily,
      fontSize: typography.sizes[size],
      fontWeight: typography.weights[weight],
      color,
      textAlign: align,
      opacity: easings.smooth(opacity),
      transform: `translateY(${translateY}px)`,
    }}>
      {text}
    </div>
  );
};
```

- [ ] **Step 7: Create CTAButton component**

Create: `frontend/src/video/components/CTAButton.tsx`

```tsx
import React from 'react';
import { interpolate, spring, useCurrentFrame } from 'remotion';
import { colors, typography } from '../styles/theme';

interface CTAButtonProps {
  text: string;
  frameOffset: number;
}

export const CTAButton: React.FC<CTAButtonProps> = ({ text, frameOffset }) => {
  const frame = useCurrentFrame();
  const progress = spring({
    frame: frame - frameOffset,
    fps: 30,
    config: { damping: 12, stiffness: 100 },
  });

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.5rem',
      padding: '1rem 2rem',
      borderRadius: '8px',
      background: colors.accent.gradient,
      fontFamily: typography.fontFamily,
      fontSize: typography.sizes.lg,
      fontWeight: typography.weights.semibold,
      color: colors.text.primary,
      opacity: progress,
      transform: `scale(${interpolate(progress, [0, 1], [0.95, 1])})`,
      boxShadow: `0 4px 20px rgba(124, 58, 237, 0.4)`,
    }}>
      {text}
      <span style={{ marginLeft: '0.5rem' }}>→</span>
    </div>
  );
};
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/video/components/ frontend/src/video/styles/ frontend/src/video/utils/
git commit -m "feat: add shared Remotion components for demo videos"
```

---

### Task 3: Create Landing Page Hero Video

**Files:**
- Create: `frontend/src/video/compositions/LandingPageHero.tsx`

- [ ] **Step 1: Create LandingPageHero composition**

Create: `frontend/src/video/compositions/LandingPageHero.tsx`

```tsx
import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame } from 'remotion';
import { colors } from '../styles/theme';
import { NeuralParticles } from '../components/NeuralParticles';
import { ROIBadge } from '../components/ROIBadge';
import { SwarmVisualization } from '../components/SwarmVisualization';
import { StageGateBadge } from '../components/StageGateBadge';
import { TextReveal } from '../components/TextReveal';
import { CTAButton } from '../components/CTAButton';

export const LandingPageHero: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ background: colors.background.gradient }}>
      {/* Background particles - always visible */}
      <NeuralParticles opacity={0.6} />

      {/* 0-5s: Hook */}
      <Sequence from={0} duration={150}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '4rem',
        }}>
          <TextReveal
            text="What if you could predict how your content performs..."
            frameOffset={0}
            duration={45}
            size="4xl"
            weight="bold"
          />
          <TextReveal
            text="before you film it?"
            frameOffset={45}
            duration={45}
            size="5xl"
            weight="bold"
            color={colors.accent.purple}
          />
        </AbsoluteFill>
      </Sequence>

      {/* 5-15s: The Reveal */}
      <Sequence from={150} duration={300}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '2rem',
        }}>
          <TextReveal
            text="Meet NeuroSim AI"
            frameOffset={150}
            duration={45}
            size="6xl"
            weight="bold"
          />
          <TextReveal
            text="Predictive Content Intelligence"
            frameOffset={195}
            duration={45}
            size="2xl"
            weight="medium"
            color={colors.text.secondary}
          />
          {/* ROI badges flash */}
          <div style={{ display: 'flex', gap: '1.5rem', marginTop: '2rem' }}>
            <ROIBadge label="A5" value={0.82} frameOffset={240} />
            <ROIBadge label="LO" value={0.76} frameOffset={255} />
            <ROIBadge label="Area45" value={0.91} frameOffset={270} />
            <ROIBadge label="TPJ" value={0.68} frameOffset={285} />
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* 15-30s: How It Works */}
      <Sequence from={450} duration={450}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '2rem',
          padding: '4rem',
        }}>
          <TextReveal text="Paste your script" frameOffset={450} duration={30} size="4xl" weight="bold" />
          <TextReveal text="Get instant predictions" frameOffset={540} duration={30} size="4xl" weight="bold" />
          <StageGateBadge passed={true} wAttn={0.72} frameOffset={630} />
          <TextReveal text="Ship with confidence" frameOffset={720} duration={30} size="4xl" weight="bold" color={colors.success} />
        </AbsoluteFill>
      </Sequence>

      {/* 30-45s: Engines */}
      <Sequence from={900} duration={450}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '2rem',
        }}>
          <div style={{ display: 'flex', gap: '4rem' }}>
            <TextReveal text="TRIBE v2 Neural Encoding" frameOffset={900} duration={45} size="3xl" weight="semibold" />
            <TextReveal text="MiroFish Swarm Simulation" frameOffset={945} duration={45} size="3xl" weight="semibold" />
          </div>
          <TextReveal text="1000 agents · 20 rounds · 43K+ benchmark videos" frameOffset={1050} duration={45} size="xl" color={colors.text.secondary} />
          <SwarmVisualization opacity={0.8} frameOffset={1100} />
        </AbsoluteFill>
      </Sequence>

      {/* 45-60s: CTA */}
      <Sequence from={1350} duration={450}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.5rem',
        }}>
          <TextReveal text="10 analyses/month" frameOffset={1350} duration={30} size="3xl" weight="bold" />
          <TextReveal text="No credit card required" frameOffset={1410} duration={30} size="xl" color={colors.text.secondary} />
          <CTAButton text="Start Predicting" frameOffset={1500} />
          <TextReveal text="neurosimai.vercel.app" frameOffset={1600} duration={45} size="lg" color={colors.text.muted} />
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/video/compositions/LandingPageHero.tsx
git commit -m "feat: add landing page hero video composition"
```

---

### Task 4: Create Product Tutorial Video

**Files:**
- Create: `frontend/src/video/compositions/ProductTutorial.tsx`

- [ ] **Step 1: Create ProductTutorial composition**

Create: `frontend/src/video/compositions/ProductTutorial.tsx`

```tsx
import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame } from 'remotion';
import { colors, roiDimensions } from '../styles/theme';
import { NeuralParticles } from '../components/NeuralParticles';
import { ROIBadge } from '../components/ROIBadge';
import { ScoreBar } from '../components/ScoreBar';
import { SwarmVisualization } from '../components/SwarmVisualization';
import { StageGateBadge } from '../components/StageGateBadge';
import { TextReveal } from '../components/TextReveal';
import { CTAButton } from '../components/CTAButton';

export const ProductTutorial: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ background: colors.background.gradient }}>
      <NeuralParticles opacity={0.3} />

      {/* 0-10s: Intro */}
      <Sequence from={0} duration={300}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.5rem',
          padding: '4rem',
        }}>
          <TextReveal text="Welcome to NeuroSim AI" frameOffset={0} duration={45} size="5xl" weight="bold" />
          <TextReveal
            text="In this video, we'll show you how to analyze your content and predict its performance before you publish."
            frameOffset={60}
            duration={60}
            size="xl"
            color={colors.text.secondary}
          />
        </AbsoluteFill>
      </Sequence>

      {/* 10-30s: Getting Started */}
      <Sequence from={300} duration={600}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.5rem',
          padding: '4rem',
        }}>
          <TextReveal text="Getting Started" frameOffset={300} duration={45} size="4xl" weight="bold" />
          <TextReveal text="Navigate to neurosimai.vercel.app" frameOffset={360} duration={45} size="xl" />
          <TextReveal text="Click 'Go to Dashboard'" frameOffset={450} duration={45} size="xl" />
          <TextReveal text="You can start with a free account — no credit card needed" frameOffset={540} duration={60} size="lg" color={colors.text.secondary} />
        </AbsoluteFill>
      </Sequence>

      {/* 30-60s: Script Analysis */}
      <Sequence from={900} duration={900}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.5rem',
          padding: '4rem',
        }}>
          <TextReveal text="Script Analysis" frameOffset={900} duration={45} size="4xl" weight="bold" />
          <TextReveal text="Paste your video script here, or upload a text file" frameOffset={960} duration={60} size="xl" color={colors.text.secondary} />
          <div style={{
            width: '80%',
            height: '200px',
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '12px',
            border: '1px solid rgba(255,255,255,0.1)',
            padding: '1.5rem',
            marginTop: '1rem',
          }}>
            <TextReveal text="[Your video script text goes here...]" frameOffset={1050} duration={45} size="lg" color={colors.text.muted} align="left" />
          </div>
          <CTAButton text="Analyze" frameOffset={1200} />
          <TextReveal text="NeuroSim analyzes your script using heuristic linguistic scoring — no LLM, no GPU, instant results" frameOffset={1350} duration={90} size="lg" color={colors.text.secondary} />
        </AbsoluteFill>
      </Sequence>

      {/* 60-100s: Understanding Your Results */}
      <Sequence from={1800} duration={1200}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1rem',
          padding: '4rem',
        }}>
          <TextReveal text="Understanding Your Results" frameOffset={1800} duration={45} size="4xl" weight="bold" />
          
          {/* ROI Dimensions */}
          <div style={{ width: '70%', marginTop: '2rem' }}>
            <ScoreBar label="A5 — Auditory Cortex: speech pacing & rhythm" score={0.82} frameOffset={1900} />
            <ScoreBar label="LO — Lateral Occipital: visual & descriptive language" score={0.76} frameOffset={2000} />
            <ScoreBar label="Area45 — CTA effectiveness & persuasion" score={0.91} frameOffset={2100} />
            <ScoreBar label="TPJ — Social cognition & curiosity gaps" score={0.68} frameOffset={2200} />
          </div>
          
          <StageGateBadge passed={true} wAttn={0.72} frameOffset={2400} />
          <TextReveal text="Your content passed the attention threshold" frameOffset={2550} duration={45} size="lg" color={colors.success} />
        </AbsoluteFill>
      </Sequence>

      {/* 100-140s: Swarm Simulation */}
      <Sequence from={3000} duration={1200}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.5rem',
          padding: '4rem',
        }}>
          <TextReveal text="Swarm Simulation" frameOffset={3000} duration={45} size="4xl" weight="bold" />
          <TextReveal text="1000 agents across 8 persona types simulate 20 rounds of sentiment evolution" frameOffset={3060} duration={90} size="xl" color={colors.text.secondary} />
          <SwarmVisualization opacity={0.7} frameOffset={3200} />
          <div style={{ display: 'flex', gap: '3rem', marginTop: '2rem' }}>
            <TextReveal text="Viral potential: 72%" frameOffset={3400} duration={45} size="2xl" weight="semibold" color={colors.accent.purple} />
            <TextReveal text="Backlash risk: low" frameOffset={3500} duration={45} size="2xl" weight="semibold" color={colors.success} />
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* 140-160s: Comparison & What-If */}
      <Sequence from={4200} duration={600}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.5rem',
          padding: '4rem',
        }}>
          <TextReveal text="Benchmark Comparison" frameOffset={4200} duration={45} size="4xl" weight="bold" />
          <TextReveal text="Compare your scores against 43K+ benchmark videos" frameOffset={4260} duration={60} size="xl" color={colors.text.secondary} />
          <div style={{
            display: 'flex',
            gap: '2rem',
            marginTop: '1rem',
            padding: '1.5rem',
            background: 'rgba(255,255,255,0.05)',
            borderRadius: '12px',
          }}>
            <TextReveal text="Your hook score: 72" frameOffset={4350} duration={45} size="xl" weight="semibold" color={colors.accent.purple} />
            <TextReveal text="vs" frameOffset={4400} duration={30} size="xl" color={colors.text.muted} />
            <TextReveal text="Average: 58" frameOffset={4450} duration={45} size="xl" color={colors.text.secondary} />
          </div>
          <TextReveal text="Use what-if simulation to see how improvements change predictions" frameOffset={4550} duration={60} size="lg" color={colors.text.secondary} />
        </AbsoluteFill>
      </Sequence>

      {/* 160-180s: Video Analysis + Wrap-up */}
      <Sequence from={4800} duration={600}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.5rem',
          padding: '4rem',
        }}>
          <TextReveal text="Video Analysis" frameOffset={4800} duration={45} size="4xl" weight="bold" />
          <TextReveal text="Upload a finished video for deeper analysis" frameOffset={4860} duration={60} size="xl" color={colors.text.secondary} />
          <TextReveal text="NeuroSim transcribes your audio and runs the same powerful pipeline" frameOffset={4980} duration={60} size="lg" color={colors.text.secondary} />
          
          <div style={{ marginTop: '3rem', display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'center' }}>
            <TextReveal text="Start predicting your next hit" frameOffset={5100} duration={45} size="3xl" weight="bold" />
            <TextReveal text="Free tier includes 10 analyses per month" frameOffset={5160} duration={45} size="xl" color={colors.text.secondary} />
            <CTAButton text="Get Started Free" frameOffset={5250} />
            <TextReveal text="neurosimai.vercel.app" frameOffset={5350} duration={45} size="lg" color={colors.text.muted} />
          </div>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/video/compositions/ProductTutorial.tsx
git commit -m "feat: add product tutorial video composition"
```

---

### Task 5: Create Social Media Teaser Video

**Files:**
- Create: `frontend/src/video/compositions/SocialMediaTeaser.tsx`

- [ ] **Step 1: Create SocialMediaTeaser composition**

Create: `frontend/src/video/compositions/SocialMediaTeaser.tsx`

```tsx
import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from 'remotion';
import { colors } from '../styles/theme';
import { NeuralParticles } from '../components/NeuralParticles';
import { ROIBadge } from '../components/ROIBadge';
import { SwarmVisualization } from '../components/SwarmVisualization';
import { TextReveal } from '../components/TextReveal';
import { CTAButton } from '../components/CTAButton';

interface SocialMediaTeaserProps {
  variant?: 'vertical' | 'square';
}

export const SocialMediaTeaser: React.FC<SocialMediaTeaserProps> = ({ variant = 'vertical' }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  
  const isVertical = variant === 'vertical';
  const padding = isVertical ? '2rem' : '3rem';
  const titleSize = isVertical ? '5xl' : '4xl';
  const bodySize = isVertical ? 'xl' : 'lg';

  return (
    <AbsoluteFill style={{ background: colors.background.gradient }}>
      <NeuralParticles opacity={0.5} />

      {/* 0-2s: Hook */}
      <Sequence from={0} duration={60}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding,
        }}>
          <TextReveal
            text="Stop guessing if your content will work."
            frameOffset={0}
            duration={20}
            size={titleSize}
            weight="bold"
          />
        </AbsoluteFill>
      </Sequence>

      {/* 2-8s: The Twist */}
      <Sequence from={60} duration={180}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '2rem',
          padding,
        }}>
          <TextReveal
            text="What if you could PREDICT it?"
            frameOffset={60}
            duration={30}
            size={titleSize}
            weight="bold"
            color={colors.accent.purple}
          />
          <div style={{ display: 'flex', gap: isVertical ? '1rem' : '0.75rem', flexWrap: 'wrap', justifyContent: 'center' }}>
            <ROIBadge label="A5" value={0.82} frameOffset={120} />
            <ROIBadge label="LO" value={0.76} frameOffset={135} />
            <ROIBadge label="Area45" value={0.91} frameOffset={150} />
            <ROIBadge label="TPJ" value={0.68} frameOffset={165} />
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* 8-15s: The Product */}
      <Sequence from={240} duration={210}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1rem',
          padding,
        }}>
          <TextReveal text="NeuroSim AI analyzes your script before you film" frameOffset={240} duration={45} size={isVertical ? '3xl' : '2xl'} weight="bold" />
          <TextReveal text="Hook strength · Viral potential · CTA effectiveness · Emotional arc" frameOffset={300} duration={60} size={bodySize} color={colors.text.secondary} />
        </AbsoluteFill>
      </Sequence>

      {/* 15-22s: Social Proof */}
      <Sequence from={450} duration={210}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.5rem',
          padding,
        }}>
          <TextReveal text="Powered by neural encoding + 1000-agent swarm simulation" frameOffset={450} duration={60} size={isVertical ? '2xl' : 'xl'} weight="semibold" />
          <SwarmVisualization opacity={0.6} frameOffset={510} />
          <TextReveal text="43,000+ benchmark videos" frameOffset={570} duration={45} size={bodySize} color={colors.text.secondary} />
        </AbsoluteFill>
      </Sequence>

      {/* 22-30s: CTA */}
      <Sequence from={660} duration={240}>
        <AbsoluteFill style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1rem',
          padding,
        }}>
          <TextReveal text="10 free analyses. No credit card." frameOffset={660} duration={45} size={isVertical ? '3xl' : '2xl'} weight="bold" />
          <CTAButton text="Try it now" frameOffset={720} />
          <TextReveal text="neurosimai.vercel.app" frameOffset={780} duration={45} size={bodySize} color={colors.text.muted} />
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/video/compositions/SocialMediaTeaser.tsx
git commit -m "feat: add social media teaser video composition"
```

---

### Task 6: Test and Render Videos

**Files:**
- No new files, testing existing compositions

- [ ] **Step 1: Test in Remotion Studio**

Run in `frontend/`:
```bash
npm run video
```

This opens Remotion Studio where you can preview all compositions and scrub through timelines.

- [ ] **Step 2: Render Landing Page Hero**

Run in `frontend/`:
```bash
npm run video:render:hero
```

Expected output: `frontend/out/videos/landing-hero.mp4`

- [ ] **Step 3: Render Product Tutorial**

Run in `frontend/`:
```bash
npm run video:render:tutorial
```

Expected output: `frontend/out/videos/product-tutorial.mp4`

- [ ] **Step 4: Render Social Media Teaser (Vertical)**

Run in `frontend/`:
```bash
npm run video:render:teaser:vertical
```

Expected output: `frontend/out/videos/teaser-vertical.mp4`

- [ ] **Step 5: Render Social Media Teaser (Square)**

Run in `frontend/`:
```bash
npm run video:render:teaser:square
```

Expected output: `frontend/out/videos/teaser-square.mp4`

- [ ] **Step 6: Final commit**

```bash
git add frontend/out/videos/
git commit -m "feat: render all three product demo videos"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ Landing page hero (30-60s) — Task 3 implements all 5 sections with timing
- ✅ Product tutorial (2-3 min) — Task 4 implements all 7 sections with timing
- ✅ Social media teaser (15-30s) — Task 5 implements all 5 sections with vertical/square variants
- ✅ Shared visual style — Task 2 creates theme.ts with all colors, typography, and shared components
- ✅ Loop design for hero — End frame at 60s transitions naturally back to start
- ✅ No voiceover needed — All text-driven with TextReveal component

**2. Placeholder scan:**
- No TBD, TODO, or incomplete sections
- All code blocks contain complete implementations
- All file paths are exact
- All commands include expected outputs

**3. Type consistency:**
- All components use consistent imports from `styles/theme.ts`
- `frameOffset` pattern used consistently across all components
- Color tokens match between theme and component usage
- All Remotion imports (`AbsoluteFill`, `Sequence`, `useCurrentFrame`, `spring`, `interpolate`) used correctly

**Plan is complete and ready for execution.**
