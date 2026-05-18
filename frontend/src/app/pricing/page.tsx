'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../lib/auth-context'
import { supabase } from '../../lib/supabase'
import { motion } from 'framer-motion'
import { Check, Sparkles, Brain, Cpu, ArrowRight } from 'lucide-react'

const tiers = [
  {
    name: 'Free',
    monthly: 0,
    yearly: 0,
    desc: 'Perfect for creators exploring predictive intelligence.',
    features: [
      '10 analyses per month',
      'TRIBE v2 simulated brain encoding',
      'MiroFish swarm simulation',
      'Stage-Gate guardrail check',
      'A/B content comparison',
      'Basic PDF reports',
    ],
    cta: 'Start Free',
    popular: false,
  },
  {
    name: 'Premium',
    monthly: 29,
    yearly: 290,
    desc: 'Unlimited access with real GPU-powered neural processing.',
    features: [
      'Unlimited analyses',
      'Real GPU TRIBE v2 encoding',
      'Priority swarm simulation',
      'Custom ROI thresholds',
      'Export reports (PDF/CSV)',
      'API access',
      'Team collaboration',
    ],
    cta: 'Join Waitlist',
    popular: true,
    comingSoon: true,
  },
]

export default function PricingPage() {
  const [yearly, setYearly] = useState(false)
  const router = useRouter()
  const { isSignedIn } = useAuth()

  const handleCTA = (tier: typeof tiers[0]) => {
    if (tier.name === 'Free') {
      if (isSignedIn) {
        router.push('/dashboard')
      } else if (supabase) {
        supabase.auth.signInWithOAuth({
          provider: 'google',
          options: { redirectTo: window.location.origin + '/dashboard' }
        })
      } else {
        router.push('/dashboard')
      }
    } else {
      router.push('/waitlist')
    }
  }

  return (
    <div className="bg-neural neural-grid min-h-screen">
      <div className="relative z-10">
        <section className="max-w-6xl mx-auto px-6 pt-24 pb-32 md:pt-32 md:pb-40">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-neural/10 border border-neural/20 mb-6">
              <Sparkles className="w-3 h-3 text-neural" />
              <span className="text-[11px] font-mono text-neural tracking-[0.15em] uppercase">Pricing</span>
            </div>
            <h1 className="text-[clamp(2rem,5vw,3.5rem)] font-bold text-white leading-[1.02] tracking-[-0.03em] mb-4">
              Simple, transparent<span className="text-gradient"> pricing</span>
            </h1>
            <p className="text-lg text-gray-400 max-w-md mx-auto">Start free. Upgrade when you need real GPU processing.</p>

            <div className="inline-flex items-center gap-2 mt-10 p-1 rounded-xl bg-white/[0.04] border border-white/[0.06]">
              <button
                onClick={() => setYearly(false)}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${!yearly ? 'bg-white/[0.08] text-white' : 'text-text-tertiary hover:text-white'}`}
              >
                Monthly
              </button>
              <button
                onClick={() => setYearly(true)}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${yearly ? 'bg-white/[0.08] text-white' : 'text-text-tertiary hover:text-white'}`}
              >
                Yearly
                <span className="ml-2 text-[10px] mono text-green-400">-17%</span>
              </button>
            </div>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {tiers.map((tier, i) => {
              const price = yearly ? tier.yearly : tier.monthly
              return (
                <motion.div
                  key={tier.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                  className={`relative rounded-2xl p-8 flex flex-col ${
                    tier.popular
                      ? 'bg-gradient-to-b from-neural/8 to-swarm/5 border border-neural/20 shadow-[0_0_40px_-8px_rgba(77,238,234,0.08)]'
                      : 'bg-white/[0.02] border border-white/[0.06]'
                  }`}
                >
                  {tier.popular && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-5 py-1 rounded-full bg-gradient-to-r from-neural/20 to-swarm/20 border border-neural/25 backdrop-blur-sm flex items-center gap-2">
                      <Cpu className="w-3 h-3 text-neural" />
                      <span className="text-[10px] font-mono text-neural font-semibold tracking-[0.15em] uppercase">GPU Powered</span>
                    </div>
                  )}
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-white">{tier.name}</h3>
                    {tier.comingSoon && (
                      <span className="badge badge-ghost text-[10px]">Coming soon</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mb-6">{tier.desc}</p>

                  <div className="flex items-baseline gap-1 mb-6">
                    <span className="text-4xl font-bold text-white font-mono tracking-tight">
                      {price === 0 ? 'Free' : `$${price}`}
                    </span>
                    {price > 0 && (
                      <span className="text-sm text-gray-500 font-mono">/{yearly ? 'yr' : 'mo'}</span>
                    )}
                  </div>

                  <ul className="space-y-3 mb-8 flex-1">
                    {tier.features.map((feat) => (
                      <li key={feat} className="flex items-start gap-3 text-sm text-gray-400">
                        <Check className={`w-4 h-4 ${tier.popular ? 'text-swarm' : 'text-neural'} mt-0.5 flex-shrink-0`} />
                        {feat}
                      </li>
                    ))}
                  </ul>

                  <button
                    onClick={() => handleCTA(tier)}
                    className="group w-full py-3 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer bg-neural/10 border border-neural/25 text-neural hover:bg-neural/20"
                  >
                    {tier.cta}
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </motion.div>
              )
            })}
          </div>
        </section>
      </div>
    </div>
  )
}
