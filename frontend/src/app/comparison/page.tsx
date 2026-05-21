'use client'

import { useState, useEffect, Suspense } from 'react'
import { useAuth } from '../../lib/auth-context'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { fadeIn } from '../../lib/easing'
import { BarChart3, TrendingUp, ArrowUp, ArrowDown, Minus, Brain, Target, Zap, Activity, type LucideIcon } from 'lucide-react'
import dynamic from 'next/dynamic'

const ComparisonBarChart = dynamic(() => import('../components/charts/ComparisonCharts').then(m => ({ default: m.ComparisonBarChart })), { ssr: false })
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

function ComparisonContent() {
  const { isSignedIn, isLoaded } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [video, setVideo] = useState<any>(null)
  const [videoId, setVideoId] = useState('')
  const [loading, setLoading] = useState(false)
  const [comparison, setComparison] = useState<any>(null)
  const [cohort, setCohort] = useState('all')
  const [cohorts, setCohorts] = useState<any[]>([])

  useEffect(() => {
    if (isLoaded && !isSignedIn) router.push('/')
  }, [isLoaded, isSignedIn, router])

  useEffect(() => {
    axios.get(`${API_URL}/api/v1/benchmarks`).then(r => setCohorts(r.data.cohorts))
  }, [])

  useEffect(() => {
    const id = searchParams.get('id')
    if (id) {
      setVideoId(id)
      handleCompare(id, cohort)
    }
  }, [searchParams])

  const handleCompare = async (id: string, selectedCohort: string) => {
    setLoading(true)
    try {
      const [analysisRes, compareRes] = await Promise.all([
        axios.get(`${API_URL}/analyses/${id}`),
        axios.post(`${API_URL}/api/v1/benchmarks/compare`, { video_id: id, cohort: selectedCohort }),
      ])
      setVideo(analysisRes.data)
      setComparison(compareRes.data)
    } catch (err) {
      console.error('Comparison failed:', err)
    } finally {
      setLoading(false)
    }
  }

  if (!isLoaded || !isSignedIn) return null

  const metrics: { label: string; key: string; icon: LucideIcon; invert?: boolean }[] = [
    { label: 'Success Probability', key: 'success_probability', icon: Target },
    { label: 'Hook Score', key: 'hook_score', icon: Activity },
    { label: 'Authenticity', key: 'authenticity_score', icon: Brain },
    { label: 'Viral Potential', key: 'viral_potential', icon: Zap },
    { label: 'Risk Score', key: 'risk_score', icon: TrendingUp, invert: true },
  ]

  const chartData = comparison
    ? metrics.map(m => ({
        name: m.label.split(' ')[0],
        Yours: comparison.comparison[m.key]?.user_value ?? 0,
        Average: comparison.comparison[m.key]?.benchmark_mean ?? 0,
      }))
    : []

  return (
    <div className="min-h-screen bg-neural neural-grid">
      <div className="relative z-10">
        <section className="max-w-4xl mx-auto px-6 py-12">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={fadeIn}>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-neural/10 border border-neural/20 mb-6">
              <BarChart3 className="w-3 h-3 text-neural" />
              <span className="text-[11px] font-mono text-neural tracking-[0.15em] uppercase">Benchmark</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">
              How does your content <span className="text-gradient">compare</span>?
            </h1>
            <p className="text-text-secondary text-sm mb-8">
              Compare your analysis against {comparison?.cohort_n?.toLocaleString() || '43,751'} creators from the FineVideo dataset.
            </p>

            <div className="glass-panel p-5 mb-8">
              <div className="flex flex-col sm:flex-row gap-3 items-end">
                <div className="flex-1">
                  <label className="text-[10px] mono text-text-tertiary mb-1 block">Video ID</label>
                  <input
                    type="text"
                    value={videoId}
                    onChange={e => setVideoId(e.target.value)}
                    placeholder="Enter video ID"
                    className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/40"
                  />
                </div>
                <div className="w-48">
                  <label className="text-[10px] mono text-text-tertiary mb-1 block">Cohort</label>
                  <select
                    value={cohort}
                    onChange={e => setCohort(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white focus:outline-none focus:border-neural/40"
                  >
                    {cohorts.map(c => (
                      <option key={c.key} value={c.key} className="bg-[#0f0f16]">
                        {c.label} ({c.n.toLocaleString()})
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={() => handleCompare(videoId, cohort)}
                  disabled={loading || !videoId}
                  className="btn-neural text-sm px-6 py-2 disabled:opacity-50"
                >
                  {loading ? 'Loading...' : 'Compare'}
                </button>
              </div>
            </div>

            {comparison && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-8">
                  {metrics.map(m => {
                    const data = comparison.comparison[m.key]
                    if (!data) return null
                    const delta = data.delta
                    const Icon = m.icon
                    return (
                      <div key={m.label} className="glass-panel p-4">
                        <div className="flex items-center gap-1.5 mb-2">
                          <Icon className="w-3.5 h-3.5 text-neural" />
                          <span className="text-[10px] mono text-text-tertiary">{m.label}</span>
                        </div>
                        <div className="flex items-end justify-between">
                          <div>
                            <p className="text-lg font-bold mono text-neural">{data.user_value.toFixed(1)}</p>
                            <p className="text-[10px] text-text-tertiary">yours</p>
                          </div>
                          <div className="text-right">
                            <div className="flex items-center gap-1 justify-end">
                              {delta > 0 ? <ArrowUp className="w-3 h-3 text-green-400" /> : delta < 0 ? <ArrowDown className="w-3 h-3 text-red-400" /> : <Minus className="w-3 h-3 text-text-tertiary" />}
                              <span className={`text-xs mono ${delta > 0 ? 'text-green-400' : delta < 0 ? 'text-red-400' : 'text-text-tertiary'}`}>
                                {delta > 0 ? '+' : ''}{delta.toFixed(1)}
                              </span>
                            </div>
                            <p className="text-[10px] text-text-tertiary">P{data.percentile}</p>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>

                <div className="glass-panel p-5 mb-8">
                  <h3 className="text-sm font-semibold text-white mb-4">Your Score vs Average</h3>
                  <ComparisonBarChart data={chartData} />
                </div>

                <div className="glass-panel p-5 border-neural/20">
                  <h3 className="text-sm font-semibold text-white mb-3">Cohort: {comparison.cohort}</h3>
                  <p className="text-xs text-text-tertiary">
                    Based on {comparison.cohort_n.toLocaleString()} videos from the FineVideo dataset.
                    Percentiles estimated from cohort quartile distributions.
                  </p>
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
    <Suspense fallback={<div className="min-h-screen bg-neural flex items-center justify-center"><div className="w-6 h-6 border-2 border-neural border-t-transparent rounded-full animate-spin" /></div>}>
      <ComparisonContent />
    </Suspense>
  )
}
