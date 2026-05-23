'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { heroReveal, heroRevealDelayed, fadeIn, staggerItem, easeOutExpo, scanLine, pulseSlow, pulseSlowDelayed, pulseFast } from '../lib/easing'
import { 
  Brain, Users, Shield, TrendingUp, Target, BarChart3, 
  ArrowRight, Check, Sparkles, Waves, Radio, Crosshair, Zap, Eye
} from 'lucide-react'

const pillars = [
  {
    icon: Brain, title: 'Predictive Content Scoring',
    desc: 'Linguistic engagement signals across 4 dimensions: visual, auditory, persuasion, and social. Scores your content\'s predicted audience response before you publish.',
    color: 'text-neural', border: 'border-neural/20', bg: 'bg-neural/5',
    badge: 'NEURAL ENGINE',
  },
  {
    icon: Users, title: 'MiroFish — Swarm Simulation',
    desc: '1,000-agent social simulation across 8 persona types. Predict viral spread, sentiment drift, backlash risk, and shareability before you publish.',
    color: 'text-swarm', border: 'border-swarm/20', bg: 'bg-swarm/5',
    badge: 'SOCIAL ENGINE',
  },
  {
    icon: Zap, title: 'Virality Predictor',
    desc: 'Upload a clip and get instant virality scoring powered by advanced AI video understanding. Hook strength, hold rate, engagement curve, and 3D brain activation in seconds.',
    color: 'text-signal-green', border: 'border-signal-green/20', bg: 'bg-signal-green/5',
    badge: 'VISION ENGINE',
    isNew: true,
  },
]

const features = [
  {
    icon: Target, title: 'Script Analysis',
    desc: 'Paste your video script and get instant predictions. Hook strength, emotional arc, viral potential, and CTA effectiveness in seconds, no video needed.',
    color: 'text-neural', border: 'border-neural/20', bg: 'bg-neural/5',
  },
  {
    icon: Eye, title: 'Vision-Powered Scoring',
    desc: 'AI vision watches your clip and scores hook strength, hold rate, and per-second engagement. Vision scores dominate the merge at 55-65% weight.',
    color: 'text-signal-green', border: 'border-signal-green/20', bg: 'bg-signal-green/5',
  },
  {
    icon: Shield, title: 'Stage-Gate Guardrail',
    desc: 'If W_attn < 0.4, the system warns you before running expensive simulations. No wasted GPU credits on content that won\'t engage.',
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
    items: ['10 analyses/month', 'Neural encoding analysis', 'MiroFish swarm simulation', 'Stage-Gate guardrail', 'A/B comparison'],
    cta: 'Get Started Free',
    disabled: false,
    href: '/dashboard',
  },
  {
    name: 'Pro', price: '—', popular: true,
    items: ['Unlimited analyses', 'Priority processing', 'Custom ROI thresholds', 'Export reports (PDF/CSV)', 'API access', 'Team collaboration'],
    cta: 'Coming Soon',
    disabled: true,
    href: '/waitlist',
    priceActive: 29,
  },
]

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export default function LandingPage() {
  const router = useRouter()
  const [proEnabled, setProEnabled] = useState(false)

  useEffect(() => {
    fetch(`${API_URL}/api/v1/premium/status`)
      .then(r => r.json())
      .then(data => { setProEnabled(data.stripe_configured && data.enabled) })
      .catch(() => {})
  }, [])

  const proPlan = proEnabled
    ? { ...plans[1], cta: 'Upgrade to Pro', disabled: false, href: '/pricing', price: String(plans[1].priceActive ?? 29) }
    : plans[1]

  const displayPlans = [plans[0], proPlan]

  return (
    <div className="bg-neural neural-grid min-h-screen">
      <div className="relative z-10">

        {/* ===== HERO ===== */}
        <section aria-label="Hero" className="max-w-7xl mx-auto px-4 sm:px-6 pt-16 pb-20 md:pt-32 md:pb-36">
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
                  <span className="text-[11px] font-mono text-neural tracking-[0.15em] uppercase">Three Engines · One Prediction</span>
                </div>

                <h1 className="text-[clamp(2rem,6vw,4.5rem)] sm:text-[clamp(2.5rem,6vw,4.5rem)] font-bold text-white leading-[1.02] tracking-[-0.03em] mb-4 sm:mb-6">
                  Predict virality{' '}
                  <span className="text-gradient">before</span>
                  {' '}you publish
                </h1>

                <p className="text-base sm:text-lg md:text-xl text-gray-400 max-w-xl leading-relaxed mb-8 sm:mb-10">
                  Neural encoding maps brain response. MiroFish simulates social spread.
                  Virality Predictor scores your clip with AI vision. Three engines, one score.
                </p>

                <div className="flex items-center gap-4 flex-wrap">
                  <button onClick={() => router.push('/dashboard')} className="btn-neural inline-flex items-center gap-2" aria-label="Go to dashboard">
                    <span>Go to Dashboard</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                  <Link href="/#features" className="btn-ghost" aria-label="See all features">
                    See Features
                  </Link>
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
                    <span className="text-[10px] font-mono text-gray-500 tracking-wide">Neural</span>
                    <span className="w-px h-3 bg-white/10 mx-1" />
                    <span className="status-dot status-swarm" />
                    <span className="text-[10px] font-mono text-gray-500 tracking-wide">MIROFISH</span>
                    <span className="w-px h-3 bg-white/10 mx-1" />
                    <span className="status-dot status-green" />
                    <span className="text-[10px] font-mono text-gray-500 tracking-wide">PREDICT</span>
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

        {/* ===== THREE PILLARS ===== */}          <section id="features" aria-label="Features" className="max-w-7xl mx-auto px-4 sm:px-6 py-16 md:py-32">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={fadeIn}
            className="max-w-2xl mb-16"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.06] mb-6">
              <Crosshair className="w-3 h-3 text-neural" />
              <span className="text-[10px] font-mono text-neural/60 tracking-[0.15em] uppercase">Three Engines</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4 tracking-[-0.02em] leading-[1.05]">
              Three engines,<br />
              <span className="text-gradient">one prediction</span>
            </h2>
            <p className="text-lg text-gray-400 max-w-xl leading-relaxed">
              Biological brain response, social swarm simulation, and AI vision scoring.
              No other platform combines all three.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6 mb-16">
            {pillars.map((p, i) => (
              <motion.div
                key={p.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={p.isNew ? { opacity: 1, y: [0, -8, 0] } : { opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={p.isNew ? { y: { duration: 4, repeat: Infinity, ease: "easeInOut" }, opacity: { duration: 0.6 } } : staggerItem(i, 0.1)}
                className={`group relative rounded-2xl border ${p.border} p-5 sm:p-8 transition-all ${
                  p.isNew 
                    ? 'glass-green ring-1 ring-signal-green/30 shadow-[0_0_40px_-8px_rgba(74,222,128,0.25)] hover:shadow-[0_0_60px_-8px_rgba(74,222,128,0.35)]' 
                    : 'bg-white/[0.02] hover:bg-white/[0.04]'
                }`}
              >
                {p.isNew && (
                  <>
                    <div className="absolute -top-3 left-6 px-3 py-0.5 rounded-full bg-signal-green/15 border border-signal-green/25 z-10">
                      <span className="text-[9px] font-mono text-signal-green font-semibold tracking-[0.15em] uppercase">New</span>
                    </div>
                    <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(74,222,128,0.12),transparent_60%)] pointer-events-none rounded-2xl" />
                  </>
                )}
                <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full ${p.bg} ${p.border} border mb-5`}>
                  <p.icon className={`w-3.5 h-3.5 ${p.color}`} />
                  <span className="text-[9px] font-mono tracking-[0.12em] uppercase text-gray-400">{p.badge}</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-3">{p.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{p.desc}</p>
                {p.isNew && (
                  <div className="mt-6">
                    <button
                      onClick={() => router.push('/predict')}
                      className={`inline-flex items-center gap-2 text-xs font-medium ${p.color} hover:underline`}
                    >
                      Try Virality Predictor <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </motion.div>
            ))}
          </div>

          {/* Utility features — 5-column grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={staggerItem(i)}
                className="group rounded-2xl bg-white/[0.02] border border-white/[0.06] p-4 sm:p-6 hover:bg-white/[0.04] hover:border-white/[0.1] transition-all"
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
        <section id="pipeline" aria-label="How it works" className="max-w-5xl mx-auto px-4 sm:px-6 py-16 md:py-32">
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
            <div className="hidden md:block absolute top-12 left-[calc(16.66%+24px)] right-[calc(16.66%+24px)] h-px bg-gradient-to-r from-neural/30 via-swarm/30 to-signal-green/30" />

            {[
              { num: '01', title: 'Input Video or Script', desc: 'Drop a video for full analysis, paste a script for instant scoring, or use the Virality Predictor for quick clip evaluation.' },
              { num: '02', title: 'Tri-Engine Prediction', desc: 'Neural encoding maps brain response. MiroFish runs 1,000-agent swarm simulation. AI vision scores visual engagement.' },
              { num: '03', title: 'Actionable Insights', desc: 'Unified score: hook strength, viral potential, sentiment forecast, engagement curve, and 3D brain activation. Ship with confidence.' },
            ].map((s, i) => (
              <motion.div
                key={s.num}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, ...fadeIn }}
                className="flex flex-col items-center text-center px-4 sm:px-8 relative"
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
        <section aria-label="Pricing" className="max-w-4xl mx-auto px-4 sm:px-6 py-16 md:py-32">
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
            {displayPlans.map((p, i) => (
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
                  <span className="text-4xl font-bold text-white font-mono tracking-tight">{p.price === '—' ? '—' : `\$${p.price}`}</span>
                  {p.price !== '—' && <span className="text-sm text-gray-500 font-mono">/mo</span>}
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
                  onClick={p.disabled ? undefined : () => router.push(p.href || '/dashboard')}
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
        <section aria-label="Call to action" className="max-w-5xl mx-auto px-4 sm:px-6 pb-20 md:pb-32">
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
              <button onClick={() => router.push('/dashboard')} className="btn-neural inline-flex items-center gap-2" aria-label="Open dashboard">
                Open Dashboard <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          </motion.div>
        </section>

        {/* ===== FOOTER ===== */}
        <footer className="border-t border-white/[0.04] py-6 sm:py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-0">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-neural" />
              <span className="text-xs text-gray-500">NeuroSim v3.0</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-[10px] text-gray-600 font-mono">Neural</span>
              <span className="text-[10px] text-gray-700">+</span>
              <span className="text-[10px] text-gray-600 font-mono">MiroFish</span>
              <span className="text-[10px] text-gray-700">+</span>
              <span className="text-[10px] text-signal-green/60 font-mono">Predict</span>
            </div>
          </div>
        </footer>

      </div>
    </div>
  )
}


