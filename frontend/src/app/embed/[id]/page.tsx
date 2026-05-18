'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { Brain, TrendingUp, Target, Zap, Activity } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function EmbedPage() {
  const params = useParams()
  const shareId = params.id as string
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/share/${shareId}`)
        setAnalysis(res.data.analysis)
      } catch {
        setError('This analysis no longer exists or the link is invalid.')
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [shareId])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-neural border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-6">
        <div className="text-center">
          <p className="text-white font-medium mb-2">Analysis Unavailable</p>
          <p className="text-text-tertiary text-sm">{error || 'No data found.'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] p-4">
      <div className="max-w-lg mx-auto">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-4 h-4 text-neural" />
          <h1 className="text-sm font-semibold text-white">NeuroSim Analysis</h1>
          <span className="text-[9px] mono text-amber-400/70 border border-amber-400/20 px-1.5 py-0.5 rounded">SIMULATED</span>
        </div>

        <div className="grid grid-cols-2 gap-2 mb-4">
          {[
            { label: 'Success', value: analysis.success_probability, icon: Target, color: 'text-neural' },
            { label: 'Hook', value: analysis.hook_score, icon: Activity, color: 'text-neural' },
            { label: 'Viral', value: analysis.viral_potential, icon: Zap, color: 'text-swarm' },
            { label: 'Risk', value: analysis.risk_score, icon: TrendingUp, color: 'text-orange-400' },
          ].map(m => (
            <div key={m.label} className="rounded-lg bg-white/[0.03] border border-white/[0.06] p-3">
              <div className="flex items-center gap-1.5 mb-1">
                <m.icon className={`w-3 h-3 ${m.color}`} />
                <span className="text-[10px] mono text-text-tertiary">{m.label}</span>
              </div>
              <p className={`text-xl font-bold mono ${m.color}`}>{m.value}%</p>
            </div>
          ))}
        </div>

        {analysis.stage_gate && (
          <div className="rounded-lg bg-white/[0.03] border border-white/[0.06] p-3 mb-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] mono text-text-tertiary">Stage-Gate</span>
              <span className={`text-xs mono font-medium ${analysis.stage_gate.passed ? 'text-green-400' : 'text-red-400'}`}>
                {analysis.stage_gate.passed ? 'PASS' : 'FAIL'}
              </span>
            </div>
          </div>
        )}

        {analysis.recommendations && analysis.recommendations.length > 0 && (
          <div className="rounded-lg bg-white/[0.03] border border-white/[0.06] p-3">
            <p className="text-[10px] mono text-text-tertiary mb-2">Top Recommendation</p>
            <p className="text-xs text-text-secondary">{analysis.recommendations[0]}</p>
          </div>
        )}

        <p className="text-[9px] text-text-tertiary text-center mt-4 mono">Powered by NeuroSim v2.2</p>
      </div>
    </div>
  )
}
