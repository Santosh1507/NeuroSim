'use client'

import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { fadeIn, hoverLift, tapPress } from '../../lib/easing'
import {
  Upload, Zap, TrendingUp, Activity, Brain, AlertTriangle,
  CheckCircle, Sparkles, Play, RotateCcw, ArrowLeft
} from 'lucide-react'
import dynamic from 'next/dynamic'

const PredictLineChart = dynamic(() => import('../components/charts/PredictCharts').then(m => ({ default: m.PredictLineChart })), { ssr: false })
import Link from 'next/link'

const Brain3DActivation = dynamic(() => import('../components/Brain3DActivation'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[350px] glass-panel flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-neural border-t-transparent rounded-full animate-spin" />
    </div>
  ),
})

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

const PREDICT_STAGES = [
  { key: 'uploading', label: 'Uploading clip...' },
  { key: 'transcribing', label: 'Extracting audio patterns...' },
  { key: 'vision', label: 'Analyzing visual engagement...' },
  { key: 'scoring', label: 'Computing viral potential...' },
  { key: 'merging', label: 'Merging analysis signals...' },
  { key: 'done', label: 'Analysis complete' },
]

interface PredictResult {
  video_id: string
  analysis_mode: string
  duration_seconds: number | null
  virality_score: number | null
  hook_score: number
  hook_strength: string
  hold_rate: number | null
  peak_hook_timestamp: number | null
  engagement_curve: number[] | null
  roi_scores: { A5: number; LO: number; Area45: number; TPJ: number }
  authenticity_score: number
  viral_potential: number
  success_probability: number
  stage_gate: { passed: boolean; message: string; W_attn: number }
  brain_regions: Record<string, number> | null
  recommendations: string[]
  created_at: string
}

export default function PredictPage() {
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStage, setUploadStage] = useState('')
  const [result, setResult] = useState<PredictResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [visionEnabled, setVisionEnabled] = useState<boolean | null>(null)
  const [videoPreview, setVideoPreview] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/health`, { timeout: 5000 } as any)
      .then(() => setVisionEnabled(true))
      .catch(() => setVisionEnabled(false))
  }, [])

  useEffect(() => {
    if (!file) return
    const url = URL.createObjectURL(file)
    setVideoPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const validateFile = (selectedFile: File) => {
    const isVideoType = selectedFile.type.startsWith('video/')
    const extension = selectedFile.name.split('.').pop()?.toLowerCase() || ''
    const isVideoExtension = ['mp4', 'mov', 'webm', 'avi', 'mkv', 'm4v', '3gp'].includes(extension)
    
    if (!isVideoType && !isVideoExtension) {
      setError('Invalid file type. Please upload a valid video file (MP4, MOV, WEBM, etc.).')
      setFile(null)
      return false
    }
    const maxSize = 50 * 1024 * 1024 // 50MB
    if (selectedFile.size > maxSize) {
      setError('File size too large. Please upload a clip under 50MB.')
      setFile(null)
      return false
    }
    setError(null)
    return true
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) {
      const selectedFile = e.dataTransfer.files[0]
      if (validateFile(selectedFile)) {
        setFile(selectedFile)
        setResult(null)
      }
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const selectedFile = e.target.files[0]
      if (validateFile(selectedFile)) {
        setFile(selectedFile)
        setResult(null)
      }
    }
  }

  const handlePredict = async () => {
    if (!file) return
    setUploading(true)
    setUploadProgress(0)
    setUploadStage('uploading')
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      // Simulate progress stages
      let currentProgress = 0
      const stageTimer = setInterval(() => {
        currentProgress = Math.min(currentProgress + 5, 90)
        setUploadProgress(currentProgress)
        const stages = ['uploading', 'transcribing', 'vision', 'scoring', 'merging']
        const idx = Math.min(Math.floor(currentProgress / 20), stages.length - 1)
        setUploadStage(stages[idx])
        if (currentProgress >= 90) {
          clearInterval(stageTimer)
        }
      }, 400)

      const res = await fetch(`${API_URL}/api/v1/predict`, {
        method: 'POST',
        body: formData,
      })

      clearInterval(stageTimer)
      setUploadProgress(100)
      setUploadStage('done')

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Prediction failed (${res.status})`)
      }

      const data = await res.json()
      setResult(data)
    } catch (err: any) {
      setError(err.message || 'Prediction failed. Ensure the backend is running.')
    } finally {
      setUploading(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setResult(null)
    setError(null)
    setUploadProgress(0)
    setUploadStage('')
    setVideoPreview(null)
  }

  const engagementChartData = result?.engagement_curve
    ? result.engagement_curve.map((v, i) => ({ second: i + 1, engagement: Math.round(v * 100) }))
    : []

  const hookColor = result?.hook_score && result.hook_score >= 70
    ? 'text-signal-green'
    : result?.hook_score && result.hook_score >= 40
    ? 'text-neural'
    : 'text-signal-red'

  return (
    <div className="min-h-screen bg-neural neural-grid">
      <main className="max-w-4xl mx-auto px-6 py-8 relative z-10">
        {/* Back link */}
        <Link href="/" className="inline-flex items-center gap-2 text-xs text-text-tertiary hover:text-neural transition-colors mb-8">
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to NeuroSim
        </Link>

        {/* Hero */}
        <div className="mb-10">
          <p className="text-[11px] mono text-neural mb-3 tracking-wider uppercase">Virality Predictor — Beta</p>
          <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
            Predict how viral<br />
            <span className="text-neural">your clip will be.</span>
          </h1>
          <p className="text-text-secondary text-sm max-w-lg">
            Upload a clip up to 15 seconds. Get a virality score, hook strength,
            hold rate, and 3D brain activation map — powered by AI video understanding.
          </p>
        </div>

        {/* Upload Zone */}
        {!result && (
          <div className="glass-panel-elevated p-8">
            <div
              className={`p-8 flex flex-col items-center justify-center gap-5 min-h-[200px] cursor-pointer glass-interactive rounded-xl border-2 border-dashed ${
                dragActive ? 'border-neural/40 bg-neural/5' : 'border-white/[0.06]'
              } ${uploading ? 'pointer-events-none opacity-60' : ''}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <input
                type="file"
                accept="video/mp4,video/mov,video/avi,video/webm"
                onChange={handleFileSelect}
                className="hidden"
                id="predict-upload"
                disabled={uploading}
              />

              {videoPreview && !uploading && (
                <div className="w-48 rounded-lg overflow-hidden border border-white/10 mb-2">
                  <video src={videoPreview} muted className="w-full" />
                </div>
              )}

              <label htmlFor="predict-upload" className="cursor-pointer flex flex-col items-center gap-4">
                <motion.div
                  className="w-14 h-14 rounded-xl bg-neural/10 border border-neural/20 flex items-center justify-center"
                  whileHover={hoverLift.whileHover}
                  whileTap={tapPress.whileTap}
                >
                  {uploading ? (
                    <div className="relative w-14 h-14">
                      <svg className="w-14 h-14 -rotate-90" viewBox="0 0 36 36">
                        <circle cx="18" cy="18" r="15.5" fill="none" stroke="rgba(77,238,234,0.15)" strokeWidth="2" />
                        <circle cx="18" cy="18" r="15.5" fill="none" stroke="#4deeea" strokeWidth="2" strokeDasharray={`${uploadProgress * 0.97} 97`} strokeLinecap="round" />
                      </svg>
                      <span className="text-xs mono text-neural font-bold absolute inset-0 flex items-center justify-center">{uploadProgress}%</span>
                    </div>
                  ) : (
                    <Upload className="w-6 h-6 text-neural" />
                  )}
                </motion.div>
                <div className="text-center">
                  <p className="text-white font-medium text-base mb-1">
                    {uploading ? 'Analyzing...' : file ? file.name : 'Drop your clip to predict virality'}
                  </p>
                  <p className="text-text-tertiary text-xs mono">
                    MP4, MOV, AVI, WebM &bull; Up to 100MB &bull; Best under 15s
                  </p>
                  {uploading && uploadStage && (
                    <div className="flex items-center gap-2 mt-3">
                      <div className="w-2 h-2 rounded-full bg-neural animate-pulse" />
                      <span className="text-xs mono text-neural">
                        {PREDICT_STAGES.find(s => s.key === uploadStage)?.label || uploadStage}
                      </span>
                    </div>
                  )}
                </div>
              </label>
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 mt-4 rounded-lg bg-orange-400/10 border border-orange-400/20">
                <AlertTriangle className="w-4 h-4 text-orange-400 flex-shrink-0" />
                <p className="text-xs text-orange-400">{error}</p>
              </div>
            )}

            {file && !uploading && (
              <div className="flex justify-center mt-6">
                <motion.button
                  onClick={handlePredict}
                  className="btn-neural flex items-center gap-2 text-sm px-8 py-3"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Zap className="w-4 h-4" />
                  Predict Viral Potential
                </motion.button>
              </div>
            )}
          </div>
        )}

        {/* Results */}
        <AnimatePresence mode="wait">
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={fadeIn}
              className="space-y-6"
            >
              {/* Score Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Virality Score */}
                <div className="glass-panel p-6 text-center">
                  <p className="text-[10px] mono text-text-tertiary mb-2 tracking-wider uppercase">Viral Potential</p>
                  <div className={`text-5xl font-bold mono ${
                    (result.virality_score || 0) >= 70 ? 'text-signal-green' :
                    (result.virality_score || 0) >= 40 ? 'text-neural' : 'text-signal-red'
                  }`}>
                    {result.virality_score ?? '--'}
                  </div>
                  <p className="text-xs text-text-tertiary mt-1">/ 100</p>
                </div>

                {/* Hook Score */}
                <div className="glass-panel p-6 text-center">
                  <p className="text-[10px] mono text-text-tertiary mb-2 tracking-wider uppercase">Hook Strength</p>
                  <div className={`text-5xl font-bold mono ${hookColor}`}>
                    {result.hook_score}
                  </div>
                  <p className="text-xs text-text-tertiary mt-1">{result.hook_strength}</p>
                </div>

                {/* Hold Rate */}
                <div className="glass-panel p-6 text-center">
                  <p className="text-[10px] mono text-text-tertiary mb-2 tracking-wider uppercase">Hold Rate</p>
                  <div className={`text-5xl font-bold mono ${
                    (result.hold_rate || 0) >= 60 ? 'text-signal-green' :
                    (result.hold_rate || 0) >= 40 ? 'text-neural' : 'text-signal-red'
                  }`}>
                    {result.hold_rate != null ? `${result.hold_rate}%` : '--'}
                  </div>
                  <p className="text-xs text-text-tertiary mt-1">predicted retention</p>
                </div>
              </div>

              {/* Analysis Mode Badge */}
              <div className="flex items-center gap-2">
                <span className={`badge ${result.analysis_mode.includes('vision') ? 'badge-neural' : 'badge-ghost'}`}>
                  {result.analysis_mode.toUpperCase()}
                </span>
                {result.duration_seconds && (
                  <span className="text-xs text-text-tertiary mono">{result.duration_seconds}s clip</span>
                )}
              </div>

              {/* Engagement Curve */}
              {engagementChartData.length > 0 && (
                <div className="glass-panel p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Activity className="w-4 h-4 text-neural" />
                      <h4 className="text-sm font-semibold text-white">Engagement Curve</h4>
                    </div>
                    {result.peak_hook_timestamp != null && (
                      <span className="text-xs mono text-neural">
                        Peak: {result.peak_hook_timestamp}s
                      </span>
                    )}
                  </div>
                  <PredictLineChart data={engagementChartData} />
                </div>
              )}

              {/* Brain + ROI side by side */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 3D Brain */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Brain className="w-4 h-4 text-neural" />
                    <h4 className="text-sm font-semibold text-white">Brain Activation</h4>
                  </div>
                  <Brain3DActivation brainRegions={result.brain_regions || undefined} height={350} />
                </div>

                {/* ROI Scores */}
                <div className="glass-panel p-5">
                  <div className="flex items-center gap-2 mb-5">
                    <TrendingUp className="w-4 h-4 text-swarm" />
                    <h4 className="text-sm font-semibold text-white">ROI Scores</h4>
                  </div>
                  <div className="space-y-4">
                    {[
                      { label: 'A5 — Auditory Cortex', value: result.roi_scores.A5, color: 'progress-neural' },
                      { label: 'LO — Visual Cortex', value: result.roi_scores.LO, color: 'progress-green' },
                      { label: 'Area45 — Persuasion', value: result.roi_scores.Area45, color: 'progress-swarm' },
                      { label: 'TPJ — Social Cognition', value: result.roi_scores.TPJ, color: 'progress-purple' },
                    ].map(item => (
                      <div key={item.label}>
                        <div className="flex justify-between text-xs mb-1.5">
                          <span className="text-text-tertiary">{item.label}</span>
                          <span className="text-white mono">{(item.value * 100).toFixed(0)}%</span>
                        </div>
                        <div className="progress-track">
                          <div className={`progress-fill ${item.color}`} style={{ width: `${item.value * 100}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Derived metrics */}
                  <div className="mt-6 pt-4 border-t border-white/[0.06] grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-[10px] mono text-text-tertiary mb-1">AUTHENTICITY</p>
                      <p className="text-xl font-bold mono text-white">{result.authenticity_score}</p>
                    </div>
                    <div>
                      <p className="text-[10px] mono text-text-tertiary mb-1">SUCCESS PROB</p>
                      <p className="text-xl font-bold mono text-neural">{result.success_probability}%</p>
                    </div>
                    <div>
                      <p className="text-[10px] mono text-text-tertiary mb-1">VIRAL POTENTIAL</p>
                      <p className="text-xl font-bold mono text-swarm">{result.viral_potential}</p>
                    </div>
                    <div>
                      <p className="text-[10px] mono text-text-tertiary mb-1">STAGE GATE</p>
                      <p className={`text-xl font-bold mono ${result.stage_gate.passed ? 'text-signal-green' : 'text-signal-red'}`}>
                        {result.stage_gate.passed ? 'PASS' : 'FAIL'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              {result.recommendations.length > 0 && (
                <div className="glass-panel p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Sparkles className="w-4 h-4 text-neural" />
                    <h4 className="text-sm font-semibold text-white">Recommendations</h4>
                  </div>
                  <div className="space-y-2">
                    {result.recommendations.map((rec: string, i: number) => (
                      <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                        <CheckCircle className="w-4 h-4 text-neural mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-text-secondary">{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* CTA to full analysis */}
              <div className="glass-panel p-6 border border-neural/20">
                <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                  <div>
                    <h4 className="text-sm font-semibold text-white mb-1">Want deeper analysis?</h4>
                    <p className="text-xs text-text-tertiary">
                      Upload to NeuroSim for full ROI breakdown, swarm simulation, PDF reports, and benchmark comparison.
                    </p>
                  </div>
                  <Link href="/dashboard" className="btn-neural flex items-center gap-2 text-sm px-6 py-2.5 whitespace-nowrap">
                    <Play className="w-4 h-4" />
                    Full Analysis
                  </Link>
                </div>
              </div>

              {/* Reset button */}
              <div className="flex justify-center">
                <motion.button
                  onClick={handleReset}
                  className="btn-ghost flex items-center gap-2 text-sm"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <RotateCcw className="w-4 h-4" />
                  Predict Another Clip
                </motion.button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}
