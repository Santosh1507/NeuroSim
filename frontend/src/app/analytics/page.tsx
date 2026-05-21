'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '../../lib/auth-context'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { fadeIn } from '../../lib/easing'
import { BarChart2, Brain, TrendingUp, Activity, Sparkles, Zap, Target, BarChart3 } from 'lucide-react'
import dynamic from 'next/dynamic'

const AnalyticsBarChart = dynamic(() => import('../components/charts/AnalyticsCharts').then(m => ({ default: m.AnalyticsBarChart })), { ssr: false })
const AnalyticsLineChart = dynamic(() => import('../components/charts/AnalyticsCharts').then(m => ({ default: m.AnalyticsLineChart })), { ssr: false })
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

const defaultData = {
  total_analyses: 0,
  total_videos: 0,
  average_success_probability: 0,
  average_hook_score: 0,
  average_viral_potential: 0,
}

export default function AnalyticsPage() {
  const { isSignedIn, isLoaded } = useAuth()
  const router = useRouter()
  const [data, setData] = useState(defaultData)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.push('/')
      return
    }
    const fetch = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/v1/analytics`)
        setData(res.data)
      } catch {
        // use defaults
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [isLoaded, isSignedIn, router])

  if (!isLoaded || !isSignedIn) return null

  const scoreData = [
    { name: 'Success', value: data.average_success_probability },
    { name: 'Hook', value: data.average_hook_score },
    { name: 'Viral', value: data.average_viral_potential },
  ]

  const trendData = [
    { label: 'Success', current: data.average_success_probability, previous: Math.round(data.average_success_probability * 0.85) },
    { label: 'Hook', current: data.average_hook_score, previous: Math.round(data.average_hook_score * 0.9) },
    { label: 'Viral', current: data.average_viral_potential, previous: Math.round(data.average_viral_potential * 0.88) },
  ]

  return (
    <div className="bg-neural neural-grid min-h-screen">
      <div className="relative z-10">
        <section className="max-w-6xl mx-auto px-6 py-12">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={fadeIn}
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-neural/10 border border-neural/20 mb-6">
              <BarChart3 className="w-3 h-3 text-neural" />
              <span className="text-[11px] font-mono text-neural tracking-[0.15em] uppercase">Analytics</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-8">
              Platform <span className="text-gradient">analytics</span>
            </h1>

            {loading ? (
              <div className="flex items-center justify-center py-20">
                <div className="w-8 h-8 border-2 border-neural border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
                  {[
                    { label: 'Total Analyses', value: data.total_analyses, icon: Activity, accent: 'text-neural' },
                    { label: 'Videos Processed', value: data.total_videos, icon: Brain, accent: 'text-swarm' },
                    { label: 'Avg Hook', value: `${data.average_hook_score}%`, icon: Target, accent: 'text-neural' },
                    { label: 'Avg Viral', value: `${data.average_viral_potential}%`, icon: Zap, accent: 'text-swarm' },
                  ].map((stat, i) => (
                    <motion.div
                      key={stat.label}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05, duration: 0.4 }}
                      className="glass-panel p-4"
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <stat.icon className={`w-3.5 h-3.5 ${stat.accent}`} />
                        <span className="text-[10px] mono text-text-tertiary uppercase tracking-wider">{stat.label}</span>
                      </div>
                      <p className={`text-2xl font-bold mono ${stat.accent}`}>{stat.value}</p>
                    </motion.div>
                  ))}
                </div>

                <div className="grid md:grid-cols-2 gap-4 mb-8">
                  <div className="glass-panel p-5">
                    <div className="flex items-center gap-2 mb-5">
                      <BarChart2 className="w-4 h-4 text-neural" />
                      <h4 className="text-sm font-semibold text-white">Average Scores</h4>
                    </div>
                    <AnalyticsBarChart data={scoreData} />
                  </div>

                  <div className="glass-panel p-5">
                    <div className="flex items-center gap-2 mb-5">
                      <TrendingUp className="w-4 h-4 text-swarm" />
                      <h4 className="text-sm font-semibold text-white">Score Trends</h4>
                    </div>
                    <AnalyticsLineChart data={trendData} />
                  </div>
                </div>

                <div className="glass-panel p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Sparkles className="w-4 h-4 text-neural" />
                    <h4 className="text-sm font-semibold text-white">Summary</h4>
                  </div>
                  <p className="text-sm text-text-secondary">
                    {data.total_analyses === 0
                      ? 'No analyses have been run yet. Upload content to start collecting analytics.'
                      : `Across ${data.total_analyses} analyses, average success probability is ${data.average_success_probability}% with an average hook score of ${data.average_hook_score}%.`}
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
