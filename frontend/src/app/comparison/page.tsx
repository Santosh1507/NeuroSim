'use client'

import { useState, useEffect, Suspense } from 'react'
import { useAuth } from '../../lib/auth-context'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { BarChart3, TrendingUp, ArrowUp, ArrowDown, Minus, Brain, Target, Zap, Activity, type LucideIcon } from 'lucide-react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function ComparisonContent() {
  const { isSignedIn, isLoaded } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [videoA, setVideoA] = useState<any>(null)
  const [videoB, setVideoB] = useState<any>(null)
  const [idA, setIdA] = useState('')
  const [idB, setIdB] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isLoaded && !isSignedIn) router.push('/')
  }, [isLoaded, isSignedIn, router])

  useEffect(() => {
    const a = searchParams.get('a')
    const b = searchParams.get('b')
    if (a && b) {
      setIdA(a)
      setIdB(b)
      handleCompareWithIds(a, b)
    }
  }, [searchParams])

  const fetchAnalysis = async (videoId: string) => {
    const res = await axios.get(`${API_URL}/analyses/${videoId}`)
    return res.data
  }

  const handleCompareWithIds = async (a: string, b: string) => {
    setLoading(true)
    try {
      const [va, vb] = await Promise.all([fetchAnalysis(a), fetchAnalysis(b)])
      setVideoA(va)
      setVideoB(vb)
    } catch (err) {
      console.error('Comparison failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCompare = async () => {
    if (!idA || !idB) return
    handleCompareWithIds(idA, idB)
  }

  if (!isLoaded || !isSignedIn) return null

  const metrics: { label: string; key: string; icon: LucideIcon; path?: string }[] = [
    { label: 'Success Probability', key: 'success_probability', icon: Target },
    { label: 'Hook Score', key: 'hook_score', icon: Activity },
    { label: 'Authenticity', key: 'authenticity_score', icon: Brain },
    { label: 'Viral Potential', key: 'viral_potential', icon: Zap },
    { label: 'Risk Score', key: 'risk_score', icon: TrendingUp },
    { label: 'CTA Activation', key: 'cta_activation_score', path: 'cta_analysis.cta_activation_score', icon: Target },
  ]

  const getVal = (analysis: any, key: string, path?: string) => {
    if (path) {
      const parts = path.split('.')
      let obj = analysis
      for (const p of parts) { if (obj) obj = obj[p] }
      return obj ?? 0
    }
    return analysis?.[key] ?? 0
  }

  const chartData = metrics.map(m => ({
    name: m.label.split(' ')[0],
    A: getVal(videoA, m.key, m.path),
    B: getVal(videoB, m.key, m.path),
  }))

  return (
    <div className="min-h-screen bg-neural neural-grid">
      <div className="relative z-10">
        <section className="max-w-6xl mx-auto px-6 py-12">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-neural/10 border border-neural/20 mb-6">
              <BarChart3 className="w-3 h-3 text-neural" />
              <span className="text-[11px] font-mono text-neural tracking-[0.15em] uppercase">Comparison</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-8">
              Compare<span className="text-gradient"> analyses</span>
            </h1>

            <div className="glass-panel p-5 mb-8">
              <div className="flex flex-col sm:flex-row gap-3 items-end">
                <div className="flex-1">
                  <label className="text-[10px] mono text-text-tertiary mb-1 block">Video A ID</label>
                  <input
                    type="text"
                    value={idA}
                    onChange={e => setIdA(e.target.value)}
                    placeholder="Enter video ID"
                    className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/40"
                  />
                </div>
                <div className="flex-1">
                  <label className="text-[10px] mono text-text-tertiary mb-1 block">Video B ID</label>
                  <input
                    type="text"
                    value={idB}
                    onChange={e => setIdB(e.target.value)}
                    placeholder="Enter video ID"
                    className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/40"
                  />
                </div>
                <button
                  onClick={handleCompare}
                  disabled={loading || !idA || !idB}
                  className="btn-neural text-sm px-6 py-2 disabled:opacity-50"
                >
                  {loading ? 'Loading...' : 'Compare'}
                </button>
              </div>
            </div>

            {videoA && videoB && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-8">
                  {metrics.map(m => {
                    const valA = getVal(videoA, m.key, m.path)
                    const valB = getVal(videoB, m.key, m.path)
                    const delta = valA - valB
                    const Icon = m.icon
                    return (
                      <div key={m.label} className="glass-panel p-4">
                        <div className="flex items-center gap-1.5 mb-2">
                          <Icon className="w-3.5 h-3.5 text-neural" />
                          <span className="text-[10px] mono text-text-tertiary">{m.label}</span>
                        </div>
                        <div className="flex items-end justify-between">
                          <div>
                            <p className="text-lg font-bold mono text-neural">{valA}%</p>
                            <p className="text-xs text-text-tertiary">A</p>
                          </div>
                          <div className="flex items-center gap-1">
                            {delta > 0 ? <ArrowUp className="w-3 h-3 text-green-400" /> : delta < 0 ? <ArrowDown className="w-3 h-3 text-red-400" /> : <Minus className="w-3 h-3 text-text-tertiary" />}
                            <span className={`text-xs mono ${delta > 0 ? 'text-green-400' : delta < 0 ? 'text-red-400' : 'text-text-tertiary'}`}>
                              {delta > 0 ? '+' : ''}{delta.toFixed(1)}
                            </span>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold mono text-swarm">{valB}%</p>
                            <p className="text-xs text-text-tertiary">B</p>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>

                <div className="glass-panel p-5">
                  <h4 className="text-sm font-semibold text-white mb-4">Score Comparison</h4>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                      <XAxis dataKey="name" stroke="#444" fontSize={11} />
                      <YAxis domain={[0, 100]} stroke="#444" fontSize={11} />
                      <Tooltip
                        contentStyle={{ background: '#0f0f16', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px' }}
                        labelStyle={{ color: '#fff' }}
                      />
                      <Bar dataKey="A" fill="#4deeea" radius={[4, 4, 0, 0]} fillOpacity={0.7} />
                      <Bar dataKey="B" fill="#a78bfa" radius={[4, 4, 0, 0]} fillOpacity={0.7} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </>
            )}
          </motion.div>
        </section>
      </div>
    </div>
  )
}

export default function ComparisonPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-neural neural-grid flex items-center justify-center"><div className="w-8 h-8 border-2 border-neural border-t-transparent rounded-full animate-spin" /></div>}>
      <ComparisonContent />
    </Suspense>
  )
}
