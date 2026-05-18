'use client'

import { useState, useCallback, useEffect, Suspense } from 'react'
import { useAuth } from '../../lib/auth-context'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Upload, Play, Brain, Users, Zap, TrendingUp, 
  AlertTriangle, CheckCircle, Sparkles, BarChart2, 
  Activity, Target, Eye, MessageSquare, ChevronRight,
  Scan, Waves, Network, Cpu, Radio, Shield
} from 'lucide-react'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, AreaChart, Area,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts'
import axios from 'axios'
import dynamic from 'next/dynamic'

const Brain3D = dynamic(() => import('../components/Brain3D'), { 
  ssr: false,
  loading: () => <div className="w-full h-[300px] glass-panel flex items-center justify-center"><div className="w-6 h-6 border-2 border-neural border-t-transparent rounded-full animate-spin" /></div>
})

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Dashboard() {
  const { isSignedIn, isLoaded } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (isLoaded && !isSignedIn) router.push('/')
  }, [isLoaded, isSignedIn, router])

  const [videos, setVideos] = useState<any[]>([])
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'analysis' | 'abtesting'>('overview')
  const [abTestRunning, setAbTestRunning] = useState(false)
  const [abResults, setAbResults] = useState<any>(null)
  const [demoMode, setDemoMode] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [modelStatus, setModelStatus] = useState<any>(null)

  const handleUpload = async (file: File) => {
    if (!file) return
    setUploading(true)
    setApiError(null)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const res = await axios.post(`${API_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 15000
      })
      
      setVideos(prev => [...prev, {
        id: res.data.video_id,
        filename: res.data.filename,
        upload_time: new Date().toISOString(),
        status: res.data.status
      }])
      
      setSelectedVideo(res.data.video_id)
      setAnalysis(res.data)
    } catch (err: any) {
      console.error('Upload failed:', err)
      setDemoMode(true)
      const demoId = `demo_${Date.now()}`
      setVideos(prev => [...prev, {
        id: demoId,
        filename: file.name,
        upload_time: new Date().toISOString(),
        status: 'analyzed'
      }])
      
      setAnalysis({
        video_id: demoId,
        hook_score: 78,
        hook_details: { strength: 'Strong', curiosity_gap_detected: true, question_detected: true },
        authenticity_score: 72,
        authenticity_details: { authenticity_level: 'High', brand_intrusion: 'Low' },
        sentiment_forecast: { 
          positive_sentiment_pct: 62.5,
          negative_sentiment_pct: 7.2,
          neutral_sentiment_pct: 30.3,
          backlash_risk: 'Low',
          shareability_index: 78,
          sellout_probability: 23
        },
        cta_analysis: {
          cta_activation_score: 75,
          cognitive_load: 'Optimal',
          timing_recommendation: 'Current placement optimal'
        },
        viral_potential: 72,
        success_probability: 74,
        risk_score: 16,
        recommendations: [
          'Strong hook detected with curiosity gap - good viral potential',
          'High authenticity score - content feels natural',
          'CTA at 8s mark should perform well'
        ],
        mirofish_simulation: {
          simulation_id: 'sim_demo_001',
          final_sentiment: 68.5,
          viral_prediction: 'High - Positive sentiment spreading',
          backlash_prediction: 'Low risk - positive reception',
          share_prediction: 72,
          persona_distribution: { loyal_fan: 18, trend_seeker: 24, casual_viewer: 26, skeptic: 10, budget_shopper: 16, anti_ad: 6 },
          comment_samples: [
            { type: 'positive', persona: 'trend_seeker', comment: 'sharing this! everyone needs to see this', sentiment: 0.82 },
            { type: 'neutral', persona: 'casual_viewer', comment: 'interesting', sentiment: 0.55 },
            { type: 'positive', persona: 'loyal_fan', comment: 'omg love this!', sentiment: 0.91 }
          ],
          trust_trajectory: [65, 68, 70, 72, 74, 76, 78]
        },
        tribev2_brain_response: {
          cortical_response: { 
            visual_cortex: 78, auditory_cortex: 72, language_center: 68,
            amygdala: 65, prefrontal_cortex: 70, reward_center: 82,
            social_cognition: 62, memory_formation: 68, overall_response_strength: 72
          },
          emotional_impact: { primary_emotion: 'excitement', emotional_intensity: 72 },
          engagement_prediction: { overall_engagement: 78, retention_prediction: 'high' },
          mode: 'simulated'
        },
        stage_gate: { passed: true, W_attn: 0.72, threshold: 0.4 }
      })
      setSelectedVideo(demoId)
      let errorMsg = 'Demo Mode - Backend unavailable'
      if (err.code === 'ECONNABORTED') {
        errorMsg = 'Demo Mode - Backend timeout. Ensure NeuroSim is running on localhost:8000'
      } else if (err.response) {
        errorMsg = `Demo Mode - Backend error (${err.response.status})`
      } else if (err.request) {
        errorMsg = 'Demo Mode - Cannot reach backend. Run NeuroSim on localhost:8000'
      }
      setApiError(errorMsg)
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) handleUpload(e.dataTransfer.files[0])
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
    if (e.target.files?.[0]) handleUpload(e.target.files[0])
  }

  const runABTest = async () => {
    setAbTestRunning(true)
    setApiError(null)
    
    try {
      const [resA, resB] = await Promise.all([
        axios.post(`${API_URL}/simulate/single`, { content_url: 'version_a' }, { timeout: 10000 }),
        axios.post(`${API_URL}/simulate/single`, { content_url: 'version_b' }, { timeout: 10000 })
      ])
      
      const dataA = resA.data
      const dataB = resB.data
      
      if (dataA.social && dataA.social.seven_day_curve) {
        dataA.social.seven_day_curve = dataA.social.seven_day_curve.map((v: number, i: number) => ({ day: i+1, value: v }))
      }
      if (dataB.social && dataB.social.seven_day_curve) {
        dataB.social.seven_day_curve = dataB.social.seven_day_curve.map((v: number, i: number) => ({ day: i+1, value: v }))
      }
      
      setAbResults({
        version_a: dataA,
        version_b: dataB,
        winner: dataA.W_attn > dataB.W_attn ? 'A' : 'B'
      })
    } catch (err: any) {
      console.error('A/B test failed:', err)
      setApiError('A/B test failed. Backend may be unavailable.')
    } finally {
      setAbTestRunning(false)
    }
  }

  const loadDemoData = () => {
    setDemoMode(true)
    const demoId = `demo_${Date.now()}`
    setVideos([{
      id: demoId,
      filename: 'sample_video.mp4',
      upload_time: new Date().toISOString(),
      status: 'analyzed'
    }])
    
    setAnalysis({
      video_id: demoId,
      hook_score: 78,
      hook_details: { strength: 'Strong', curiosity_gap_detected: true, question_detected: true },
      authenticity_score: 72,
      authenticity_details: { authenticity_level: 'High', brand_intrusion: 'Low' },
      sentiment_forecast: { 
        positive_sentiment_pct: 62.5, negative_sentiment_pct: 7.2, neutral_sentiment_pct: 30.3,
        backlash_risk: 'Low', shareability_index: 78, sellout_probability: 23
      },
      cta_analysis: { cta_activation_score: 75, cognitive_load: 'Optimal', timing_recommendation: 'Current placement optimal' },
      viral_potential: 72, success_probability: 74, risk_score: 16,
      recommendations: [
        'Strong hook detected with curiosity gap - good viral potential',
        'High authenticity score - content feels natural',
        'CTA at 8s mark should perform well'
      ],
      mirofish_simulation: {
        simulation_id: 'sim_demo_001', final_sentiment: 68.5,
        viral_prediction: 'High - Positive sentiment spreading',
        backlash_prediction: 'Low risk - positive reception',
        share_prediction: 72,
        persona_distribution: { loyal_fan: 18, trend_seeker: 24, casual_viewer: 26, skeptic: 10, budget_shopper: 16, anti_ad: 6 },
        comment_samples: [
          { type: 'positive', persona: 'trend_seeker', comment: 'sharing this! everyone needs to see this', sentiment: 0.82 },
          { type: 'neutral', persona: 'casual_viewer', comment: 'interesting', sentiment: 0.55 },
          { type: 'positive', persona: 'loyal_fan', comment: 'omg love this!', sentiment: 0.91 }
        ],
        trust_trajectory: [65, 68, 70, 72, 74, 76, 78]
      },
      tribev2_brain_response: {
        cortical_response: { 
          visual_cortex: 78, auditory_cortex: 72, language_center: 68,
          amygdala: 65, prefrontal_cortex: 70, reward_center: 82,
          social_cognition: 62, memory_formation: 68, overall_response_strength: 72
        },
        emotional_impact: { primary_emotion: 'excitement', emotional_intensity: 72 },
        engagement_prediction: { overall_engagement: 78, retention_prediction: 'high' },
        mode: 'simulated'
      },
      stage_gate: { passed: true, W_attn: 0.72, threshold: 0.4 }
    })
    setSelectedVideo(demoId)
  }

  const radarData = analysis ? [
    { subject: 'Hook', value: analysis.hook_score || 0, fullMark: 100 },
    { subject: 'Authenticity', value: analysis.authenticity_score || 0, fullMark: 100 },
    { subject: 'Viral', value: analysis.viral_potential || 0, fullMark: 100 },
    { subject: 'CTA', value: analysis.cta_analysis?.cta_activation_score || 0, fullMark: 100 },
    { subject: 'Share', value: analysis.sentiment_forecast?.shareability_index || 0, fullMark: 100 },
  ] : []

  return (
    <div className="min-h-screen bg-neural neural-grid">
      {/* Header - minimal, precise */}
      <header className="sticky top-0 z-50 border-b border-white/[0.04] bg-black/60 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-neural/10 border border-neural/20 flex items-center justify-center">
              <Brain className="w-4 h-4 text-neural" />
            </div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-semibold text-white tracking-tight">NeuroSim</h1>
              <span className="text-[10px] mono text-text-tertiary">v2.0</span>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <span className="status-dot status-neural"></span>
                <span className="text-[11px] mono text-text-tertiary">TRIBE</span>
              </div>
              <div className="w-px h-3 bg-white/10"></div>
              <div className="flex items-center gap-1.5">
                <span className="status-dot status-swarm"></span>
                <span className="text-[11px] mono text-text-tertiary">MIROFISH</span>
              </div>
            </div>
            {demoMode && (
              <span className="badge badge-ghost">DEMO</span>
            )}
            <button 
              onClick={loadDemoData}
              className="btn-ghost text-xs py-1.5 px-3"
            >
              Load Demo
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 relative z-10">
        {/* Hero - asymmetric composition */}
        <div className="mb-10">
          <div className="flex items-end justify-between mb-8">
            <div className="max-w-lg">
              <p className="text-[11px] mono text-neural mb-3 tracking-wider uppercase">Predictive Content Intelligence</p>
              <h2 className="text-4xl font-bold text-white mb-4 leading-tight">
                Measure neural response<br />
                <span className="text-text-tertiary">before you publish.</span>
              </h2>
              <p className="text-text-secondary text-sm max-w-md">
                TRIBE v2 encodes biological brain responses. MiroFish simulates social swarm behavior. 
                Together, they predict how your content will perform.
              </p>
            </div>
          </div>

          {/* Upload Zone - hero element, asymmetric */}
          <div 
            className={`glass-panel-elevated p-12 flex flex-col items-center justify-center gap-5 min-h-[180px] cursor-pointer glass-interactive ${dragActive ? 'drag-active' : ''}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <input 
              type="file" 
              accept="video/mp4,video/mov,video/avi,video/webm"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-4">
              <motion.div 
                className="w-14 h-14 rounded-xl bg-neural/10 border border-neural/20 flex items-center justify-center"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {uploading ? (
                  <div className="w-6 h-6 border-2 border-neural border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Upload className="w-6 h-6 text-neural" />
                )}
              </motion.div>
              <div className="text-center">
                <p className="text-white font-medium text-base mb-1">
                  {uploading ? 'Encoding neural response...' : 'Drop video to analyze'}
                </p>
                <p className="text-text-tertiary text-xs mono">
                  MP4, MOV, AVI, WebM ΓÇó Up to 2GB
                </p>
              </div>
            </label>
        </div>
      </div>

        {apiError && (
          <div className="mb-6 p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center gap-3">
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <p className="text-sm text-amber-200">{apiError}</p>
          </div>
        )}

        {/* Stats - inline, minimal */}
        {videos.length > 0 && (
          <div className="flex items-center gap-6 mb-8 stagger">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-white mono">{videos.length}</span>
              <span className="text-xs text-text-tertiary">videos</span>
            </div>
            <div className="w-px h-6 bg-white/10"></div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-neural mono">{videos.filter(v => v.status === 'analyzed').length}</span>
              <span className="text-xs text-text-tertiary">analyzed</span>
            </div>
            <div className="w-px h-6 bg-white/10"></div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-swarm mono">{analysis?.success_probability ?? '--'}</span>
              <span className="text-xs text-text-tertiary">avg score</span>
            </div>
          </div>
        )}

        {/* Main Content - asymmetric layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left column - main content (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* Tab Bar */}
            <div className="flex items-center gap-1 p-1 glass-panel w-fit">
              {[
                { id: 'overview', label: 'Overview', icon: BarChart2 },
                { id: 'analysis', label: 'Neural Analysis', icon: Brain },
                { id: 'abtesting', label: 'A/B Testing', icon: Target },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`tab-segment flex items-center gap-2 ${activeTab === tab.id ? 'active' : ''}`}
                >
                  <tab.icon className="w-3.5 h-3.5" />
                  {tab.label}
                </button>
              ))}
            </div>

            <AnimatePresence mode="wait">
              {activeTab === 'overview' && (
                <motion.div 
                  key="overview"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.2, ease: 'easeOut' }}
                  className="space-y-6"
                >
                  {analysis ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 stagger">
                      {[
                        { label: 'Success', value: analysis.success_probability, accent: 'neural' },
                        { label: 'Risk', value: analysis.risk_score, accent: 'orange' },
                        { label: 'Viral', value: analysis.viral_potential, accent: 'swarm' },
                        { label: 'Hook', value: analysis.hook_score, accent: 'neural' },
                      ].map((metric, i) => (
                        <div key={metric.label} className="glass-panel p-4">
                          <p className="text-[10px] mono text-text-tertiary uppercase tracking-wider mb-2">{metric.label}</p>
                          <p className={`text-2xl font-bold mono ${
                            metric.accent === 'neural' ? 'text-neural' :
                            metric.accent === 'swarm' ? 'text-swarm' :
                            metric.accent === 'orange' ? 'text-orange-400' :
                            'text-white'
                          }`}>
                            {metric.value}%
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="glass-panel p-16 flex flex-col items-center justify-center text-center">
                      <motion.div 
                        className="w-16 h-16 rounded-xl bg-neural/5 border border-neural/10 flex items-center justify-center mb-5"
                        animate={{ opacity: [0.5, 1, 0.5] }}
                        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                      >
                        <Activity className="w-7 h-7 text-neural/60" />
                      </motion.div>
                      <h3 className="text-lg font-semibold text-white mb-2">Ready for Analysis</h3>
                      <p className="text-text-tertiary text-sm max-w-sm mb-6">
                        Upload a video to receive neural response predictions and social simulation results.
                      </p>
                      <button className="btn-neural flex items-center gap-2 text-sm">
                        <Upload className="w-4 h-4" />
                        Get Started
                      </button>
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === 'analysis' && analysis && (
                <motion.div 
                  key="analysis"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.2, ease: 'easeOut' }}
                  className="space-y-6"
                >
                  {/* 3D Brain Heatmap */}
                  <Suspense fallback={<div className="w-full h-[300px] glass-panel flex items-center justify-center"><div className="w-6 h-6 border-2 border-neural border-t-transparent rounded-full animate-spin" /></div>}>
                    <Brain3D brainData={analysis.tribev2_brain_response} />
                  </Suspense>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="glass-panel p-5">
                      <div className="flex items-center justify-between mb-5">
                        <div className="flex items-center gap-2">
                          <Brain className="w-4 h-4 text-neural" />
                          <h4 className="text-sm font-semibold text-white">Neural Response</h4>
                        </div>
                        <span className={`badge ${analysis.tribev2_brain_response?.mode === 'real' ? 'badge-neural' : 'badge-ghost'}`}>
                          {analysis.tribev2_brain_response?.mode === 'real' ? 'REAL' : 'SIM'}
                        </span>
                      </div>
                      <ResponsiveContainer width="100%" height={200}>
                        <RadarChart data={radarData}>
                          <PolarGrid stroke="rgba(255,255,255,0.05)" />
                          <PolarAngleAxis dataKey="subject" tick={{ fill: '#555', fontSize: 10 }} />
                          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#333' }} />
                          <Radar name="Response" dataKey="value" stroke="#4deeea" fill="#4deeea" fillOpacity={0.1} strokeWidth={1.5} />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>

                    <div className="glass-panel p-5">
                      <div className="flex items-center justify-between mb-5">
                        <div className="flex items-center gap-2">
                          <MessageSquare className="w-4 h-4 text-swarm" />
                          <h4 className="text-sm font-semibold text-white">Sentiment</h4>
                        </div>
                        <span className={`badge ${analysis.mirofish_simulation?.mode === 'real' ? 'badge-swarm' : 'badge-ghost'}`}>
                          {analysis.mirofish_simulation?.mode === 'real' ? 'REAL' : 'SIM'}
                        </span>
                      </div>
                      <div className="space-y-4">
                        {[
                          { label: 'Positive', value: analysis.sentiment_forecast?.positive_sentiment_pct || 0, color: 'progress-green' },
                          { label: 'Neutral', value: analysis.sentiment_forecast?.neutral_sentiment_pct || 0, color: 'progress-track' },
                          { label: 'Negative', value: analysis.sentiment_forecast?.negative_sentiment_pct || 0, color: 'progress-red' },
                        ].map(item => (
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

                  {analysis.recommendations && analysis.recommendations.length > 0 && (
                    <div className="glass-panel p-5">
                      <div className="flex items-center gap-2 mb-4">
                        <Sparkles className="w-4 h-4 text-neural" />
                        <h4 className="text-sm font-semibold text-white">Recommendations</h4>
                      </div>
                      <div className="space-y-2">
                        {analysis.recommendations.map((rec: string, i: number) => (
                          <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                            <CheckCircle className="w-4 h-4 text-neural mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-text-secondary">{rec}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === 'abtesting' && (
                <motion.div 
                  key="abtesting"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.2, ease: 'easeOut' }}
                  className="space-y-6"
                >
                  <div className="glass-panel p-6">
                    <h3 className="text-base font-semibold text-white mb-1">Neuro-Social A/B Prediction</h3>
                    <p className="text-text-tertiary text-xs mono">Stage-Gate ΓÇó W = 0.7├ùLO + 0.3├ùA5</p>
                  </div>

                  {!abResults && !abTestRunning && (
                    <div className="flex justify-center">
                      <motion.button
                        onClick={runABTest}
                        className="btn-neural flex items-center gap-2 px-6 py-3"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <Play className="w-4 h-4" />
                        Run Predictive Test
                      </motion.button>
                    </div>
                  )}

                  {abTestRunning && (
                    <div className="glass-panel p-12 flex flex-col items-center justify-center">
                      <div className="relative w-16 h-16 mb-5">
                        <div className="absolute inset-0 rounded-full border border-neural/30 animate-spin"></div>
                        <div className="absolute inset-2 rounded-full border border-swarm/30 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
                        <Brain className="w-6 h-6 text-neural absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                      </div>
                      <p className="text-white font-medium mb-1">Running Neural Pipeline</p>
                      <p className="text-text-tertiary text-xs mono">TRIBE v2 ΓåÆ ROI ΓåÆ MiroFish Swarm</p>
                    </div>
                  )}

                  {abResults && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        {['A', 'B'].map((ver) => {
                          const data = abResults[`version_${ver.toLowerCase()}`]
                          const isWinner = abResults.winner === ver
                          
                          return (
                            <div 
                              key={ver}
                              className={`glass-panel p-5 ${isWinner ? 'border-neural/20' : ''}`}
                            >
                              <div className="flex items-center justify-between mb-4">
                                <span className="text-lg font-bold text-white mono">V{ver}</span>
                                {isWinner && (
                                  <span className="badge badge-neural">WINNER</span>
                                )}
                              </div>
                              
                              <div className="space-y-3">
                                <div>
                                  <div className="flex justify-between text-xs mb-1.5">
                                    <span className="text-text-tertiary">W_attn</span>
                                    <span className={`mono font-medium ${data.W_attn >= 0.4 ? 'text-neural' : 'text-red-400'}`}>
                                      {data.W_attn.toFixed(3)}
                                    </span>
                                  </div>
                                  <div className="progress-track">
                                    <div 
                                      className={`progress-fill ${data.W_attn >= 0.4 ? 'progress-neural' : 'progress-red'}`}
                                      style={{ width: `${data.W_attn * 100}%` }}
                                    />
                                  </div>
                                </div>
                                
                                <div className="flex justify-between items-center pt-2 border-t border-white/[0.04]">
                                  <span className="text-[10px] mono text-text-tertiary">STAGE-GATE</span>
                                  <span className={`text-xs mono font-medium ${data.stage_gate_passed ? 'text-green-400' : 'text-red-400'}`}>
                                    {data.stage_gate_passed ? 'PASS' : 'FAIL'}
                                  </span>
                                </div>
                                
                                {data.social && (
                                  <div className="pt-3 space-y-2">
                                    <div className="flex justify-between">
                                      <span className="text-text-tertiary text-xs">Viral Coef</span>
                                      <span className="mono text-swarm text-xs">{data.social.viral_coefficient.toFixed(2)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-text-tertiary text-xs">Peak Reach</span>
                                      <span className="text-white text-xs mono">{data.social.peak_reach.toLocaleString()}</span>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          )
                        })}
                      </div>

                      {abResults.version_a.social && abResults.version_b.social && (
                        <div className="glass-panel p-5">
                          <h4 className="text-sm font-semibold text-white mb-4">7-Day Propagation</h4>
                          <ResponsiveContainer width="100%" height={240}>
                            <AreaChart>
                              <defs>
                                <linearGradient id="gradA" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#4deeea" stopOpacity={0.2}/>
                                  <stop offset="95%" stopColor="#4deeea" stopOpacity={0}/>
                                </linearGradient>
                                <linearGradient id="gradB" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#a78bfa" stopOpacity={0.2}/>
                                  <stop offset="95%" stopColor="#a78bfa" stopOpacity={0}/>
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                              <XAxis dataKey="day" stroke="#444" fontSize={10} />
                              <YAxis stroke="#444" fontSize={10} />
                              <Tooltip 
                                contentStyle={{ background: '#0f0f16', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px' }}
                                labelStyle={{ color: '#fff' }}
                              />
                              <Area 
                                type="monotone" 
                                data={abResults.version_a.social.seven_day_curve.map((v: number, i: number) => ({ day: i+1, a: v }))}
                                dataKey="a" 
                                stroke="#4deeea" 
                                fill="url(#gradA)" 
                                strokeWidth={1.5}
                                name="Version A"
                              />
                              <Area 
                                type="monotone" 
                                data={abResults.version_b.social.seven_day_curve.map((v: number, i: number) => ({ day: i+1, b: v }))}
                                dataKey="b" 
                                stroke="#a78bfa" 
                                fill="url(#gradB)" 
                                strokeWidth={1.5}
                                name="Version B"
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      <div className="glass-panel p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Zap className="w-4 h-4 text-neural" />
                          <div>
                            <p className="text-xs text-text-tertiary">Neuro-Social Bridge</p>
                            <p className="mono text-white text-xs">W = 0.7 ├ù LO + 0.3 ├ù A5</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-[10px] mono text-text-tertiary">GATE</p>
                          <p className="text-lg font-bold mono text-green-400">0.4</p>
                        </div>
                      </div>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right column - sidebar (4 cols) */}
          <div className="lg:col-span-4 space-y-4">
            {/* Active Models */}
            <div className="glass-panel p-4">
              <h4 className="text-[10px] mono text-text-tertiary uppercase tracking-wider mb-3">Systems</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02]">
                  <div className="flex items-center gap-2">
                    <span className="status-dot status-neural"></span>
                    <div>
                      <span className="text-xs text-white font-medium">TRIBE v2</span>
                      <p className="text-[10px] text-text-tertiary">Brain Encoding</p>
                    </div>
                  </div>
                  <span className="text-[10px] mono text-neural">ONLINE</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02]">
                  <div className="flex items-center gap-2">
                    <span className="status-dot status-swarm"></span>
                    <div>
                      <span className="text-xs text-white font-medium">MiroFish</span>
                      <p className="text-[10px] text-text-tertiary">Swarm Sim</p>
                    </div>
                  </div>
                  <span className="text-[10px] mono text-swarm">ONLINE</span>
                </div>
              </div>
            </div>

            {analysis && (
              <>
                {/* Risk Assessment */}
                <div className="glass-panel p-4">
                  <h4 className="text-[10px] mono text-text-tertiary uppercase tracking-wider mb-3">Risk</h4>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="text-text-tertiary">Backlash</span>
                        <span className={analysis.sentiment_forecast?.backlash_risk === 'Low' ? 'text-green-400' : 'text-orange-400'}>
                          {analysis.sentiment_forecast?.backlash_risk || 'N/A'}
                        </span>
                      </div>
                      <div className="progress-track">
                        <div className="progress-fill progress-orange" style={{ width: `${analysis.risk_score || 0}%` }} />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="text-text-tertiary">Sellout</span>
                        <span className="text-orange-400 mono">{analysis.sentiment_forecast?.sellout_probability || 0}%</span>
                      </div>
                      <div className="progress-track">
                        <div className="progress-fill progress-swarm" style={{ width: `${analysis.sentiment_forecast?.sellout_probability || 0}%` }} />
                      </div>
                    </div>
                  </div>
                </div>

                {/* CTA Optimization */}
                {analysis.cta_analysis && (
                  <div className="glass-panel p-4">
                    <h4 className="text-[10px] mono text-text-tertiary uppercase tracking-wider mb-3">CTA</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-text-tertiary text-xs">Activation</span>
                        <span className="mono text-neural text-xs">{analysis.cta_analysis.cta_activation_score}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-tertiary text-xs">Load</span>
                        <span className="text-white text-xs">{analysis.cta_analysis.cognitive_load}</span>
                      </div>
                      <p className="text-[10px] text-text-tertiary pt-2 border-t border-white/[0.04]">
                        {analysis.cta_analysis.timing_recommendation}
                      </p>
                    </div>
                  </div>
                )}

                {/* Stage-Gate */}
                {analysis.stage_gate && (
                  <div className="glass-panel p-4">
                    <h4 className="text-[10px] mono text-text-tertiary uppercase tracking-wider mb-3">Stage-Gate</h4>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xl font-bold text-white mono">{analysis.stage_gate.W_attn.toFixed(3)}</p>
                        <p className="text-[10px] text-text-tertiary">W_attn</p>
                      </div>
                      <div className={`px-3 py-1.5 rounded-lg ${analysis.stage_gate.passed ? 'bg-green-400/10 text-green-400' : 'bg-red-400/10 text-red-400'}`}>
                        <span className="text-xs mono font-medium">
                          {analysis.stage_gate.passed ? 'PASS' : 'FAIL'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Recent Uploads */}
            {videos.length > 0 && (
              <div className="glass-panel p-4">
                <h4 className="text-[10px] mono text-text-tertiary uppercase tracking-wider mb-3">Recent</h4>
                <div className="space-y-1.5">
                  {videos.slice(-5).reverse().map(video => (
                    <div 
                      key={video.id}
                      className="p-2.5 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors cursor-pointer"
                      onClick={() => setSelectedVideo(video.id)}
                    >
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-xs text-white truncate max-w-[140px]">{video.filename}</span>
                        <span className={`text-[10px] mono px-1.5 py-0.5 rounded ${
                          video.status === 'analyzed' ? 'bg-green-400/10 text-green-400' :
                          video.status === 'processing' ? 'bg-orange-400/10 text-orange-400' :
                          'bg-white/5 text-text-tertiary'
                        }`}>
                          {video.status}
                        </span>
                      </div>
                      <p className="text-[10px] text-text-tertiary mono">
                        {new Date(video.upload_time).toLocaleTimeString()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
