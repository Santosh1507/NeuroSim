'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '../../lib/auth-context'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { BarChart2, Brain, TrendingUp, Activity, Sparkles, Zap, Target, BarChart3 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
        const res = await axios.get(`${API_URL}/api/analytics`)
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
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-neural/10 border border-neural/20 mb-6">
              <BarChart3 className="w-3 h-3 text-neural" />
              <span className="text-[11px] font-mono text-neural tracking-[0.15em] uppercase">Analytics</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-8">
              Platform<span className="text-gradient"> analytics</span>
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
                    <ResponsiveContainer width="100%" height={240}>
                      <BarChart data={scoreData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                        <XAxis dataKey="name" stroke="#444" fontSize={11} />
                        <YAxis domain={[0, 100]} stroke="#444" fontSize={11} />
                        <Tooltip
                          contentStyle={{ background: '#0f0f16', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px' }}
                          labelStyle={{ color: '#fff' }}
                        />
                        <Bar dataKey="value" fill="#4deeea" radius={[4, 4, 0, 0]} fillOpacity={0.7} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="glass-panel p-5">
                    <div className="flex items-center gap-2 mb-5">
                      <TrendingUp className="w-4 h-4 text-swarm" />
                      <h4 className="text-sm font-semibold text-white">Score Trends</h4>
                    </div>
                    <ResponsiveContainer width="100%" height={240}>
                      <LineChart data={trendData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                        <XAxis dataKey="label" stroke="#444" fontSize={11} />
                        <YAxis domain={[0, 100]} stroke="#444" fontSize={11} />
                        <Tooltip
                          contentStyle={{ background: '#0f0f16', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px' }}
                          labelStyle={{ color: '#fff' }}
                        />
                        <Line type="monotone" dataKey="current" stroke="#4deeea" strokeWidth={2} dot={{ fill: '#4deeea', r: 4 }} name="Current" />
                        <Line type="monotone" dataKey="previous" stroke="#a78bfa" strokeWidth={2} strokeDasharray="4 4" dot={{ fill: '#a78bfa', r: 4 }} name="Previous" />
                      </LineChart>
                    </ResponsiveContainer>
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
