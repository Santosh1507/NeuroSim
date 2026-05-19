# NeuroSim Design System

## Philosophy

Dark, precise, instrument-grade. Think surgical microscope in a dark room — every visual element has a function, nothing is decorative. The interface reads as a neural measurement instrument, not a marketing site.

**Core metaphor:** Neural measurement lab. Glass panels like microscope slides. Cyan neural activity traces. Purple swarm intelligence overlays. Every interface element feels like it's reading a real signal.

**Design principles:**
1. **Light emits from data** — the only bright elements are data points, scores, and active signals
2. **Glass physics** — surfaces are transparent, layered, with subtle refraction and edge highlights
3. **Asymmetric composition** — avoid centered, symmetrical layouts; prefer intentional imbalance
4. **Instrument precision** — mono type for data, tight tracking, hairline borders, no slop

---

## Color Palette

### Background system (void → surface)

| Token | Value | Usage |
|-------|-------|-------|
| `--void` | `#000000` | Primary background |
| `--depth-1` | `#030305` | 1st elevation layer |
| `--depth-2` | `#08080d` | 2nd elevation layer |
| `--depth-3` | `#0f0f16` | 3rd elevation / tooltip backgrounds |
| `--surface` | `#14141c` | Raised surface |
| `--surface-elevated` | `#1a1a24` | Elevated surface (cards) |

### Accent system

| Token | Value | Usage |
|-------|-------|-------|
| `--neural` | `#4deeea` | TRIBE v2 — primary accent, active signals, data highlights |
| `--neural-dim` | `rgba(77, 238, 234, 0.15)` | Neural background fills, hover states |
| `--neural-glow` | `rgba(77, 238, 234, 0.08)` | Large radial gradient glows |
| `--swarm` | `#a78bfa` | MiroFish — secondary accent, social data, sentiment charts |
| `--swarm-dim` | `rgba(167, 139, 250, 0.15)` | Swarm background fills |
| `--swarm-glow` | `rgba(167, 139, 250, 0.08)` | Large radial gradient glows |

### Signal system

| Token | Value | Usage |
|-------|-------|-------|
| `--signal-green` | `#34d399` | Positive metrics, pass status, healthy signals |
| `--signal-orange` | `#fb923c` | Warning, moderate risk, attention needed |
| `--signal-red` | `#f87171` | Critical, fail, high risk, error states |

### Text hierarchy

| Token | Value | Opacity | Usage |
|-------|-------|---------|-------|
| `--text-primary` | `#f0f0f5` | ~94% | Headings, primary labels, key data |
| `--text-secondary` | `#f0f0f5` | 60% | Body text, descriptions |
| `--text-tertiary` | `#f0f0f5` | 35% | Captions, metadata, secondary labels |
| `--text-quaternary` | `#f0f0f5` | 20% | Placeholders, disabled, muted |

### Glass system

| Token | Value | Usage |
|-------|-------|-------|
| `--glass-bg` | `rgba(255, 255, 255, 0.03)` | Default glass panel background |
| `--glass-border` | `rgba(255, 255, 255, 0.06)` | Default glass border |
| `--glass-border-hover` | `rgba(255, 255, 255, 0.12)` | Hover state border |
| `--glass-highlight` | `rgba(255, 255, 255, 0.08)` | Top edge highlight |
| `--glass-shadow` | `rgba(0, 0, 0, 0.5)` | Drop shadow |

---

## Typography

### Font stack

| Role | Font | Weight | Usage |
|------|------|--------|-------|
| Display | **Sora** | 300–800 | Headings h1–h4 |
| Body | **Instrument Sans** | 400–700 | Body text, UI labels, buttons |
| Mono | **JetBrains Mono** | 400–600 | Data, scores, metrics, code |
| Mono alt | **Space Mono** | 400, 700 | Fallback mono |

### Type scale

```
h1: clamp(2.5rem, 6vw, 4.5rem) / Sora 700 / -0.03em tracking
h2: clamp(2rem, 5vw, 3.5rem) / Sora 600 / -0.02em tracking
h3: text-3xl (1.875rem) / Sora 600
h4: text-base (1rem) / Sora 600
Body: text-sm (0.875rem) / Instrument Sans 400 / 1.5 leading
Caption: text-xs (0.75rem) / Instrument Sans or Mono
Micro: text-[10px] or text-[11px] / Mono / uppercase tracking-wider
```

### Text treatments

- **Gradient text:** `.text-gradient` — linear gradient from `--neural` to `--swarm`, uses `background-clip: text`
- **Neural text:** `.text-neural` — cyan (#4deeea)
- **Swarm text:** `.text-swarm` — purple (#a78bfa)
- **Mono data:** All scores, metrics, and numerical values use `.mono` (JetBrains Mono)

---

## Spacing System

Base unit: **4px**. All spacing uses multiples of 4.

| Token | Value | Context |
|-------|-------|---------|
| `gap-1` | 4px | Internal icon/label spacing |
| `gap-2` | 8px | Tight element grouping |
| `gap-3` | 12px | Related item spacing |
| `gap-4` | 16px | Standard grid gap |
| `gap-6` | 24px | Section separation |
| `p-4` | 16px | Standard panel padding |
| `p-5` | 20px | Elevated panel padding |
| `p-6` | 24px | Feature card padding |
| `p-8` | 32px | Large panel padding |
| `p-12` | 48px | Hero section padding |
| `px-6` | 24px | Standard page horizontal padding |

Layout columns: `max-w-7xl` (1280px) for full pages, `max-w-6xl` (1152px) for content sections.

Dashboard uses 12-column grid: main content 8 cols, sidebar 4 cols.

---

## Component Patterns

### Glass Panels (`.glass-panel`)

The fundamental building block. Applies to cards, sidebars, modals, and section containers.

- Background: `rgba(255, 255, 255, 0.03)` with 24px blur + 150% saturate
- Border: 1px `rgba(255, 255, 255, 0.06)` with 16px radius
- **Top edge highlight:** `::before` pseudo-element — 1px gradient line at 20%–80% width, creates the "microscope slide" effect
- **Elevated variant (`.glass-panel-elevated`):** Higher opacity (0.04), 32px blur, 20px radius, drop shadow
- **Accent variants:** `.glass-neural` (cyan tint) and `.glass-swarm` (purple tint) for specific engine panels

### Interactive panels (`.glass-interactive`)

- Hover: background increases to 0.05, border lightens, translates -1px up
- Active: returns to position, scale 0.995
- Drag active: neural cyan border + glow shadow
- Transition: 0.3s `var(--ease-smooth)`

### Buttons

| Class | Purpose | Style |
|-------|---------|-------|
| `.btn-neural` | Primary actions | Neural cyan dim bg, cyan text, hover lift + glow |
| `.btn-swarm` | Secondary actions | Swarm purple dim bg, purple text |
| `.btn-ghost` | Tertiary actions | Transparent, subtle border, white text on hover |
| Inline link | Text actions | `text-[10px] mono text-neural hover:underline` |

All buttons: 10px radius, 10px 20px padding, transition 0.25s `var(--ease-smooth)`.

### Tabs / Segmented Control (`.tab-segment`)

- Container: glass-panel on flex row
- Items: 13px font, 500 weight, tertiary color
- Active: white text, 0.08 white bg, subtle shadow
- Hover: slight bg increase
- Transition: 0.25s `var(--ease-smooth)`

### Progress Bars (`.progress-track` + `.progress-fill`)

- Track: 3px height, `rgba(255,255,255,0.06)` background, 2px radius
- Fill: color-coded by metric:
  - `.progress-neural` — neural cyan
  - `.progress-swarm` — swarm purple
  - `.progress-green` — signal green
  - `.progress-orange` — signal orange
  - `.progress-red` — signal red
- Fill transition: 0.6s `var(--ease-smooth)`

### Badges (`.badge`)

- Inline flex with 6px gap, 4px 10px padding
- 11px JetBrains Mono, 600 weight, 0.02em tracking
- Variants: `.badge-neural`, `.badge-swarm`, `.badge-ghost`

### Status Dots (`.status-dot`)

- 6px circle, with pulse-ring `::after` animation
- Color variants: `.status-neural`, `.status-swarm`, `.status-green`
- Use for model status indicators and live connection states

### Inputs (`.input-neural`)

- 0.03 white bg, glass border, 10px radius
- Focus: neural cyan border + subtle glow ring
- Placeholder: `--text-quaternary`

### Progress Stage Indicator

Used during upload to show pipeline stages (Transcribing → Scoring → Saving → Done):
- Active stage: neural cyan dot + pulse animation
- Completed: neural cyan dot
- Pending: 10% white dot
- Connector: 4px hairline between stages

---

## Animation System

### Timing functions

| Token | Value | Usage |
|-------|-------|-------|
| `--ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` | Entry animations (fade, slide) |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Micro-interactions |
| `--ease-smooth` | `cubic-bezier(0.4, 0, 0.2, 1)` | Hover, transition states |

### Keyframe animations

| Name | Pattern | Use |
|------|---------|-----|
| `fadeIn` | 0→1 opacity + 8px slide | Element entrance |
| `slideUp` | 0→1 opacity + 16px slide | Section entrance |
| `neural-pulse` | 0.4→1→0.4 opacity | Active reading state |
| `pulse-ring` | scale 1→2.5 opacity 1→0 | Status dots |
| `scan-line` | translateY -100%→100% | Hero visual effect |

### Stagger children (`.stagger`)

Sequential fade-in for grid items up to 8 children, 50ms delay increments.

---

## Background Patterns

### Neural background (`.bg-neural`)

Multi-layered:
1. Neural cyan radial glow at 20% 40%
2. Swarm purple radial glow at 80% 20%
3. Signal green subtle glow at 60% 80%
4. Linear gradient void → depth-1 → depth-2
5. SVG fractal noise overlay at 2% opacity (subtle grain texture)

### Grid overlay (`.neural-grid`)

1px hairline grid at 40px spacing, 0.015 opacity — references neural recording grid paper.

---

## State Tables

### Dashboard Upload Zone

| State | Visual | Message |
|-------|--------|---------|
| **Empty (idle)** | Upload icon + dashed drop zone | "Drop video to analyze" |
| **Drag active** | Neural cyan border + glow, `drag-active` class | (no text change) |
| **Uploading** | Circular progress indicator + percentage | "Uploading..." → "Transcribing..." → "Analyzing..." |
| **Processing** | Stage indicator with animated dots | "Starting analysis..." + progress bar |
| **Success** | Analysis appears, video list updates | "Analysis complete" |
| **Error** | Amber warning banner | "Demo Mode — [error detail]" |
| **Backend unreachable** | Amber warning + demo mode fallback | "Cannot reach backend. Run NeuroSim on localhost:8000" |

### Dashboard Analysis Tab

| State | Visual | Message |
|-------|--------|---------|
| **Empty (loading)** | Skeleton spinner | Spinning loader in panel |
| **Empty (no data)** | Pulse animation + Activity icon | "Ready for Analysis — Upload a video..." |
| **Data (desktop)** | 3D Brain heatmap (Brain3D component) | Full neural response visualization |
| **Data (mobile)** | 2D score grid | 6 cortical region scores in 2x3 grid |
| **Error** | Amber banner | error message string |

### Dashboard A/B Testing

| State | Visual | Message |
|-------|--------|---------|
| **Empty (idle)** | Call-to-action button | "Run Predictive Test" |
| **Loading** | Double spinning ring + Brain icon | "Running Neural Pipeline — TRIBE v2 → ROI → MiroFish Swarm" |
| **Success** | Two comparison cards + 7-day chart | Version winner badge + metrics |
| **Error** | Amber banner | "A/B test failed. Backend may be unavailable." |

### Waitlist

| State | Visual | Message |
|-------|--------|---------|
| **Empty (form)** | Email + name inputs | "Join the waitlist" |
| **Submitting** | Disabled button | "Joining..." |
| **Success** | Check circle icon | "You're on the list! #N in line" |
| **Conflict** | Amber inline error | "Already on the waitlist!" |
| **Error** | Amber inline error | "Something went wrong." |

### Analytics Page

| State | Visual | Message |
|-------|--------|---------|
| **Loading** | Centered spinner | Spinning loader |
| **Empty (no data)** | Default zeros + summary | "No analyses have been run yet." |
| **Data** | 4 stat cards + 2 charts + summary | Score bars + trend lines + narrative |

### Comparison Page

| State | Visual | Message |
|-------|--------|---------|
| **Empty (no IDs)** | Two input fields + Compare button | "Enter video ID" |
| **Loading** | Disabled button | "Loading..." |
| **Data** | 6 metric cards + grouped bar chart | Delta indicators (+/-/—) per metric |

### Digest Page

| State | Visual | Message |
|-------|--------|---------|
| **Loading** | Centered spinner | Spinning loader |
| **Empty (no data)** | Mail icon centered | "No digest available — Analyze some content first" |
| **Data** | 4 stat cards + top performers list | "Your analysis summary" |

### Share Modal

| State | Visual | Message |
|-------|--------|---------|
| **Generating** | Button shows spinner | "..." |
| **Success** | Copyable link + copy button | "Anyone with this link can view" |
| **Copied** | Check icon replaces copy | "Copied to clipboard!" (2s auto-dismiss) |
| **Error** | Console log only | No user-facing error |

---

## Motion Guidelines

### When to animate

- **Entry:** Page sections fade in with slideUp (0.5s, stagger 50ms)
- **Tab switch:** Framer Motion AnimatePresence with fade + 8px vertical
- **Hover:** Panel lifts 1px, border lightens, 0.3s ease-smooth
- **Active:** Scale 0.98, 0.1s duration
- **Data change:** 0.6s progress bar fill, chart data transitions

### When NOT to animate

- Critical status indicators (status dots) — always instant
- Score numbers on load — instant render
- Error/success transitions — instant with subtle color change
- Scroll — native browser scroll, no custom scroll animations

### Neural recording aesthetic

- Scan-line sweep on hero (4s cycle, linear)
- Pulse rings on status dots (2s cycle, ease-out)
- Neural pulse on empty states (3s cycle, ease-in-out)
- Double spinning rings on processing states (opposite directions)

---

## GPU Cold Start Storyboard

When NeuroSim transitions from heuristic (simulated) to real GPU mode with TRIBE v2:

### Frame 1: Upload Initiated
```
User drops video → Upload progress reaches 100%
UI shows: "Analysis queued" — the video is in the pipeline
```

### Frame 2: Cold Start Detection (0–5s)
```
Backend detects TRIBE v2 model is not loaded
Logs: "TRIBE v2 not loaded — initializing GPU model"
UI shows: "Loading neural engine..." — progress bar at 10%
Stage indicator: all dots dim, "GPU" label appears
```

### Frame 3: Model Loading (5–45s)
```
~40s for facebook/tribev2 to load from HuggingFace on a T4 GPU
UI shows: "Loading TRIBE v2 neural model (~40s first time)"
Progress bar: slow crawl from 10% → 40%
Stage: "Loading" — animated neural pulse
Message: "First analysis loads GPU model — subsequent analyses are instant"
``` 

### Frame 4: Model Ready (45–50s)
```
Model loaded successfully
UI shows: "Model ready! Running neural encoding"
Progress jumps: 40% → 60%
Status dot: transitions from dim to status-neural (pulsing)
Stage: "Encoding"
```

### Frame 5: Analysis Running (50–65s)
```
TRIBE processes video through 20 timesteps × 20484 vertices
UI shows: "Running TRIBE v2 neural analysis"
Progress: 60% → 80%
Stage: "Scoring"
```

### Frame 6: Analysis Complete (65–70s)
```
Full report generated
UI shows: "Analysis complete"
Progress: 100%
Status dot: solid neural cyan (real mode)
Badge: "REAL" replaces "SIMULATED"
```

### Frame 7: Subsequent Uploads (5–10s)
```
No cold start — model cached in GPU memory
UI shows: "Neural engine ready" — instant processing
Progress: 0% → 100% in 5–10 seconds
```

### UX Copy for Cold Start

| Moment | Message |
|--------|---------|
| Queue | "Analysis queued. GPU cold start estimated at 40s." |
| Loading | "Loading TRIBE v2 (facebook/tribev2) — first analysis loads the model, subsequent ones are instant." |
| Ready | "Neural model loaded. Encoding your content." |
| Warning (>60s) | "GPU cold start taking longer than expected. Check Render GPU logs." |

### Premium Tier States

| State | Detail |
|-------|--------|
| Free user uploads | Heuristic mode (simulated) — instant analysis, no GPU |
| Pro user, first upload | Cold start storyboard above |
| Pro user, subsequent | GPU hot — instant neural encoding |
| Free → Pro upgrade | Existing analyses stay, next upload triggers GPU load |
| GPU unavailable | Fallback to heuristic + amber warning: "GPU unavailable — running simulated analysis" |

---

## Responsive Design

### Breakpoints

| Breakpoint | Target | Changes |
|------------|--------|---------|
| sm (640px) | Mobile | Stack grids, reduce padding, full-width panels |
| md (768px) | Tablet | Reduce tab sizes, compact sidebar |
| lg (1024px) | Desktop | Full 12-col dashboard layout |

### Mobile adaptations

- Dashboard 12-col → 1-col stack
- 3D Brain component → 2D score card grid
- Tab labels hide, icons only
- Sidebar panels collapse to inline stats row
- Upload zone padding reduced
- Hero text smaller, center-aligned

---

## Accessibility

### Focus management

- All interactive elements use `:focus-visible` with 2px neural cyan outline + 2px offset
- Modal focus trap (share modal closes on backdrop click + X button)
- Tab order follows visual reading order

### Color contrast

- `--text-primary` on `--void`: ~15:1 ratio (exceeds WCAG AAA)
- `--text-secondary` on `--void`: ~8:1 (exceeds WCAG AA)
- Status colors on dark background: green (6:1), orange (5:1), red (5:1)
- Gradient text is decorative only — data is also displayed as numeric values

### Reduced motion

- All animations use `framer-motion` which respects `prefers-reduced-motion`
- Pulsing status dots and scan-line effects are non-essential — users with motion sensitivity see static indicators
- Tab transitions skip animation when reduced motion is preferred
