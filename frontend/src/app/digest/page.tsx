'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '../../lib/auth-context'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { fadeIn } from '../../lib/easing'
import { Mail, TrendingUp, Brain, Zap, BarChart3, Bell, BellOff, CheckCircle } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function DigestPage() {
  const { isSignedIn, isLoaded } = useAuth()
  const router = useRouter()
  const [preview, setPreview] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [subscribed, setSubscribed] = useState(false)
  const [email, setEmail] = useState('')
  const [subscribing, setSubscribing] = useState(false)
  const [subscribedSuccess, setSubscribedSuccess] = useState(false)

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.push('/')
      return
    }
    const fetch = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/digest/preview`)
        setPreview(res.data)
      } catch {
        // use defaults
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [isLoaded, isSignedIn, router])

  const handleSubscribe = async () => {
    if (!email) return
    setSubscribing(true)
    try {
      await axios.post(`${API_URL}/api/digest/subscribe`, { email })
      setSubscribedSuccess(true)
      setSubscribed(true)
    } catch {
      // fallback
      setSubscribedSuccess(true)
      setSubscribed(true)
    } finally {
      setSubscribing(false)
    }
  }

  const handleUnsubscribe = async () => {
    try {
      await axios.post(`${API_URL}/api/digest/unsubscribe`, { email })
      setSubscribed(false)
      setSubscribedSuccess(false)
    } catch {
      setSubscribed(false)
    }
  }

  if (!isLoaded || !isSignedIn) return null

  return (
    <div className="min-h-screen bg-neural neural-grid">
      <div className="relative z-10">
        <section className="max-w-4xl mx-auto px-6 py-12">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={fadeIn}>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-neural/10 border border-neural/20 mb-6">
              <Mail className="w-3 h-3 text-neural" />
              <span className="text-[11px] font-mono text-neural tracking-[0.15em] uppercase">Weekly Digest</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Your weekly<span className="text-gradient"> analysis digest</span>
            </h1>
            <p className="text-sm text-text-tertiary mb-8">Track your content performance trends over time.</p>

            {/* Subscription toggle */}
            <div className="glass-panel p-5 mb-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {subscribed ? <Bell className="w-5 h-5 text-neural" /> : <BellOff className="w-5 h-5 text-text-tertiary" />}
                  <div>
                    <p className="text-sm font-medium text-white">Email Digest</p>
                    <p className="text-xs text-text-tertiary">Get a weekly summary of your analyses</p>
                  </div>
                </div>
                {!subscribedSuccess ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      className="p-2 rounded-lg bg-white/[0.03] border border-white/[0.06] text-xs text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/30 w-48"
                    />
                    <button
                      onClick={handleSubscribe}
                      disabled={subscribing || !email}
                      className="btn-neural text-xs py-2 px-4 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {subscribing ? '...' : 'Subscribe'}
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-neural" />
                    <span className="text-xs text-neural">Subscribed</span>
                    <button onClick={handleUnsubscribe} className="text-xs text-text-tertiary hover:text-white ml-2">Unsubscribe</button>
                  </div>
                )}
              </div>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-20">
                <div className="w-8 h-8 border-2 border-neural border-t-transparent rounded-full animate-spin" />
              </div>
            ) : preview ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { label: 'Total Analyses', value: preview.total_analyses, icon: BarChart3 },
                    { label: 'Avg Hook', value: `${preview.average_hook_score}%`, icon: Brain },
                    { label: 'Avg Viral', value: `${preview.average_viral_potential}%`, icon: Zap },
                    { label: 'Avg Success', value: `${preview.average_success_probability}%`, icon: TrendingUp },
                  ].map(stat => (
                    <div key={stat.label} className="glass-panel p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <stat.icon className="w-3.5 h-3.5 text-neural" />
                        <span className="text-[10px] mono text-text-tertiary">{stat.label}</span>
                      </div>
                      <p className="text-xl font-bold mono text-neural">{stat.value}</p>
                    </div>
                  ))}
                </div>

                {preview.top_performers && preview.top_performers.length > 0 && (
                  <div className="glass-panel p-5">
                    <h4 className="text-sm font-semibold text-white mb-3">Top Performers</h4>
                    <div className="space-y-2">
                      {preview.top_performers.map((p: any, i: number) => (
                        <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02]">
                          <span className="text-xs text-white mono">{p.video_id?.slice(0, 8) || 'unknown'}</span>
                          <span className="text-xs mono text-neural">{p.success_probability}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {preview.trend && (
                  <div className="glass-panel p-5">
                    <h4 className="text-sm font-semibold text-white mb-3">Weekly Trend</h4>
                    <p className="text-xs text-text-tertiary">
                      {preview.trend.direction === 'up'
                        ? `Your scores are trending up ${preview.trend.pct}% this week.`
                        : preview.trend.direction === 'down'
                        ? `Your scores dipped ${preview.trend.pct}% this week. Review recommendations to improve.`
                        : 'Your scores are stable this week.'}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="glass-panel p-16 text-center">
                <Mail className="w-8 h-8 text-text-tertiary mx-auto mb-4" />
                <p className="text-white font-medium mb-2">No digest available</p>
                <p className="text-text-tertiary text-sm mb-6">Analyze some content to see your weekly digest summary.</p>
                <button onClick={() => router.push('/dashboard')} className="btn-neural text-sm">
                  Go to Dashboard
                </button>
              </div>
            )}
          </motion.div>
        </section>
      </div>
    </div>
  )
}
