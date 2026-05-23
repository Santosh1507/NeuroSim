'use client'

import { useState, useEffect, useRef } from 'react'
import { X, Sparkles, Check, ArrowRight, Loader2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { fadeIn } from '../../lib/easing'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

interface UpgradeModalProps {
  open: boolean
  onClose: () => void
}

export function UpgradeModal({ open, onClose }: UpgradeModalProps) {
  const [loading, setLoading] = useState(false)
  const [stripePriceId, setStripePriceId] = useState<string | null>(null)
  const dialogRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    fetch(`${API_URL}/api/v1/premium/status`)
      .then(r => r.json())
      .then(data => {
        setStripePriceId(data.stripe_price_id_monthly)
      })
      .catch(() => {})

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key !== 'Tab' || !dialogRef.current) return
      const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      if (focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus() }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first.focus() }
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    const originalOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = originalOverflow
    }
  }, [open, onClose])

  const handleUpgrade = async () => {
    if (!stripePriceId) return
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/v1/stripe/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          price_id: stripePriceId,
          success_url: window.location.origin + '/dashboard',
          cancel_url: window.location.origin + '/pricing',
        }),
      })
      if (!res.ok) throw new Error('Checkout failed')
      const data = await res.json()
      if (data.url) window.location.href = data.url
    } catch {
      window.location.href = '/pricing'
    } finally {
      setLoading(false)
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={fadeIn}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />
          <div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label="Upgrade to Pro"
            className="relative w-full max-w-md rounded-2xl bg-[#0a0a0f] border border-white/[0.08] p-8 shadow-2xl"
          >
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-500 hover:text-white hover:bg-white/[0.06] transition-colors"
              aria-label="Close modal"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-neural/10 border border-neural/20 mb-4">
              <Sparkles className="w-3 h-3 text-neural" />
              <span className="text-[10px] font-mono text-neural tracking-[0.15em] uppercase">Pro</span>
            </div>

            <h2 className="text-xl font-bold text-white mb-2">Upgrade to Pro</h2>
            <p className="text-sm text-gray-400 mb-6">Unlock unlimited analyses, PDF exports, and priority features.</p>

            <ul className="space-y-3 mb-6">
              {[
                'Unlimited analyses per month',
                'PDF report exports',
                'LLM-enhanced content analysis',
                'Priority swarm simulation',
                'Custom ROI thresholds',
              ].map(feat => (
                <li key={feat} className="flex items-start gap-3 text-sm text-gray-400">
                  <Check className="w-4 h-4 text-swarm mt-0.5 flex-shrink-0" />
                  {feat}
                </li>
              ))}
            </ul>

            <div className="flex items-baseline gap-1 mb-6">
              <span className="text-3xl font-bold text-white font-mono tracking-tight">$29</span>
              <span className="text-sm text-gray-500 font-mono">/month</span>
            </div>

            <button
              onClick={handleUpgrade}
              disabled={loading || !stripePriceId}
              className={`w-full py-3 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                loading || !stripePriceId
                  ? 'bg-neural/5 border border-neural/15 text-neural/60 cursor-not-allowed'
                  : 'bg-neural/10 border border-neural/25 text-neural hover:bg-neural/20 cursor-pointer'
              }`}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  Redirecting...
                </>
              ) : (
                <>
                  Upgrade to Pro
                  <ArrowRight className="w-4 h-4" aria-hidden="true" />
                </>
              )}
            </button>

            <p className="text-xs text-gray-600 text-center mt-4">
              You can cancel anytime. No long-term commitment.
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
