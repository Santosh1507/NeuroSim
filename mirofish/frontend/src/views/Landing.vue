<template>
  <div class="landing">
    <!-- Navbar -->
    <nav class="nav">
      <div class="nav-inner">
        <div class="nav-left">
          <div class="nav-logo">
            <div class="logo-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="#06d6a0" stroke-width="2"/>
                <circle cx="12" cy="12" r="4" fill="#06d6a0"/>
                <line x1="12" y1="2" x2="12" y2="6" stroke="#06d6a0" stroke-width="2"/>
                <line x1="12" y1="18" x2="12" y2="22" stroke="#06d6a0" stroke-width="2"/>
              </svg>
            </div>
            <span class="logo-text">NeuroSim</span>
            <span class="logo-version">v2.0</span>
          </div>
        </div>
        <div class="nav-center">
          <a href="#features" class="nav-link" @click.prevent="scrollTo('features')">Features</a>
          <a href="#how-it-works" class="nav-link" @click.prevent="scrollTo('how-it-works')">How it works</a>
        </div>
        <div class="nav-right">
          <button class="btn-ghost" @click="goToLogin">Sign in</button>
          <button class="btn-primary" @click="goToSignup">Get Started Free</button>
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <section class="hero">
      <div class="hero-glow"></div>
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-icon">✦</span>
          <span>PREDICTIVE CONTENT INTELLIGENCE</span>
        </div>
        <h1 class="hero-title">
          Measure neural<br/>response<span class="hero-cursor">_</span>
        </h1>
        <p class="hero-subtitle">
          TRIBE v2 encodes brain responses. MiroFish simulates social swarms.
          Together they predict how your content performs before you spend a dollar.
        </p>
        <div class="hero-actions">
          <button class="btn-primary btn-lg" @click="goToDashboard">
            Start Analyzing Free
            <span class="btn-arrow">→</span>
          </button>
          <button class="btn-outline btn-lg" @click="scrollTo('features')">See Features</button>
        </div>
        <p class="hero-note">No credit card. Free tier includes 10 analyses per month.</p>
      </div>
    </section>

    <!-- Features -->
    <section id="features" class="features-section">
      <div class="section-inner">
        <h2 class="section-title">Two engines, one prediction</h2>
        <p class="section-subtitle">Biological brain response plus social swarm simulation. No other tool does both.</p>

        <div class="features-grid">
          <div class="feature-card feature-highlight" v-for="feature in features" :key="feature.title">
            <div class="feature-icon">{{ feature.icon }}</div>
            <h3 class="feature-name">{{ feature.title }}</h3>
            <p class="feature-desc">{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section id="how-it-works" class="steps-section">
      <div class="section-inner">
        <h2 class="section-title">Three steps to insight</h2>
        <p class="section-subtitle">From raw video to predictive report in under a minute.</p>

        <div class="steps-grid">
          <div class="step-card" v-for="(step, i) in steps" :key="step.title">
            <div class="step-number">{{ String(i + 1).padStart(2, '0') }}</div>
            <h3 class="step-name">{{ step.title }}</h3>
            <p class="step-desc">{{ step.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta-section">
      <div class="section-inner cta-inner">
        <h2 class="cta-title">Ready to predict your next hit?</h2>
        <p class="cta-subtitle">Upload a video, get neural and social predictions. Free to start, no credit card.</p>
        <button class="btn-primary btn-lg" @click="goToDashboard">
          Get Started Free
          <span class="btn-arrow">→</span>
        </button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <span class="logo-text">NeuroSim</span>
          <span class="footer-copy">© 2026 NeuroSim. Powered by MiroFish + TRIBE v2.</span>
        </div>
        <div class="footer-links">
          <a href="https://github.com/Santosh1507/NeuroSim" target="_blank" class="footer-link">GitHub</a>
          <a href="#features" class="footer-link" @click.prevent="scrollTo('features')">Features</a>
          <a href="#how-it-works" class="footer-link" @click.prevent="scrollTo('how-it-works')">How it works</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const features = [
  {
    icon: '🧠',
    title: 'TRIBE v2 Brain Encoding',
    description: 'Upload a video and get fMRI-level brain activation maps across 4 regions. Meta\'s neural response model predicts visual, auditory, and emotional engagement.'
  },
  {
    icon: '🐟',
    title: 'MiroFish Swarm Simulation',
    description: '1000-agent social simulation across 8 persona types. Predict viral spread, sentiment drift, backlash risk, and shareability before you publish.'
  },
  {
    icon: '🚧',
    title: 'Stage-Gate Guardrail',
    description: 'If W_attn < 0.4, the system warns you before running expensive simulations. No wasted GPU credits on content that won\'t engage.'
  },
  {
    icon: '📈',
    title: '7-Day Forecast',
    description: 'Predict reach curves, viral coefficients, and peak audiences. Compare A/B variants side by side before spending a dollar on distribution.'
  },
  {
    icon: '⚡',
    title: 'Predictive A/B Testing',
    description: 'Two versions, one report. The system tells you which has higher neural engagement and social spread. No guesswork, no gut feelings.'
  },
  {
    icon: '📊',
    title: 'Live Dashboard',
    description: 'Neural heatmaps, sentiment breakdowns, CTA optimization scores, and stage-gate pass/fail. All in one glass-panel interface.'
  }
]

const steps = [
  {
    title: 'Upload your content',
    description: 'Drop a video or paste a URL. NeuroSim processes it through TRIBE v2 neural encoding in seconds.'
  },
  {
    title: 'Neural analysis runs',
    description: '70,000 virtual voxels mapped across 4 brain regions. Stage-Gate checks if engagement passes the threshold.'
  },
  {
    title: 'Get predictions',
    description: 'Full report: hook score, viral potential, sentiment forecast, share prediction. Ship with confidence.'
  }
]

function scrollTo(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

function goToLogin() {
  router.push({ name: 'Login' })
}

function goToSignup() {
  router.push({ name: 'Login' })
}

function goToDashboard() {
  router.push({ name: 'Home' })
}
</script>

<style scoped>
/* ===== DESIGN TOKENS ===== */
:root {
  --bg: #000000;
  --surface: rgba(255,255,255,0.04);
  --surface-hover: rgba(255,255,255,0.08);
  --border: rgba(255,255,255,0.08);
  --border-hover: rgba(255,255,255,0.16);
  --text: #ffffff;
  --text-muted: rgba(255,255,255,0.5);
  --text-dim: rgba(255,255,255,0.3);
  --accent: #06d6a0;
  --accent-glow: rgba(6,214,160,0.15);
  --blue: #4361ee;
  --radius: 12px;
  --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --mono: 'JetBrains Mono', 'Fira Code', monospace;
}

.landing {
  background: #000;
  color: #fff;
  font-family: var(--font);
  min-height: 100vh;
  overflow-x: hidden;
}

/* ===== NAVBAR ===== */
.nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(0,0,0,0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
}

.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 32px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-left {
  display: flex;
  align-items: center;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  display: flex;
  align-items: center;
}

.logo-text {
  font-weight: 700;
  font-size: 1.1rem;
  letter-spacing: -0.5px;
}

.logo-version {
  font-family: var(--mono);
  font-size: 0.7rem;
  color: var(--text-muted);
  background: var(--surface);
  padding: 2px 8px;
  border-radius: 4px;
}

.nav-center {
  display: flex;
  gap: 32px;
}

.nav-link {
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: color 0.2s;
}

.nav-link:hover {
  color: var(--text);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* ===== BUTTONS ===== */
.btn-ghost {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.2s;
  font-family: var(--font);
}

.btn-ghost:hover {
  color: var(--text);
  background: var(--surface);
}

.btn-primary {
  background: var(--accent);
  color: #000;
  border: none;
  padding: 10px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.25s;
  font-family: var(--font);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-primary:hover {
  background: #05c996;
  transform: translateY(-1px);
  box-shadow: 0 8px 32px rgba(6,214,160,0.3);
}

.btn-outline {
  background: transparent;
  color: var(--text);
  border: 1px solid var(--border);
  padding: 10px 24px;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.25s;
  font-family: var(--font);
}

.btn-outline:hover {
  border-color: var(--text-muted);
  background: var(--surface);
}

.btn-lg {
  padding: 14px 32px;
  font-size: 1rem;
}

.btn-arrow {
  transition: transform 0.2s;
}

.btn-primary:hover .btn-arrow {
  transform: translateX(4px);
}

/* ===== HERO ===== */
.hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 120px 32px 80px;
  position: relative;
  overflow: hidden;
}

.hero-glow {
  position: absolute;
  top: -200px;
  left: 50%;
  transform: translateX(-50%);
  width: 800px;
  height: 600px;
  background: radial-gradient(ellipse, rgba(6,214,160,0.08) 0%, rgba(67,97,238,0.04) 40%, transparent 70%);
  pointer-events: none;
}

.hero-content {
  max-width: 800px;
  text-align: left;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 100px;
  padding: 6px 16px;
  font-family: var(--mono);
  font-size: 0.75rem;
  letter-spacing: 2px;
  color: var(--text-muted);
  margin-bottom: 32px;
}

.badge-icon {
  color: var(--accent);
}

.hero-title {
  font-size: clamp(3rem, 8vw, 5.5rem);
  font-weight: 700;
  line-height: 1.05;
  letter-spacing: -3px;
  margin: 0 0 32px 0;
}

.hero-cursor {
  color: var(--accent);
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.hero-subtitle {
  font-size: 1.2rem;
  line-height: 1.7;
  color: var(--text-muted);
  max-width: 640px;
  margin: 0 0 40px 0;
}

.hero-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.hero-note {
  font-size: 0.8rem;
  color: var(--text-dim);
}

/* ===== SECTIONS ===== */
.section-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 32px;
}

.section-title {
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 700;
  letter-spacing: -1.5px;
  margin: 0 0 16px 0;
}

.section-subtitle {
  font-size: 1.1rem;
  color: var(--text-muted);
  margin: 0 0 60px 0;
  max-width: 600px;
}

/* ===== FEATURES ===== */
.features-section {
  padding: 120px 0;
  border-top: 1px solid var(--border);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.feature-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 32px;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  opacity: 0;
  transition: opacity 0.3s;
}

.feature-card:hover {
  border-color: var(--border-hover);
  background: var(--surface-hover);
  transform: translateY(-4px);
}

.feature-card:hover::before {
  opacity: 1;
}

.feature-icon {
  font-size: 2rem;
  margin-bottom: 20px;
}

.feature-name {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.feature-desc {
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--text-muted);
  margin: 0;
}

/* ===== STEPS ===== */
.steps-section {
  padding: 120px 0;
  border-top: 1px solid var(--border);
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 40px;
}

.step-card {
  padding: 8px 0;
}

.step-number {
  font-family: var(--mono);
  font-size: 3rem;
  font-weight: 700;
  color: var(--text-dim);
  margin-bottom: 20px;
  line-height: 1;
}

.step-name {
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.step-desc {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--text-muted);
  margin: 0;
}

/* ===== CTA ===== */
.cta-section {
  padding: 120px 0;
  border-top: 1px solid var(--border);
}

.cta-inner {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.cta-title {
  font-size: clamp(2rem, 4vw, 2.8rem);
  font-weight: 700;
  letter-spacing: -1px;
  margin: 0 0 16px 0;
}

.cta-subtitle {
  font-size: 1.1rem;
  color: var(--text-muted);
  margin: 0 0 40px 0;
  max-width: 520px;
}

/* ===== FOOTER ===== */
.footer {
  border-top: 1px solid var(--border);
  padding: 40px 0;
}

.footer-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 20px;
}

.footer-copy {
  font-size: 0.8rem;
  color: var(--text-dim);
}

.footer-links {
  display: flex;
  gap: 24px;
}

.footer-link {
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.85rem;
  transition: color 0.2s;
}

.footer-link:hover {
  color: var(--text);
}

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
  .nav-center {
    display: none;
  }

  .features-grid,
  .steps-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .hero-content {
    text-align: center;
  }

  .hero-actions {
    justify-content: center;
  }

  .footer-inner {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
}
</style>
