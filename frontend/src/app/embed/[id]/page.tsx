'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { Brain, AlertTriangle } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function EmbedPage() {
  const params = useParams()
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    if (!params.id) return
    const fetchShare = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/share/${params.id}`)
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
      <div className="bg-transparent min-h-[200px] flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-neural border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (notFound || !analysis) {
    return (
      <div className="bg-neural neural-grid min-h-[300px] flex items-center justify-center p-6">
        <div className="text-center">
          <div className="w-12 h-12 rounded-2xl bg-amber-400/10 border border-amber-400/20 flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-6 h-6 text-amber-400" />
          </div>
          <p className="text-sm text-gray-400">Analysis not found or has expired.</p>
        </div>
      </div>
    )
  }

  const scores = [
    { label: 'Hook', value: analysis.hook_score || 0, color: 'text-neural' },
    { label: 'Authenticity', value: analysis.authenticity_score || 0, color: 'text-swarm' },
    { label: 'Viral', value: analysis.viral_potential || 0, color: 'text-blue-400' },
    { label: 'Success', value: analysis.success_probability || 0, color: 'text-green-400' },
  ]

  return (
    <div className="bg-neural neural-grid min-h-[400px] w-full max-w-[400px] mx-auto">
      <div className="p-5">
        <div className="space-y-3">
          {scores.map((s) => (
            <div key={s.label}>
              <div className="flex justify-between text-xs mb-1">
                <span className="mono text-text-tertiary uppercase tracking-wider">{s.label}</span>
                <span className={`mono font-bold ${s.color}`}>{s.value}%</span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{ width: `${s.value}%`, background: s.color === 'text-neural' ? '#4deeea' : s.color === 'text-swarm' ? '#a78bfa' : s.color === 'text-blue-400' ? '#60a5fa' : '#4ade80' }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-4 border-t border-white/[0.06] text-center">
          <Link href="/" className="inline-flex items-center gap-1.5 text-[10px] mono text-text-tertiary hover:text-neural transition-colors">
            <Brain className="w-3 h-3" />
            Powered by NeuroSim
          </Link>
        </div>
      </div>
    </div>
  )
}
