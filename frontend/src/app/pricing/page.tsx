'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../lib/auth-context'
import { supabase } from '../../lib/supabase'
import { motion } from 'framer-motion'
import { heroReveal, staggerItem, easeOutExpo } from '../../lib/easing'
import { Check, Sparkles, Brain, Cpu, ArrowRight, Loader2 } from 'lucide-react'

const TIERS = [
  {
    name: 'Free',
    monthly: 0,
    yearly: 0,
    desc: 'Heuristic content analysis — no GPU required.',
    features: [
      '10 analyses per month',
      'Audio transcription (Whisper)',
      'Heuristic neural scoring',
      'MiroFish swarm simulation',
      'Stage-Gate guardrail check',
      'A/B content comparison',
      'Basic PDF reports',
    ],
    cta: 'Start Free',
    popular: false,
    stripePriceId: null,
  },
  {
    name: 'Pro',
    monthly: 29,
    yearly: 290,
    desc: 'LLM-enhanced analysis with deeper content insights.',
    features: [
      'Unlimited analyses',
      'LLM-enhanced content analysis',
      'Priority swarm simulation',
      'Custom ROI thresholds',
      'Export reports (PDF/CSV)',
      'API access',
      'Team collaboration',
    ],
    cta: 'Upgrade to Pro',
    ctaWaitlist: 'Join Waitlist',
    popular: true,
  },
]

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export default function PricingPage() {
  const [yearly, setYearly] = useState(false)
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null)
  const [stripePriceIdMonthly, setStripePriceIdMonthly] = useState<string | null>(null)
  const [stripePriceIdYearly, setStripePriceIdYearly] = useState<string | null>(null)
  const [stripeConfigured, setStripeConfigured] = useState(false)
  const [premiumEnabled, setPremiumEnabled] = useState(false)
  const router = useRouter()
  const { isSignedIn, user, isDemoMode } = useAuth()

  useEffect(() => {
    fetch(`${API_URL}/api/v1/premium/status`)
      .then(r => r.json())
      .then(data => {
        setStripePriceIdMonthly(data.stripe_price_id_monthly)
        setStripePriceIdYearly(data.stripe_price_id_yearly)
        setStripeConfigured(data.stripe_configured)
        setPremiumEnabled(data.enabled)
      })
      .catch(() => {})
  }, [])

  const handleCTA = async (tier: typeof TIERS[0]) => {
    if (tier.name === 'Free') {
      router.push('/dashboard')
      return
    }

    // Pro tier
    if (!stripeConfigured) {
      router.push('/waitlist')
      return
    }

    const priceId = yearly ? stripePriceIdYearly : stripePriceIdMonthly
    if (!priceId) {
      router.push('/waitlist')
      return
    }

    setCheckoutLoading(tier.name)
    try {
      const userId = user?.id || (isDemoMode ? 'demo-user' : undefined)
      const res = await fetch(`${API_URL}/api/v1/stripe/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          price_id: priceId,
          success_url: window.location.origin + '/dashboard',
          cancel_url: window.location.origin + '/pricing',
          user_id: userId,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        console.error('Checkout error:', err)
        router.push('/waitlist')
        return
      }
      const data = await res.json()
      if (data.url) {
        window.location.href = data.url
      }
    } catch (e) {
      console.error('Checkout error:', e)
      router.push('/waitlist')
    } finally {
      setCheckoutLoading(null)
    }
  }

  return (
    <div className="bg-neural neural-grid min-h-screen">
      <div className="relative z-10">
        <section className="max-w-6xl mx-auto px-6 pt-24 pb-32 md:pt-32 md:pb-40">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={heroReveal}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-neural/10 border border-neural/20 mb-6">
              <Sparkles className="w-3 h-3 text-neural" />
              <span className="text-[11px] font-mono text-neural tracking-[0.15em] uppercase">Pricing</span>
            </div>
            <h1 className="text-[clamp(2rem,5vw,3.5rem)] font-bold text-white leading-[1.02] tracking-[-0.03em] mb-4">
              Simple, transparent <span className="text-gradient">pricing</span>
            </h1>
              <p className="text-lg text-gray-400 max-w-md mx-auto">Start free. Upgrade when you need deeper analysis.</p>

            <div
              className="inline-flex items-center gap-2 mt-10 p-1 rounded-xl bg-white/[0.04] border border-white/[0.06]"
              role="radiogroup"
              aria-label="Billing period"
              onKeyDown={(e) => {
                if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                  e.preventDefault()
                  setYearly(yearly => !yearly)
                }
              }}
            >
              <button
                onClick={() => setYearly(false)}
                tabIndex={!yearly ? 0 : -1}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${!yearly ? 'bg-white/[0.08] text-white' : 'text-text-tertiary hover:text-white'}`}
                role="radio"
                aria-checked={!yearly}
                aria-label="Monthly billing"
              >
                Monthly
              </button>
              <button
                onClick={() => setYearly(true)}
                tabIndex={yearly ? 0 : -1}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${yearly ? 'bg-white/[0.08] text-white' : 'text-text-tertiary hover:text-white'}`}
                role="radio"
                aria-checked={yearly}
                aria-label="Yearly billing — save 17 percent"
              >
                Yearly
                <span className="ml-2 text-[10px] mono text-signal-green">-17%</span>
              </button>
            </div>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {TIERS.map((tier, i) => {
              const price = yearly ? tier.yearly : tier.monthly
              const ctaText = tier.name === 'Pro' && !stripeConfigured ? tier.ctaWaitlist : tier.cta
              const isLoading = checkoutLoading === tier.name
              return (
                <motion.div
                  key={tier.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={staggerItem(i, 0.1)}
                  className={`relative rounded-2xl p-8 flex flex-col ${
                    tier.popular
                      ? 'bg-gradient-to-b from-neural/8 to-swarm/5 border border-neural/20 shadow-[0_0_40px_-8px_rgba(77,238,234,0.08)]'
                      : 'bg-white/[0.02] border border-white/[0.06]'
                  }`}
                >
                  {tier.popular && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-5 py-1 rounded-full bg-gradient-to-r from-neural/20 to-swarm/20 border border-neural/25 backdrop-blur-sm flex items-center gap-2">
                      <Cpu className="w-3 h-3 text-neural" />
                      <span className="text-[10px] font-mono text-neural font-semibold tracking-[0.15em] uppercase">AI Enhanced</span>
                    </div>
                  )}
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-white">{tier.name}</h3>
                    {!premiumEnabled && (
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
                    disabled={isLoading}
                    className={`group w-full py-3 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer ${
                      isLoading
                        ? 'bg-neural/5 border border-neural/15 text-neural/60 cursor-not-allowed'
                        : 'bg-neural/10 border border-neural/25 text-neural hover:bg-neural/20'
                    }`}
                    aria-label={`${tier.name} plan: ${ctaText}`}
                    aria-busy={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                        Redirecting...
                      </>
                    ) : (
                      <>
                        {ctaText}
                        <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" aria-hidden="true" />
                      </>
                    )}
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
