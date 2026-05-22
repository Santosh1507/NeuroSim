'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { easeOutExpo } from '../../../lib/easing'
import { Brain, AlertTriangle, ArrowRight, BarChart3, MessageSquare, Target, Sparkles } from 'lucide-react'
import dynamic from 'next/dynamic'

const SharedRadarChart = dynamic(() => import('../../components/charts/SharedAnalysisCharts').then(m => ({ default: m.SharedRadarChart })), { ssr: false })
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export default function SharedAnalysisPage() {
  const params = useParams()
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    if (!params.id) return
    const fetchShare = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/v1/share/${params.id}`)
        setAnalysis(res.data.analysis)
      } catch {
        setNotFound(true)
      } finally {
        setLoading(false)
      }
    }
    fetchShare()
  }, [params.id])

  if (loading) {
    return (
      <div className="bg-neural neural-grid min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-neural border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (notFound || !analysis) {
    return (
      <div className="bg-neural neural-grid min-h-screen">
        <div className="relative z-10 max-w-lg mx-auto px-6 pt-32 text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: easeOutExpo }}
          >
            <div className="w-16 h-16 rounded-2xl bg-amber-400/10 border border-amber-400/20 flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="w-8 h-8 text-amber-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Analysis not found</h1>
            <p className="text-gray-400 mb-8">This share link doesn&apos;t exist or has expired.</p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-neural/10 border border-neural/25 text-neural font-semibold text-sm hover:bg-neural/20 transition-all"
            >
              <Brain className="w-4 h-4" /> Analyze your own content
            </Link>
          </motion.div>
        </div>
      </div>
    )
  }

  const radarData = [
    { subject: 'Hook', value: analysis.hook_score || 0, fullMark: 100 },
    { subject: 'Authenticity', value: analysis.authenticity_score || 0, fullMark: 100 },
    { subject: 'Viral', value: analysis.viral_potential || 0, fullMark: 100 },
    { subject: 'CTA', value: analysis.cta_analysis?.cta_activation_score || 0, fullMark: 100 },
    { subject: 'Share', value: analysis.sentiment_forecast?.shareability_index || 0, fullMark: 100 },
  ]

  return (
    <div className="bg-neural neural-grid min-h-screen">
      <div className="relative z-10">
        <section className="max-w-4xl mx-auto px-6 py-12">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: easeOutExpo }}
          >
            <div className="flex items-center justify-between mb-10">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-neural/10 border border-neural/20 flex items-center justify-center">
                  <Brain className="w-4 h-4 text-neural" />
                </div>
                <span className="text-sm font-semibold text-white">NeuroSim</span>
                <span className="text-[10px] mono text-text-tertiary">v3.0</span>
              </div>
              <div className="flex items-center gap-2 text-[10px] mono text-text-tertiary">
                <span className="status-dot status-neural" />
                Shared Analysis
                <span className={`text-[9px] ${analysis.analysis_response?.mode === 'real' ? 'text-neural border-neural/30' : 'text-amber-400/70 border-amber-400/20'} border px-1.5 py-0.5 rounded`}>
                  {analysis.analysis_response?.mode === 'real' ? 'REAL' : 'SIMULATED'}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
              {[
                { label: 'Success', value: analysis.success_probability, accent: 'text-neural' },
                { label: 'Risk', value: analysis.risk_score, accent: 'text-orange-400' },
                { label: 'Viral', value: analysis.viral_potential, accent: 'text-swarm' },
                { label: 'Hook', value: analysis.hook_score, accent: 'text-neural' },
              ].map((m) => (
                <div key={m.label} className="glass-panel p-4">
                  <p className="text-[10px] mono text-text-tertiary uppercase tracking-wider mb-2">{m.label}</p>
                  <p className={`text-2xl font-bold mono ${m.accent}`}>{m.value}%</p>
                </div>
              ))}
            </div>

            <div className="grid md:grid-cols-2 gap-4 mb-8">
              <div className="glass-panel p-5">
                <div className="flex items-center gap-2 mb-5">
                  <Brain className="w-4 h-4 text-neural" />
                  <h4 className="text-sm font-semibold text-white">Content Analysis</h4>
                </div>
                <SharedRadarChart data={radarData} />
              </div>

              <div className="glass-panel p-5">
                <div className="flex items-center gap-2 mb-5">
                  <MessageSquare className="w-4 h-4 text-swarm" />
                  <h4 className="text-sm font-semibold text-white">Sentiment</h4>
                </div>
                <div className="space-y-4">
                  {[
                    { label: 'Positive', value: analysis.sentiment_forecast?.positive_sentiment_pct || 0, color: 'progress-green' },
                    { label: 'Neutral', value: analysis.sentiment_forecast?.neutral_sentiment_pct || 0, color: 'progress-track' },
                    { label: 'Negative', value: analysis.sentiment_forecast?.negative_sentiment_pct || 0, color: 'progress-red' },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="text-text-tertiary">{item.label}</span>
                        <span className="text-white mono">{item.value.toFixed(1)}%</span>
                      </div>
                      <div className="progress-track">
                        <div className={`progress-fill ${item.color}`} style={{ width: `${item.value}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="glass-panel p-5 mb-8">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-4 h-4 text-neural" />
                <h4 className="text-sm font-semibold text-white">Recommendations</h4>
              </div>
              <div className="space-y-2">
                {analysis.recommendations?.map((rec: string, i: number) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                    <div className="w-1.5 h-1.5 rounded-full bg-neural mt-2 flex-shrink-0" />
                    <span className="text-sm text-text-secondary">{rec}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-panel-elevated p-8 text-center">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-neural/10 border border-neural/15 mb-4">
                <Sparkles className="w-3 h-3 text-neural" />
                <span className="text-[10px] font-mono text-neural/60 tracking-[0.15em] uppercase">Powered by NeuroSim</span>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Predict your content&apos;s performance</h3>
              <p className="text-sm text-gray-400 mb-6">Upload a video and get neural + social predictions in seconds.</p>
              <Link
                href="/"
                className="group inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-neural/10 border border-neural/25 text-neural font-semibold text-sm hover:bg-neural/20 transition-all"
              >
                Analyze your own content <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
          </motion.div>
        </section>
      </div>
    </div>
  )
}
