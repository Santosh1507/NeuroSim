'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { heroReveal, fadeIn } from '../../lib/easing'
import { Mail, CheckCircle, ArrowRight, Brain, Sparkles } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export default function WaitlistPage() {
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [queuePos, setQueuePos] = useState(0)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await axios.post(`${API_URL}/waitlist`, { email, name: name || undefined })
      setQueuePos(res.data.queue_position)
      setSuccess(true)
    } catch (err: any) {
      if (err.response?.status === 409) {
        setError(err.response.data.detail || 'Already on the waitlist!')
      } else {
        setError('Something went wrong. Try again later.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-neural neural-grid min-h-screen">
      <div className="relative z-10">
        <section className="max-w-lg mx-auto px-6 pt-24 pb-32 md:pt-32 md:pb-40">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={heroReveal}
            className="text-center"
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-neural/10 border border-neural/20 mb-6">
              <Sparkles className="w-3 h-3 text-neural" />
              <span className="text-[11px] font-mono text-neural tracking-[0.15em] uppercase">Waitlist</span>
            </div>

            {success ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={fadeIn}
              >
                <div className="w-16 h-16 rounded-2xl bg-neural/10 border border-neural/20 flex items-center justify-center mx-auto mb-6">
                  <CheckCircle className="w-8 h-8 text-neural" />
                </div>
                <h1 className="text-3xl font-bold text-white mb-2">You&apos;re on the list!</h1>
                <p className="text-gray-400 mb-4">
                  You&apos;re #{queuePos} in line. We&apos;ll notify you when Premium launches.
                </p>
                <div className="glass-panel p-6">
                  <p className="text-sm text-text-tertiary mb-2">Also track us on</p>
                  <div className="flex items-center justify-center gap-3">
                    <span className="text-xs mono text-neural">X / GitHub</span>
                    <span className="w-px h-3 bg-white/10" />
                    <Brain className="w-4 h-4 text-neural/60" />
                    <span className="text-xs text-text-tertiary">NeuroSim v2</span>
                  </div>
                </div>
              </motion.div>
            ) : (
              <>
                <h1 className="text-[clamp(1.8rem,4vw,2.8rem)] font-bold text-white leading-[1.02] tracking-[-0.03em] mb-3">
                  Join the <span className="text-gradient">waitlist</span>
                </h1>
                <p className="text-gray-400 mb-10">
                  Premium unlocks real GPU processing, unlimited analyses, and API access.
                </p>

                <form onSubmit={handleSubmit} className="glass-panel p-6 text-left">
                  <div className="space-y-4">
                    <div>
                      <label className="text-xs text-text-tertiary mb-1 block">Name <span className="text-text-quaternary">(optional)</span></label>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Your name"
                        className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/40"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-text-tertiary mb-1 block">Email</label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
                        <input
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="you@example.com"
                          required
                          className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/40"
                        />
                      </div>
                    </div>

                    {error && (
                      <p className="text-xs text-amber-400 bg-amber-400/10 border border-amber-400/20 rounded-lg px-3 py-2">{error}</p>
                    )}

                    <button
                      type="submit"
                      disabled={loading}
                      className="group w-full py-2.5 rounded-lg bg-neural/15 border border-neural/30 text-sm font-medium text-white hover:bg-neural/25 transition-colors disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
                    >
                      {loading ? 'Joining...' : 'Join Waitlist'}
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                    </button>
                  </div>
                </form>
              </>
            )}
          </motion.div>
        </section>
      </div>
    </div>
  )
}
