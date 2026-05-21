'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Target, TrendingUp, Users, Brain, AlertTriangle, CheckCircle, Activity, BarChart2, Zap, Shield } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

interface ValidationStudyData {
  progress: {
    total_entries: number
    unique_users: number
    target_entries: number
    completion_pct: number
    by_type: { video: number; script: number }
  }
  correlations: {
    status: string
    message?: string
    n_samples?: number
    correlations?: Record<string, {
      vs_views: { pearson_r: number; p_value: number; significant: boolean }
      vs_engagement: { pearson_r: number; p_value: number; significant: boolean }
    }>
  }
  accuracy: {
    status: string
    n_samples?: number
    directional_accuracy?: {
      overall: number
      vs_views: number
      vs_engagement: number
    }
    mean_absolute_error?: {
      vs_views: number
      vs_engagement: number
    }
  }
  benchmarks: {
    status: string
    cohort_averages?: Record<string, number>
  }
}

export function ValidationStudyPanel({ refreshTrigger = 0 }: { refreshTrigger?: number }) {
  const [data, setData] = useState<ValidationStudyData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStudyData()
  }, [refreshTrigger])

  const fetchStudyData = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}/api/v1/validation/study`, { signal: AbortSignal.timeout(5000) })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setData(json)
    } catch (err: any) {
      setError(err.message || 'Failed to load study data')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !data) {
    return (
      <div className="glass-panel p-4">
        <div className="flex items-center gap-2 mb-3">
          <Activity className="w-4 h-4 text-neural animate-pulse" />
          <h4 className="text-[10px] mono text-text-tertiary uppercase tracking-wider">Validation Study</h4>
        </div>
        <div className="flex items-center justify-center py-4">
          <div className="w-5 h-5 border-2 border-neural border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass-panel p-4 border border-orange-400/20">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="w-4 h-4 text-orange-400" />
          <h4 className="text-[10px] mono text-text-tertiary uppercase tracking-wider">Validation Study</h4>
        </div>
        <p className="text-[10px] text-text-tertiary">{error}</p>
        <button onClick={fetchStudyData} className="text-[10px] text-neural hover:underline mt-1">Retry</button>
      </div>
    )
  }

  if (!data) return null

  const { progress, correlations, accuracy, benchmarks } = data
  const hasCorrelations = correlations?.status === 'computed' && correlations?.correlations
  const hasAccuracy = accuracy?.status === 'computed' && accuracy?.directional_accuracy

  return (
    <div className="glass-panel p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-neural" />
          <h4 className="text-[10px] mono text-text-tertiary uppercase tracking-wider">Validation Study</h4>
        </div>
        <button onClick={fetchStudyData} className="text-[9px] mono text-text-tertiary hover:text-neural transition-colors" aria-label="Refresh study data">
          ↻
        </button>
      </div>

      {/* Prediction Accuracy — prominent display */}
      {hasAccuracy && (
        <div className="mb-3 p-3 rounded-xl bg-gradient-to-br from-neural/5 via-swarm/[0.02] to-neural/5 border border-neural/10">
          <div className="flex items-center gap-1.5 mb-2">
            <Shield className="w-3 h-3 text-neural" />
            <span className="text-[9px] mono text-neural uppercase tracking-wider font-semibold">Prediction Accuracy</span>
          </div>
          <div className="flex items-end gap-3 mb-2">
            <div>
              <span className="text-2xl font-bold mono text-white">
                {accuracy.directional_accuracy!.overall}%
              </span>
              <span className="text-[10px] text-text-tertiary ml-1">overall</span>
            </div>
            <div className="flex gap-2 text-[10px] pb-1">
              <div className="px-2 py-0.5 rounded bg-white/[0.03]">
                <span className="text-text-tertiary">Views </span>
                <span className="mono text-neural">{accuracy.directional_accuracy!.vs_views}%</span>
              </div>
              <div className="px-2 py-0.5 rounded bg-white/[0.03]">
                <span className="text-text-tertiary">Eng. </span>
                <span className="mono text-swarm">{accuracy.directional_accuracy!.vs_engagement}%</span>
              </div>
            </div>
          </div>
          {accuracy.mean_absolute_error && (
            <div className="text-[9px] text-text-tertiary">
              <span>Avg error: </span>
              <span className="mono text-white/60">MAE views {accuracy.mean_absolute_error.vs_views}</span>
              <span className="mx-1">·</span>
              <span className="mono text-white/60">MAE eng {accuracy.mean_absolute_error.vs_engagement}</span>
            </div>
          )}
        </div>
      )}

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex justify-between text-[10px] mb-1">
          <span className="text-text-tertiary">Progress</span>
          <span className="text-white mono">{progress.total_entries}/{progress.target_entries}</span>
        </div>
        <div className="progress-track">
          <div
            className={`progress-fill ${progress.completion_pct >= 100 ? 'bg-green-400' : 'bg-neural'}`}
            style={{ width: `${Math.min(progress.completion_pct, 100)}%` }}
          />
        </div>
        <div className="flex justify-between text-[9px] text-text-tertiary mt-1">
          <span>{progress.unique_users} users</span>
          <span>{progress.by_type.video} video / {progress.by_type.script} script</span>
        </div>
      </div>

      {/* Correlations */}
      {hasCorrelations && (
        <div className="space-y-2 pt-2 border-t border-white/[0.04]">
          <div className="flex items-center gap-1.5 mb-1.5">
            <TrendingUp className="w-3 h-3 text-swarm" />
            <span className="text-[9px] mono text-text-tertiary uppercase tracking-wider">Correlations</span>
          </div>
          {Object.entries(correlations.correlations!).map(([metric, corr]) => (
            <div key={metric} className="p-2 rounded-lg bg-white/[0.02]">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-text-secondary font-medium capitalize">
                  {metric.replace(/_/g, ' ')}
                </span>
                <span className={`text-[9px] mono px-1.5 py-0.5 rounded ${
                  corr.vs_views.significant
                    ? 'bg-green-400/10 text-green-400'
                    : 'bg-white/5 text-text-tertiary'
                }`}>
                  {corr.vs_views.significant ? 'SIGNIFICANT' : 'N/A'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[9px]">
                <div>
                  <span className="text-text-tertiary">vs Views: </span>
                  <span className="mono text-white">r={corr.vs_views.pearson_r.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-text-tertiary">vs Eng: </span>
                  <span className="mono text-white">r={corr.vs_engagement.pearson_r.toFixed(2)}</span>
                </div>
              </div>
            </div>
          ))}
          <p className="text-[8px] text-text-tertiary pt-1">
            Based on {correlations.n_samples} prediction-outcome pairs
          </p>
        </div>
      )}

      {/* Benchmarks */}
      {benchmarks?.status === 'available' && benchmarks?.cohort_averages && (
        <div className="pt-2 mt-2 border-t border-white/[0.04]">
          <div className="flex items-center gap-1.5 mb-1.5">
            <Users className="w-3 h-3 text-neural" />
            <span className="text-[9px] mono text-text-tertiary uppercase tracking-wider">Cohort Benchmarks</span>
          </div>
          <div className="grid grid-cols-3 gap-1">
            {Object.entries(benchmarks.cohort_averages).map(([key, val]) => (
              <div key={key} className="p-1.5 rounded bg-white/[0.02] text-center">
                <p className="text-[9px] mono text-neural font-bold">{typeof val === 'number' ? val.toFixed(1) : val}</p>
                <p className="text-[8px] text-text-tertiary capitalize">{key.replace(/_/g, ' ')}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!hasCorrelations && correlations?.status === 'insufficient_data' && (
        <div className="flex items-center gap-2 p-2 rounded-lg bg-white/[0.02] mt-1">
          <Brain className="w-3 h-3 text-text-tertiary" />
          <p className="text-[9px] text-text-tertiary">
            {correlations.message || 'Submit validation data to see results'}
          </p>
        </div>
      )}

      {/* Target info */}
      <div className="pt-2 mt-2 border-t border-white/[0.04]">
        <div className="flex items-center gap-1.5">
          <CheckCircle className={`w-3 h-3 ${progress.completion_pct >= 100 ? 'text-green-400' : 'text-text-tertiary'}`} />
          <span className="text-[9px] text-text-tertiary">
            Target: {progress.target_entries} entries for statistical significance
          </span>
        </div>
      </div>
    </div>
  )
}
