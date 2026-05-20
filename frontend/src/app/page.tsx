'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '../lib/auth-context'
import { supabase } from '../lib/supabase'
import { motion } from 'framer-motion'
import { heroReveal, heroRevealDelayed, fadeIn, staggerItem, easeOutExpo, scanLine, pulseSlow, pulseSlowDelayed, pulseFast } from '../lib/easing'
import { 
  Brain, Users, Shield, TrendingUp, Target, BarChart3, 
  ArrowRight, Check, Sparkles, Waves, Radio, Crosshair
} from 'lucide-react'

const features = [
  {
    icon: Target, title: 'Script Analysis',
    desc: 'Paste your video script and get instant predictions. Hook strength, emotional arc, viral potential, and CTA effectiveness in seconds, no video needed.',
    color: 'text-neural', border: 'border-neural/20', bg: 'bg-neural/5',
  },
  {
    icon: Brain, title: 'TRIBE v2 Brain Encoding',
    desc: 'Upload a video and get fMRI-level brain activation maps across 4 regions. Meta\u2019s neural response model predicts visual, auditory, and emotional engagement.',
    color: 'text-neural', border: 'border-neural/20', bg: 'bg-neural/5',
  },
  {
    icon: Users, title: 'MiroFish Swarm Simulation',
    desc: '1000-agent social simulation across 8 persona types. Predict viral spread, sentiment drift, backlash risk, and shareability before you publish.',
    color: 'text-swarm', border: 'border-swarm/20', bg: 'bg-swarm/5',
  },
  {
    icon: Shield, title: 'Stage-Gate Guardrail',
    desc: 'If W_attn < 0.4, the system warns you before running expensive simulations. No wasted GPU credits on content that won\u2019t engage.',
    color: 'text-signal-green', border: 'border-signal-green/20', bg: 'bg-signal-green/5',
  },
  {
    icon: TrendingUp, title: '7-Day Forecast',
    desc: 'Predict reach curves, viral coefficients, and peak audiences. Compare A/B variants side by side before spending a dollar on distribution.',
    color: 'text-neural', border: 'border-neural/20', bg: 'bg-neural/5',
  },
  {
    icon: BarChart3, title: 'Benchmark Comparison',
    desc: 'Compare your scores against 43K+ videos across education, entertainment, gaming, and music cohorts. Know where you stand.',
    color: 'text-swarm', border: 'border-swarm/20', bg: 'bg-swarm/5',
  },
]

const plans = [
  {
    name: 'Free', price: '0', popular: false,
    items: ['10 analyses/month', 'TRIBE v2 brain encoding', 'MiroFish swarm simulation', 'Stage-Gate guardrail', 'A/B comparison'],
    cta: 'Get Started Free',
  },
  {
    name: 'Pro', price: '29', popular: true,
    items: ['Unlimited analyses', 'Priority processing', 'Custom ROI thresholds', 'Export reports (PDF/CSV)', 'API access', 'Team collaboration'],
    cta: 'Coming Soon',
    disabled: true,
  },
]

export default function LandingPage() {
  const router = useRouter()

  return (
    <div className="bg-neural neural-grid min-h-screen">
      <div className="relative z-10">

        {/* ===== HERO ===== */}
        <section aria-label="Hero" className="max-w-7xl mx-auto px-6 pt-24 pb-28 md:pt-32 md:pb-36">
          <div className="grid md:grid-cols-12 gap-12 items-center">
            
            {/* Left: text — 7 cols */}
            <div className="md:col-span-7">
              <motion.div
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={heroReveal}
              >
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-neural/10 border border-neural/20 mb-8">
                  <Radio className="w-3 h-3 text-neural" />
                  <span className="text-[11px] font-mono text-neural tracking-[0.15em] uppercase">Predictive Content Intelligence</span>
                </div>

                <h1 className="text-[clamp(2.5rem,6vw,4.5rem)] font-bold text-white leading-[1.02] tracking-[-0.03em] mb-6">
                  Analyze your content{' '}
                  <span className="text-gradient">before</span>
                  {' '}you create
                </h1>

                <p className="text-lg md:text-xl text-gray-400 max-w-xl leading-relaxed mb-10">
                  Paste a script for instant predictions, or upload a video for full neural analysis.
                  Know how your content performs before you film, edit, or publish.
                </p>

                <div className="flex items-center gap-4 flex-wrap">
                  <button onClick={() => router.push('/dashboard')} className="btn-neural inline-flex items-center gap-2" aria-label="Go to dashboard">
                    <span>Go to Dashboard</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                  <a href="#features" className="btn-ghost" aria-label="See all features">
                    See Features
                  </a>
                </div>

                <p className="text-xs text-gray-500 mt-5 font-mono tracking-wide" aria-label="Pricing info">No credit card &middot; Free tier includes 10 analyses per month</p>
              </motion.div>
            </div>

            {/* Right: neural visual — 5 cols */}
            <div className="md:col-span-5" aria-hidden="true">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={heroRevealDelayed()}
                className="relative"
              >
                {/* Scan-line container */}
                <div className="relative aspect-[4/3] rounded-2xl border border-white/[0.06] bg-white/[0.015] overflow-hidden">
                  
                  {/* Scan line sweep */}
                  <motion.div
                    className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-neural/60 to-transparent z-10"
                    initial={{ top: '0%' }}
                    animate={{ top: ['0%', '100%', '0%'] }}
                    transition={scanLine}
                  />

                  {/* Inner glow */}
                  <div className="absolute inset-0 bg-gradient-to-br from-neural/5 via-transparent to-swarm/5" />

                  {/* Pulsing neural rings */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <motion.div
                      className="w-48 h-48 rounded-full border border-neural/20"
                      animate={{ scale: [1, 1.08, 1], opacity: [0.3, 0.6, 0.3] }}
                      transition={pulseSlow}
                    />
                    <motion.div
                      className="absolute w-36 h-36 rounded-full border border-swarm/15"
                      animate={{ scale: [1.08, 1, 1.08], opacity: [0.2, 0.5, 0.2] }}
                      transition={pulseSlowDelayed()}
                    />
                    <motion.div
                      className="absolute w-24 h-24 rounded-full bg-neural/8 blur-xl"
                      animate={{ scale: [1, 1.15, 1], opacity: [0.4, 0.8, 0.4] }}
                      transition={Object.assign({}, pulseFast, { delay: 1 })}
                    />
                  </div>

                  {/* Center icon */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-16 h-16 rounded-2xl bg-neural/10 border border-neural/20 flex items-center justify-center backdrop-blur-sm">
                      <Brain className="w-8 h-8 text-neural" />
                    </div>
                  </div>

                  {/* Status indicators */}
                  <div className="absolute bottom-4 left-4 flex items-center gap-2">
                    <span className="status-dot status-neural" />
                    <span className="text-[10px] font-mono text-gray-500 tracking-wide">TRIBE v2</span>
                    <span className="w-px h-3 bg-white/10 mx-1" />
                    <span className="status-dot status-swarm" />
                    <span className="text-[10px] font-mono text-gray-500 tracking-wide">MIROFISH</span>
                  </div>

                  {/* Crosshair measurement marks */}
                  <div className="absolute top-4 right-4 flex flex-col items-end gap-1">
                    <span className="text-[10px] font-mono text-gray-600">W_attn</span>
                    <span className="text-xs font-mono text-neural/60">0.72</span>
                  </div>
                  <div className="absolute bottom-4 right-4 flex items-center gap-1">
                    <span className="text-[10px] font-mono text-gray-600">threshold</span>
                    <span className="text-[10px] font-mono text-neural/40">0.4</span>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </section>

        {/* ===== FEATURES ===== */}
        <section id="features" aria-label="Features" className="max-w-7xl mx-auto px-6 py-24 md:py-32">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={fadeIn}
            className="max-w-2xl mb-16"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.06] mb-6">
              <Crosshair className="w-3 h-3 text-neural" />
              <span className="text-[10px] font-mono text-neural/60 tracking-[0.15em] uppercase">Instrumentation</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4 tracking-[-0.02em] leading-[1.05]">
              Two engines,<br />
              <span className="text-gradient">one prediction</span>
            </h2>
            <p className="text-lg text-gray-400 max-w-xl leading-relaxed">
              Biological brain response plus social swarm simulation. No other tool does both.
            </p>
          </motion.div>

          {/* Marquee features — wider, more prominent */}
          <div className="grid md:grid-cols-2 gap-4 mb-4">
            {features.slice(0, 2).map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={staggerItem(i, 0.1)}
                className="group relative rounded-2xl bg-white/[0.02] border border-white/[0.06] p-8 hover:bg-white/[0.04] hover:border-white/[0.1] transition-all"
              >
                <div className="flex items-start gap-5">
                  <div className={`w-12 h-12 rounded-xl ${f.bg} ${f.border} border flex items-center justify-center flex-shrink-0`}>
                    <f.icon className={`w-6 h-6 ${f.color}`} />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white mb-2">{f.title}</h3>
                    <p className="text-sm text-gray-500 leading-relaxed max-w-md">{f.desc}</p>
                    <div className="flex items-center gap-2 mt-4 text-[11px] font-mono text-neural/50 group-hover:text-neural/80 transition-colors">
                      <span className="w-4 h-px bg-neural/30" />
                      Learn more
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Utility features — 2x2 grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {features.slice(2).map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={staggerItem(i)}
                className="group rounded-2xl bg-white/[0.02] border border-white/[0.06] p-6 hover:bg-white/[0.04] hover:border-white/[0.1] transition-all"
              >
                <div className={`w-10 h-10 rounded-xl ${f.bg} ${f.border} border flex items-center justify-center mb-4`}>
                  <f.icon className={`w-5 h-5 ${f.color}`} />
                </div>
                <h3 className="text-sm font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ===== HOW IT WORKS — PIPELINE ===== */}
        <section id="pipeline" aria-label="How it works" className="max-w-5xl mx-auto px-6 py-24 md:py-32">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={fadeIn}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.06] mb-6">
              <Waves className="w-3 h-3 text-swarm" />
              <span className="text-[10px] font-mono text-swarm/60 tracking-[0.15em] uppercase">Pipeline</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 tracking-[-0.02em]">
              Three steps to insight
            </h2>
            <p className="text-gray-400 max-w-md mx-auto">From raw video to predictive report in under a minute.</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-0 relative">
            {/* Connecting line (desktop) */}
            <div className="hidden md:block absolute top-12 left-[calc(16.66%+24px)] right-[calc(16.66%+24px)] h-px bg-gradient-to-r from-neural/30 via-swarm/30 to-neural/30" />

            {[
              { num: '01', title: 'Upload your content', desc: 'Drop a video or paste a URL. NeuroSim processes it through TRIBE v2 neural encoding in seconds.' },
              { num: '02', title: 'Neural analysis runs', desc: '70,000 virtual voxels mapped across 4 brain regions. Stage-Gate checks if engagement passes the threshold.' },
              { num: '03', title: 'Get predictions', desc: 'Full report: hook score, viral potential, sentiment forecast, share prediction. Ship with confidence.' },
            ].map((s, i) => (
              <motion.div
                key={s.num}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, ...fadeIn }}
                className="flex flex-col items-center text-center px-8 relative"
              >
                <div className="w-12 h-12 rounded-full bg-neural/10 border border-neural/20 flex items-center justify-center mb-5 z-10 relative">
                  <span className="text-lg font-bold font-mono text-neural">{s.num}</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{s.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed max-w-xs">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ===== PRICING ===== */}
        <section aria-label="Pricing" className="max-w-4xl mx-auto px-6 py-24 md:py-32">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={fadeIn}
            className="max-w-xl mb-16"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-neural/10 border border-neural/20 mb-6">
              <Sparkles className="w-3 h-3 text-neural" />
              <span className="text-[10px] font-mono text-neural/60 tracking-[0.15em] uppercase">Pricing</span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 tracking-[-0.02em]">Simple pricing</h2>
            <p className="text-gray-400">Start free. Upgrade when you need more analyses.</p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6">
            {plans.map((p, i) => (
              <motion.div
                key={p.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, ...fadeIn }}
                className={`relative rounded-2xl p-8 flex flex-col ${
                  p.popular
                    ? 'bg-gradient-to-b from-neural/8 to-swarm/5 border border-neural/20 shadow-[0_0_40px_-8px_rgba(77,238,234,0.08)]'
                    : 'bg-white/[0.02] border border-white/[0.06]'
                }`}
              >
                {p.popular && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-5 py-1 rounded-full bg-gradient-to-r from-neural/20 to-swarm/20 border border-neural/25 backdrop-blur-sm">
                    <span className="text-[10px] font-mono text-neural font-semibold tracking-[0.15em] uppercase">Most Capable</span>
                  </div>
                )}
                <h3 className="text-lg font-semibold text-white mb-1">{p.name}</h3>
                <div className="flex items-baseline gap-0.5 mb-6">
                  <span className="text-4xl font-bold text-white font-mono tracking-tight">${p.price}</span>
                  <span className="text-sm text-gray-500 font-mono">/mo</span>
                </div>
                <ul className="space-y-3 mb-8 flex-1">
                  {p.items.map(item => (
                    <li key={item} className="flex items-start gap-3 text-sm text-gray-400">
                      <Check className={`w-4 h-4 ${p.popular ? 'text-swarm' : 'text-neural'} mt-0.5 flex-shrink-0`} />
                      {item}
                    </li>
                  ))}
                </ul>
                <button
                  disabled={p.disabled}
                  onClick={p.disabled ? undefined : (isSignedIn ? () => router.push('/dashboard') : handleAuth)}
                  className={`w-full py-3 rounded-xl text-sm font-semibold transition-all ${
                    p.popular
                      ? 'bg-gradient-to-r from-neural/15 to-swarm/15 border border-neural/25 text-neural hover:from-neural/25 hover:to-swarm/25'
                      : 'bg-neural/10 border border-neural/25 text-neural hover:bg-neural/20'
                  } ${p.disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
                  aria-label={`${p.cta}${p.disabled ? ' (coming soon)' : ''}`}
                >
                  {p.cta}
                </button>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ===== CTA ===== */}
        <section aria-label="Call to action" className="max-w-5xl mx-auto px-6 pb-32">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={fadeIn}
            className="relative rounded-3xl overflow-hidden"
          >
            {/* Background atmosphere */}
            <div className="absolute inset-0 bg-gradient-to-br from-neural/8 via-swarm/5 to-neural/8 border border-neural/15 rounded-3xl" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_0%,rgba(77,238,234,0.06),transparent_60%)]" />
            
            {/* Neural scan line accent */}
            <div className="absolute inset-x-[10%] top-0 h-px bg-gradient-to-r from-transparent via-neural/30 to-transparent" />

            <div className="relative px-8 py-16 md:px-16 md:py-20 text-center">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-neural/10 border border-neural/15 mb-6">
                <Sparkles className="w-3 h-3 text-neural" />
                <span className="text-[10px] font-mono text-neural/60 tracking-[0.15em] uppercase">Ready</span>
              </div>
              <h2 className="text-3xl md:text-5xl font-bold text-white mb-4 tracking-[-0.02em] leading-[1.05]">
                Ready to predict<br />
                <span className="text-gradient">your next hit?</span>
              </h2>
              <p className="text-gray-400 max-w-md mx-auto mb-10">
                Upload a video, get neural and social predictions. Free to start, no credit card.
              </p>
              {isSignedIn ? (
                <button onClick={() => router.push('/dashboard')} className="btn-neural inline-flex items-center gap-2" aria-label="Open dashboard">
                  Open Dashboard <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </button>
              ) : (
                <button onClick={handleAuth} className="btn-neural inline-flex items-center gap-2" aria-label="Start for free">
                  Start Free <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </button>
              )}
            </div>
          </motion.div>
        </section>

        {/* ===== FOOTER ===== */}
        <footer className="border-t border-white/[0.04] py-8">
          <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-neural" />
              <span className="text-xs text-gray-500">NeuroSim v3.0</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-[10px] text-gray-600 font-mono">TRIBE v2</span>
              <span className="text-[10px] text-gray-700">+</span>
              <span className="text-[10px] text-gray-600 font-mono">MiroFish</span>
            </div>
          </div>
        </footer>

      </div>
    </div>
  )
}


