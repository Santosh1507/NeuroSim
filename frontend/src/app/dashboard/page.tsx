'use client'

import { useState, useCallback, useEffect, useRef, Suspense, useMemo } from 'react'
import { useAuth } from '../../lib/auth-context'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { tabSwitch, pulseSlow, hoverLift, tapPress } from '../../lib/easing'
import {
  Brain, Users, Upload, FileText, Youtube, TrendingUp, Share2, Download, MessageSquare, Activity, Target, Zap,
  ChevronRight, Check, X, AlertTriangle, RotateCcw, Trash2, RefreshCw, Plus, Edit3, ArrowLeft, BarChart3,
  Sparkles, Volume2, Music, Hash, Compass, Eye, Play, Pause, ChevronDown, AlertCircle, Copy,
  ArrowUpRight, ExternalLink, Scan, Sliders, CheckCircle
} from 'lucide-react'
import { UsageCounter } from '../components/UsageCounter'
import ProgressStageIndicator from '../components/ProgressStageIndicator'
import axios from 'axios'
import { supabase } from '../../lib/supabase'

// Inject Supabase auth token into all axios requests from this page
axios.interceptors.request.use(async (config) => {
  if (supabase) {
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.access_token) {
      config.headers.set('Authorization', `Bearer ${session.access_token}`)
    }
  }
  return config
})
import dynamic from 'next/dynamic'
import OnboardingTour from '../components/OnboardingTour'

const Brain3D = dynamic(() => import('../components/Brain3D'), { 
  ssr: false,
  loading: () => <div className="w-full h-[300px] glass-panel flex items-center justify-center"><div className="w-6 h-6 border-2 border-neural border-t-transparent rounded-full animate-spin" /></div>
})

const SimulatedPhone = dynamic(() => import('../components/SimulatedPhone'), { 
  ssr: false,
  loading: () => <div className="w-full h-[400px] glass-panel flex items-center justify-center"><div className="w-6 h-6 border-2 border-neural border-t-transparent rounded-full animate-spin" /></div>
})

const DashboardRadar = dynamic(() => import('../components/charts/DashboardCharts').then(m => ({ default: m.DashboardRadar })), { ssr: false })
const DashboardABAreaChart = dynamic(() => import('../components/charts/DashboardCharts').then(m => ({ default: m.DashboardABAreaChart })), { ssr: false })

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export default function Dashboard() {
  const { isSignedIn, isLoaded, guestSessionId, recoverGuestSession } = useAuth()
  const router = useRouter()
  const pollAbortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (isLoaded && !isSignedIn) router.push('/')
  }, [isLoaded, isSignedIn, router])

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      pollAbortRef.current?.abort()
    }
  }, [])

  const [videos, setVideos] = useState<any[]>([])
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'analysis' | 'abtesting' | 'llm_compare' | 'feed_simulator'>('overview')
  const [abTestRunning, setAbTestRunning] = useState(false)
  const [abResults, setAbResults] = useState<any>(null)
  const [demoMode, setDemoMode] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [modelStatus, setModelStatus] = useState<any>(null)
  const [compareData, setCompareData] = useState<any>(null)
  const [loadingComparison, setLoadingComparison] = useState(false)
  const [showShareModal, setShowShareModal] = useState(false)
  const [shareUrl, setShareUrl] = useState('')
  const [sharing, setSharing] = useState(false)
  const [copied, setCopied] = useState(false)
  const [onboardingComplete, setOnboardingComplete] = useState(true)

  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatusMsg, setUploadStatusMsg] = useState('')
  const [uploadStage, setUploadStage] = useState<string>('')
  const [isMobile, setIsMobile] = useState(false)
  const [compareIds, setCompareIds] = useState<string[]>([])
  const [backendReachable, setBackendReachable] = useState<boolean | null>(null)
  const [showFeedbackForm, setShowFeedbackForm] = useState(false)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)
  const [feedbackData, setFeedbackData] = useState({ views: '', engagement: '', wouldPublish: true })

  const [inputMode, setInputMode] = useState<'upload' | 'script' | 'youtube'>('upload')
  const [scriptText, setScriptText] = useState('')
  const [scriptTitle, setScriptTitle] = useState('')
  const [scriptError, setScriptError] = useState<string | null>(null)
  const [analyzingScript, setAnalyzingScript] = useState(false)
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [youtubeError, setYoutubeError] = useState<string | null>(null)
  const [analyzingYoutube, setAnalyzingYoutube] = useState(false)

  const [whatIfMods, setWhatIfMods] = useState({
    emotional_tone: false,
    earlier_product_mention: false,
    aggressive_cta: false,
    price_decrease: 0,
  })
  const [whatIfResult, setWhatIfResult] = useState<any>(null)
  const [whatIfRunning, setWhatIfRunning] = useState(false)
  const [validationSubmitted, setValidationSubmitted] = useState(false)
  const [validationData, setValidationData] = useState({ views: '', engagement: '', days: '7' })
  const [benchmarkData, setBenchmarkData] = useState<any>(null)
  const [benchmarkCohort, setBenchmarkCohort] = useState('all')

  // A/B Workspace states
  const [abTests, setAbTests] = useState<any[]>([])
  const [selectedAbTestId, setSelectedAbTestId] = useState<string | null>(null)
  const [abBaselineVideoId, setAbBaselineVideoId] = useState<string>('')
  const [abVariantVideoId, setAbVariantVideoId] = useState<string>('')
  const [abVariantScript, setAbVariantScript] = useState<string>('')
  const [abCompareMode, setAbCompareMode] = useState<'script' | 'video'>('script')
  const [abTestName, setAbTestName] = useState<string>('')

  // Script rewrite state
  const [isRewriting, setIsRewriting] = useState(false)
  const [rewriteResult, setRewriteResult] = useState<any>(null)
  const [showRewriteModal, setShowRewriteModal] = useState(false)
  const [activeRewriteDimension, setActiveRewriteDimension] = useState<'hook' | 'authenticity' | 'cta'>('hook')
  const [additionalInstructions, setAdditionalInstructions] = useState('')
  const [rewriteError, setRewriteError] = useState<string | null>(null)

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  useEffect(() => {
    axios.get(`${API_URL}/health`, { timeout: 5000 })
      .then(() => setBackendReachable(true))
      .catch(() => setBackendReachable(false))
  }, [])

  const selectVideo = async (videoId: string, customVideosList?: any[]) => {
    setSelectedVideo(videoId)
    const list = customVideosList || videos
    const videoObj = list.find((v: any) => v.id === videoId)
    if (!videoObj) return
    
    if (videoObj.status === 'analyzed') {
      try {
        const analysisRes = await axios.get(`${API_URL}/analyses/${videoId}`, { timeout: 10000 })
        setAnalysis({ filename: videoObj.filename, ...analysisRes.data })
        
        // Also pre-fill baseline video selection for A/B testing
        setAbBaselineVideoId(videoId)
        
        // Pre-fill transcript in variant script block
        const transcriptText = analysisRes.data.full_transcript || analysisRes.data.transcript || ''
        setAbVariantScript(transcriptText)
      } catch (err) {
        console.error('Failed to load analysis for selected video:', err)
      }
    }
  }

  const fetchABTests = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/v1/ab-tests`)
      setAbTests(res.data.ab_tests || [])
    } catch (err) {
      console.error('Failed to fetch A/B tests:', err)
    }
  }

  const deleteABTest = async (testId: string) => {
    try {
      await axios.delete(`${API_URL}/api/v1/ab-tests/${testId}`)
      if (selectedAbTestId === testId) {
        setAbResults(null)
        setSelectedAbTestId(null)
      }
      await fetchABTests()
    } catch (err) {
      console.error('Failed to delete A/B test:', err)
      setApiError('Failed to delete A/B test.')
    }
  }

  useEffect(() => {
    if (backendReachable) {
      axios.get(`${API_URL}/api/v1/videos`)
        .then(res => {
          if (res.data?.videos) {
            setVideos(res.data.videos)
            if (res.data.videos.length > 0 && !selectedVideo) {
              selectVideo(res.data.videos[0].id, res.data.videos)
            }
          }
        })
        .catch(err => console.error('Failed to load videos:', err))
    }
  }, [backendReachable])

  useEffect(() => {
    if (activeTab === 'abtesting') {
      fetchABTests()
    }
  }, [activeTab])

  const toggleCompare = (videoId: string) => {
    setCompareIds(prev => {
      if (prev.includes(videoId)) return prev.filter(id => id !== videoId)
      if (prev.length >= 2) return [prev[1], videoId]
      return [...prev, videoId]
    })
  }

  const goToComparison = () => {
    if (compareIds.length === 2) {
      router.push(`/comparison?a=${compareIds[0]}&b=${compareIds[1]}`)
    }
  }

  const handleRewriteScript = async (dimension: 'hook' | 'authenticity' | 'cta') => {
    if (!analysis) return
    setActiveRewriteDimension(dimension)
    setIsRewriting(true)
    setRewriteError(null)
    setRewriteResult(null)
    setShowRewriteModal(true)

    try {
      const res = await axios.post(
        `${API_URL}/api/v1/analyze/rewrite`,
        {
          video_id: selectedVideo || undefined,
          script: analysis.full_transcript || analysis.transcript || undefined,
          dimension: dimension,
          additional_instructions: additionalInstructions || undefined,
        },
        { timeout: 30000 }
      )
      setRewriteResult(res.data)
    } catch (err: any) {
      console.error('Script rewrite failed:', err)
      setRewriteError(err.response?.data?.detail || 'Script rewrite failed. Please check backend log or try again.')
    } finally {
      setIsRewriting(false)
    }
  }

  const applyRewrittenScript = () => {
    if (!rewriteResult?.rewritten_script) return
    setScriptText(rewriteResult.rewritten_script)
    setInputMode('script')
    setShowRewriteModal(false)
    const editorElement = document.getElementById('script-editor-container')
    if (editorElement) {
      editorElement.scrollIntoView({ behavior: 'smooth' })
    }
  }

  const pollAnalysis = async (videoId: string, file: File) => {
    pollAbortRef.current?.abort()
    pollAbortRef.current = new AbortController()
    const { signal } = pollAbortRef.current

    const maxAttempts = 60
    for (let i = 0; i < maxAttempts; i++) {
      if (signal.aborted) return
      try {
        const statusRes = await axios.get(`${API_URL}/status/${videoId}`, { timeout: 5000, signal })
        const s = statusRes.data
        setUploadProgress(s.progress || 0)
        setUploadStatusMsg(s.message || '')
        setUploadStage(s.stage || '')
        if (s.status === 'completed') {
          const analysisRes = await axios.get(`${API_URL}/analyses/${videoId}`, { timeout: 10000, signal })
          setAnalysis({ filename: file.name, ...analysisRes.data })
          setSelectedVideo(videoId)
          setVideos(prev => prev.map(v => v.id === videoId ? { ...v, status: 'analyzed' } : v))
          setUploading(false)
          return
        }
        if (s.status === 'error') {
          throw new Error(s.message || 'Analysis failed')
        }
      } catch (err: any) {
        if (axios.isCancel(err)) return
        if (err.message === 'Analysis failed') throw err
      }
      await new Promise(r => setTimeout(r, 1500))
    }
    throw new Error('Analysis timed out')
  }

  const handleUpload = async (file: File) => {
    if (!file) return
    setUploading(true)
    setUploadProgress(0)
    setUploadStatusMsg('Uploading...')
    setUploadStage('uploading')
    setApiError(null)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('user_id', guestSessionId || 'anonymous')
      
      const res = await axios.post(`${API_URL}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000
      })
      const videoId = res.data.video_id
      
      setVideos(prev => [...prev, {
        id: videoId,
        filename: file.name,
        upload_time: new Date().toISOString(),
        status: 'processing'
      }])
      setSelectedVideo(videoId)
      
      setUploadStatusMsg('Starting analysis...')
      await pollAnalysis(videoId, file)
    } catch (err: any) {
      console.error('Upload failed:', err)
      setDemoMode(true)
      const demoId = `demo_${Date.now()}`
      setVideos(prev => [...prev, {
        id: demoId, filename: file.name, upload_time: new Date().toISOString(), status: 'analyzed'
      }])
      setAnalysis({
        video_id: demoId, hook_score: 78,
        hook_details: { strength: 'Strong', curiosity_gap_detected: true, question_detected: true },
        authenticity_score: 72, authenticity_details: { authenticity_level: 'High', brand_intrusion: 'Low' },
        sentiment_forecast: { positive_sentiment_pct: 62.5, negative_sentiment_pct: 7.2, neutral_sentiment_pct: 30.3, backlash_risk: 'Low', shareability_index: 78, sellout_probability: 23 },
        cta_analysis: { cta_activation_score: 75, cognitive_load: 'Optimal', timing_recommendation: 'Current placement optimal' },
        viral_potential: 72, success_probability: 74, risk_score: 16,
        recommendations: ['Strong hook detected with curiosity gap - good viral potential', 'High authenticity score - content feels natural', 'CTA at 8s mark should perform well'],
        mirofish_simulation: { simulation_id: 'sim_demo_001', final_sentiment: 68.5, viral_prediction: 'High - Positive sentiment spreading', backlash_prediction: 'Low risk - positive reception', share_prediction: 72, persona_distribution: { loyal_fan: 18, trend_seeker: 24, casual_viewer: 26, skeptic: 10, budget_shopper: 16, anti_ad: 6 }, comment_samples: [{ type: 'positive', persona: 'trend_seeker', comment: 'sharing this! everyone needs to see this', sentiment: 0.82 }, { type: 'neutral', persona: 'casual_viewer', comment: 'interesting', sentiment: 0.55 }, { type: 'positive', persona: 'loyal_fan', comment: 'omg love this!', sentiment: 0.91 }], trust_trajectory: [65, 68, 70, 72, 74, 76, 78] },
        analysis_response: { cortical_response: { visual_cortex: 78, auditory_cortex: 72, language_center: 68, amygdala: 65, prefrontal_cortex: 70, reward_center: 82, social_cognition: 62, memory_formation: 68, overall_response_strength: 72 }, emotional_impact: { primary_emotion: 'excitement', emotional_intensity: 72 }, engagement_prediction: { overall_engagement: 78, retention_prediction: 'high' }, mode: 'simulated' },
        stage_gate: { passed: true, W_attn: 0.72, threshold: 0.4 }
      })
      setSelectedVideo(demoId)
      const errorMsg = err.code === 'ECONNABORTED' ? 'Backend timeout. Ensure NeuroSim is running on localhost:8001' : err.response ? `Backend error (${err.response.status})` : 'Cannot reach backend. Run NeuroSim on localhost:8001'
      setApiError(`Demo Mode - ${errorMsg}`)
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

  const handleScriptAnalyze = async () => {
    if (!scriptText.trim()) {
      setScriptError('Please enter your script text.')
      return
    }
    if (scriptText.trim().length < 50) {
      setScriptError('Script too short. Minimum 50 characters for meaningful analysis.')
      return
    }
    setScriptError(null)
    setAnalyzingScript(true)
    setApiError(null)

    try {
      const res = await axios.post(
        `${API_URL}/api/v1/analyze/script`,
        { script: scriptText.trim(), title: scriptTitle || undefined },
        { timeout: 30000 },
      )
      const scriptId = res.data.video_id
      setAnalysis({ filename: scriptTitle || 'Script Analysis', ...res.data })
      setSelectedVideo(scriptId)
      setVideos(prev => [...prev, {
        id: scriptId,
        filename: scriptTitle || 'Script Analysis',
        upload_time: new Date().toISOString(),
        status: 'analyzed',
      }])
      setScriptText('')
      setScriptTitle('')
    } catch (err: any) {
      console.error('Script analysis failed:', err)
      const errorMsg = err.response?.data?.detail || 'Analysis failed. Please try again.'
      setScriptError(errorMsg)
      if (err.response?.status === 429 || err.response?.status === 403) {
        setDemoMode(true)
        const demoId = `demo_${Date.now()}`
        setVideos(prev => [...prev, {
          id: demoId, filename: scriptTitle || 'Script Analysis', upload_time: new Date().toISOString(), status: 'analyzed'
        }])
        setAnalysis({
          video_id: demoId, hook_score: 78,
          hook_details: { strength: 'Strong', curiosity_gap_detected: true, question_detected: true },
          authenticity_score: 72, authenticity_details: { authenticity_level: 'High', brand_intrusion: 'Low' },
          sentiment_forecast: { positive_sentiment_pct: 62.5, negative_sentiment_pct: 7.2, neutral_sentiment_pct: 30.3, backlash_risk: 'Low', shareability_index: 78, sellout_probability: 23 },
          cta_analysis: { cta_activation_score: 75, cognitive_load: 'Optimal', timing_recommendation: 'Current placement optimal' },
          viral_potential: 72, success_probability: 74, risk_score: 16,
          recommendations: ['Strong hook detected with curiosity gap - good viral potential', 'High authenticity score - content feels natural', 'CTA at 8s mark should perform well'],
          mirofish_simulation: { simulation_id: 'sim_demo_001', final_sentiment: 68.5, viral_prediction: 'High - Positive sentiment spreading', backlash_prediction: 'Low risk - positive reception', share_prediction: 72, persona_distribution: { loyal_fan: 18, trend_seeker: 24, casual_viewer: 26, skeptic: 10, budget_shopper: 16, anti_ad: 6 }, comment_samples: [{ type: 'positive', persona: 'trend_seeker', comment: 'sharing this! everyone needs to see this', sentiment: 0.82 }, { type: 'neutral', persona: 'casual_viewer', comment: 'interesting', sentiment: 0.55 }, { type: 'positive', persona: 'loyal_fan', comment: 'omg love this!', sentiment: 0.91 }], trust_trajectory: [65, 68, 70, 72, 74, 76, 78] },
          analysis_response: { cortical_response: { visual_cortex: 78, auditory_cortex: 72, language_center: 68, amygdala: 65, prefrontal_cortex: 70, reward_center: 82, social_cognition: 62, memory_formation: 68, overall_response_strength: 72 }, emotional_impact: { primary_emotion: 'excitement', emotional_intensity: 72 }, engagement_prediction: { overall_engagement: 78, retention_prediction: 'high' }, mode: 'simulated' },
          stage_gate: { passed: true, W_attn: 0.72, threshold: 0.4 },
          analysis_type: 'script',
          source: 'text_input',
        })
        setSelectedVideo(demoId)
        setScriptText('')
        setScriptTitle('')
      }
    } finally {
      setAnalyzingScript(false)
    }
  }

  const handleYoutubeAnalyze = async () => {
    if (!youtubeUrl.trim()) {
      setYoutubeError('Please enter a YouTube URL.')
      return
    }
    const ytRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|embed\/)|youtu\.be\/)/
    if (!ytRegex.test(youtubeUrl.trim())) {
      setYoutubeError('Invalid YouTube URL. Use youtube.com or youtu.be links.')
      return
    }
    setYoutubeError(null)
    setAnalyzingYoutube(true)
    setApiError(null)

    try {
      const res = await axios.post(
        `${API_URL}/api/v1/analyze/youtube`,
        { url: youtubeUrl.trim() },
        { timeout: 60000 },
      )
      const ytId = res.data.video_id || `yt_${Date.now()}`
      setAnalysis({ filename: res.data.script_title || 'YouTube Analysis', ...res.data })
      setSelectedVideo(ytId)
      setVideos(prev => [...prev, {
        id: ytId,
        filename: res.data.script_title || 'YouTube Analysis',
        upload_time: new Date().toISOString(),
        status: 'analyzed',
      }])
      setYoutubeUrl('')
    } catch (err: any) {
      console.error('YouTube analysis failed:', err)
      const errorMsg = err.response?.data?.detail || 'Analysis failed. Video may not have captions.'
      setYoutubeError(errorMsg)
    } finally {
      setAnalyzingYoutube(false)
    }
  }

  const runABTest = async () => {
    if (!abBaselineVideoId) {
      setApiError('Please select a baseline video from your history.')
      return
    }
    setAbTestRunning(true)
    setApiError(null)
    
    try {
      const payload: any = {
        name: abTestName || `A/B Test ${new Date().toLocaleDateString()}`,
        baseline_video_id: abBaselineVideoId,
      }
      
      if (abCompareMode === 'video') {
        if (!abVariantVideoId) {
          setApiError('Please select a variant video to compare.')
          setAbTestRunning(false)
          return
        }
        payload.variant_video_id = abVariantVideoId
      } else {
        if (!abVariantScript.trim()) {
          setApiError('Please write or generate a variant script in the smart editor.')
          setAbTestRunning(false)
          return
        }
        payload.variant_script = abVariantScript
      }

      const res = await axios.post(`${API_URL}/api/v1/ab-tests`, payload)
      const data = res.data
      setAbResults(data.results)
      setSelectedAbTestId(data.id)
      
      // Refresh historical comparative list
      await fetchABTests()
    } catch (err: any) {
      console.error('A/B test execution failed:', err)
      const errorMsg = err.response?.data?.detail || 'A/B test failed. Ensure both baseline and variant videos are fully analyzed.'
      setApiError(errorMsg)
    } finally {
      setAbTestRunning(false)
    }
  }

  const runWhatIf = async () => {
    if (!selectedVideo) return
    setWhatIfRunning(true)
    setApiError(null)

    const mods: Record<string, any> = {}
    if (whatIfMods.emotional_tone) mods.emotional_tone = true
    if (whatIfMods.earlier_product_mention) mods.earlier_product_mention = true
    if (whatIfMods.aggressive_cta) mods.aggressive_cta = true
    if (whatIfMods.price_decrease > 0) mods.price_decrease = whatIfMods.price_decrease

    try {
      const res = await axios.post(
        `${API_URL}/simulation/what-if/${selectedVideo}`,
        { modifications: mods },
        { timeout: 10000 },
      )
      setWhatIfResult(res.data)
    } catch (err: any) {
      console.error('What-if failed:', err)
      setApiError('What-if simulation failed. Ensure you have an analysis first.')
    } finally {
      setWhatIfRunning(false)
    }
  }

  const submitValidation = async () => {
    if (!selectedVideo) return
    try {
      await axios.post(`${API_URL}/api/v1/validation/submit`, {
        video_id: selectedVideo,
        actual_views: parseInt(validationData.views) || 0,
        actual_engagement: parseFloat(validationData.engagement) || 0,
        would_publish: true,
        days_after_publish: parseInt(validationData.days) || 7,
      })
      setValidationSubmitted(true)
    } catch (err: any) {
      console.error('Validation submit failed:', err)
      setApiError('Failed to submit validation data.')
    }
  }

  const loadBenchmark = async () => {
    if (!selectedVideo) return
    try {
      const res = await axios.post(`${API_URL}/api/v1/benchmarks/compare`, {
        video_id: selectedVideo,
        cohort: benchmarkCohort,
      })
      setBenchmarkData(res.data)
    } catch (err: any) {
      console.error('Benchmark load failed:', err)
      setApiError('Failed to load benchmark data.')
    }
  }

  const loadComparison = async (videoId: string) => {
    setLoadingComparison(true)
    setCompareData(null)
    try {
      const res = await axios.get(`${API_URL}/api/v1/analyses/${videoId}/compare`)
      setCompareData(res.data)
    } catch (err: any) {
      console.error('Comparison load failed:', err)
      setCompareData({ error: err?.response?.data?.detail || 'Failed to load comparison data.' })
    } finally {
      setLoadingComparison(false)
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
      analysis_response: {
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

  const handleShare = async () => {
    if (!selectedVideo) return
    setSharing(true)
    try {
      const res = await axios.post(`${API_URL}/api/v1/share`, { video_id: selectedVideo })
      setShareUrl(`${window.location.origin}/r/${res.data.share_id}`)
      setShowShareModal(true)
    } catch (err) {
      console.error('Share failed:', err)
    } finally {
      setSharing(false)
    }
  }

  const handleCopyLink = () => {
    navigator.clipboard.writeText(shareUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const downloadPDF = async () => {
    if (!selectedVideo) return
    try {
      const res = await fetch(`${API_URL}/reports/${selectedVideo}/pdf`)
      if (!res.ok) throw new Error('Failed to generate PDF')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `neurosim_report_${selectedVideo.slice(0, 8)}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('PDF download failed:', err)
    }
  }

  const radarData = useMemo(() => analysis ? [
    { subject: 'Hook', value: analysis.hook_score || 0, fullMark: 100 },
    { subject: 'Authenticity', value: analysis.authenticity_score || 0, fullMark: 100 },
    { subject: 'Viral', value: analysis.viral_potential || 0, fullMark: 100 },
    { subject: 'CTA', value: analysis.cta_analysis?.cta_activation_score || 0, fullMark: 100 },
    { subject: 'Share', value: analysis.sentiment_forecast?.shareability_index || 0, fullMark: 100 },
  ] : [], [analysis])

  return (
    <div className="min-h-screen bg-neural neural-grid">
      <OnboardingTour onComplete={() => setOnboardingComplete(true)} />
      <main className="max-w-7xl mx-auto px-6 py-8 relative z-10">
        {/* Hero - asymmetric composition */}
        <div className="mb-10">
          <div className="flex items-end justify-between mb-8">
            <div className="max-w-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[11px] mono text-neural mb-3 tracking-wider uppercase">Predictive Content Intelligence</p>
                  <h2 className="text-4xl font-bold text-white mb-4 leading-tight">
                    Measure neural response<br />
                    <span className="text-text-tertiary">before you publish.</span>
                  </h2>
                </div>
                <UsageCounter />
              </div>
              <p className="text-text-secondary text-sm max-w-md">
                Analyze before you film. Paste a script for instant predictions,
                or upload a video for full neural analysis + swarm simulation.
              </p>
            </div>
          </div>

          {/* Upload Zone - hero element, asymmetric */}
          <div id="script-editor-container" className="glass-panel-elevated p-8 min-h-[180px]">
            {/* Input mode toggle */}
            <div className="flex items-center gap-1 p-1 bg-white/[0.03] rounded-lg w-fit mb-6">
              <button
                onClick={() => setInputMode('upload')}
                className={`px-4 py-2 rounded-md text-xs font-medium transition-all flex items-center gap-2 ${
                  inputMode === 'upload'
                    ? 'bg-neural/15 text-neural border border-neural/20'
                    : 'text-text-tertiary hover:text-white'
                }`}
              >
                <Upload className="w-3.5 h-3.5" /> Upload Video
              </button>
              <button
                onClick={() => setInputMode('script')}
                className={`px-4 py-2 rounded-md text-xs font-medium transition-all flex items-center gap-2 ${
                  inputMode === 'script'
                    ? 'bg-neural/15 text-neural border border-neural/20'
                    : 'text-text-tertiary hover:text-white'
                }`}
              >
                <FileText className="w-3.5 h-3.5" /> Paste Script
              </button>
              <button
                onClick={() => setInputMode('youtube')}
                className={`px-4 py-2 rounded-md text-xs font-medium transition-all flex items-center gap-2 ${
                  inputMode === 'youtube'
                    ? 'bg-neural/15 text-neural border border-neural/20'
                    : 'text-text-tertiary hover:text-white'
                }`}
              >
                <Youtube className="w-3.5 h-3.5" /> YouTube URL
              </button>
            </div>

            {inputMode === 'upload' ? (
              /* Video upload mode */
              <div
                className={`p-8 flex flex-col items-center justify-center gap-5 min-h-[140px] cursor-pointer glass-interactive rounded-xl border-2 border-dashed ${
                  dragActive ? 'border-neural/40 bg-neural/5' : 'border-white/[0.06]'
                }`}
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
                    whileHover={hoverLift.whileHover}
                    whileTap={tapPress.whileTap}
                  >
                    {uploading ? (
                      <div className="relative w-14 h-14 rounded-xl bg-neural/10 border border-neural/20 flex items-center justify-center">
                        <svg className="w-14 h-14 -rotate-90 absolute" viewBox="0 0 36 36">
                          <circle cx="18" cy="18" r="15.5" fill="none" stroke="rgba(77,238,234,0.15)" strokeWidth="2"/>
                          <circle cx="18" cy="18" r="15.5" fill="none" stroke="#4deeea" strokeWidth="2" strokeDasharray={`${uploadProgress * 0.97} 97`} strokeLinecap="round"/>
                        </svg>
                        <span className="text-xs mono text-neural font-bold">{uploadProgress}%</span>
                      </div>
                    ) : (
                      <Upload className="w-6 h-6 text-neural" />
                    )}
                  </motion.div>
                  <div className="text-center">
                    <p className="text-white font-medium text-base mb-1">
                      {uploading ? (uploadStatusMsg || 'Analyzing...') : 'Drop video to analyze'}
                    </p>
                    <p className="text-text-tertiary text-xs mono">
                      MP4, MOV, AVI, WebM &bull; Up to 2GB
                    </p>
                    {uploading && uploadStage && (
                      <div className="flex items-center gap-2 mt-3">
                        <ProgressStageIndicator
                          currentStage={uploadStage}
                          accent="neural"
                        />
                      </div>
                    )}
                  </div>
                </label>
              </div>
            ) : inputMode === 'script' ? (
              /* Script input mode */
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Script title (optional)"
                  value={scriptTitle}
                  onChange={(e) => setScriptTitle(e.target.value)}
                  className="w-full p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/30 transition-colors"
                />
                <textarea
                  placeholder="Paste your video script here... (minimum 50 characters)"
                  value={scriptText}
                  onChange={(e) => {
                    setScriptText(e.target.value)
                    if (scriptError) setScriptError(null)
                  }}
                  rows={8}
                  className="w-full p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/30 transition-colors resize-y font-mono leading-relaxed"
                />
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`text-xs mono ${
                      scriptText.length >= 50 ? 'text-green-400' : 'text-text-tertiary'
                    }`}>
                      {scriptText.length} chars
                    </span>
                    {scriptText.length > 0 && scriptText.length < 50 && (
                      <span className="text-xs text-orange-400">
                        {50 - scriptText.length} more needed
                      </span>
                    )}
                  </div>
                  <motion.button
                    onClick={handleScriptAnalyze}
                    disabled={analyzingScript || !scriptText.trim()}
                    className="btn-neural flex items-center gap-2 text-sm px-6 py-2.5 disabled:opacity-40 disabled:cursor-not-allowed"
                    whileHover={!analyzingScript && scriptText.trim() ? { scale: 1.02 } : {}}
                    whileTap={!analyzingScript && scriptText.trim() ? { scale: 0.98 } : {}}
                  >
                    {analyzingScript ? (
                      <>
                        <div className="w-4 h-4 border-2 border-neural border-t-transparent rounded-full animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Scan className="w-4 h-4" />
                        Analyze Script
                      </>
                    )}
                  </motion.button>
                </div>
                {scriptError && (
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-orange-400/10 border border-orange-400/20">
                    <AlertTriangle className="w-4 h-4 text-orange-400 flex-shrink-0" />
                    <p className="text-xs text-orange-400">{scriptError}</p>
                  </div>
                )}
              </div>
            ) : inputMode === 'youtube' ? (
              /* YouTube URL input mode */
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="https://www.youtube.com/watch?v=... or https://youtu.be/..."
                  value={youtubeUrl}
                  onChange={(e) => {
                    setYoutubeUrl(e.target.value)
                    if (youtubeError) setYoutubeError(null)
                  }}
                  className="w-full p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/30 transition-colors font-mono"
                />
                <div className="flex items-center justify-between">
                  <p className="text-xs text-text-tertiary">
                    Extracts transcript and runs full neural analysis
                  </p>
                  <motion.button
                    onClick={handleYoutubeAnalyze}
                    disabled={analyzingYoutube || !youtubeUrl.trim()}
                    className="btn-neural flex items-center gap-2 text-sm px-6 py-2.5 disabled:opacity-40 disabled:cursor-not-allowed"
                    whileHover={!analyzingYoutube && youtubeUrl.trim() ? { scale: 1.02 } : {}}
                    whileTap={!analyzingYoutube && youtubeUrl.trim() ? { scale: 0.98 } : {}}
                  >
                    {analyzingYoutube ? (
                      <>
                        <div className="w-4 h-4 border-2 border-neural border-t-transparent rounded-full animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Youtube className="w-4 h-4" />
                        Analyze Video
                      </>
                    )}
                  </motion.button>
                </div>
                {youtubeError && (
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-orange-400/10 border border-orange-400/20">
                    <AlertTriangle className="w-4 h-4 text-orange-400 flex-shrink-0" />
                    <p className="text-xs text-orange-400">{youtubeError}</p>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>

        {apiError && (
          <div className="glass-panel p-4 mb-4 border border-signal-orange/30">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-signal-orange" />
              <p className="text-sm text-text-primary">{apiError}</p>
            </div>
            <button
              onClick={() => setApiError(null)}
              className="btn-ghost mt-2 text-sm"
            >
              Try Again
            </button>
          </div>
        )}

        {isSignedIn && typeof window !== 'undefined' && localStorage.getItem('neurosim_guest_id') && (
          <div className="glass-panel p-4 mb-4 border border-neural/30">
            <p className="text-sm text-text-primary">
              You have videos from a previous guest session.{' '}
              <button onClick={recoverGuestSession} className="text-neural underline">
                Merge them into your account
              </button>
            </p>
          </div>
        )}

        {/* Stats - inline, minimal */}
        {videos.length > 0 && (
          <div className="flex items-center gap-6 mb-8 stagger flex-wrap">
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

        {/* Main Content - tabbed layout */}
        {analysis && (
          <div>
            {/* Tab switcher */}
            <div className="flex items-center gap-1 p-1 bg-white/[0.03] rounded-lg w-fit mb-6">
              <button
                onClick={() => setActiveTab('overview')}
                className={`px-4 py-2 rounded-md text-xs font-medium transition-all flex items-center gap-2 ${
                  activeTab === 'overview'
                    ? 'bg-neural/15 text-neural border border-neural/20'
                    : 'text-text-tertiary hover:text-white'
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" /> Overview
              </button>
              <button
                onClick={() => setActiveTab('analysis')}
                className={`px-4 py-2 rounded-md text-xs font-medium transition-all flex items-center gap-2 ${
                  activeTab === 'analysis'
                    ? 'bg-neural/15 text-neural border border-neural/20'
                    : 'text-text-tertiary hover:text-white'
                }`}
              >
                <Brain className="w-3.5 h-3.5" /> Analysis
              </button>
              <button
                onClick={() => setActiveTab('abtesting')}
                className={`px-4 py-2 rounded-md text-xs font-medium transition-all flex items-center gap-2 ${
                  activeTab === 'abtesting'
                    ? 'bg-neural/15 text-neural border border-neural/20'
                    : 'text-text-tertiary hover:text-white'
                }`}
              >
                <Zap className="w-3.5 h-3.5" /> A/B Testing
              </button>
              <button
                onClick={() => { setActiveTab('llm_compare'); if (selectedVideo) loadComparison(selectedVideo) }}
                className={`px-4 py-2 rounded-md text-xs font-medium transition-all flex items-center gap-2 ${
                  activeTab === 'llm_compare'
                    ? 'bg-purple-500/15 text-purple-400 border border-purple-500/20'
                    : 'text-text-tertiary hover:text-white'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" /> LLM Compare
              </button>
              <button
                onClick={() => setActiveTab('feed_simulator')}
                className={`px-4 py-2 rounded-md text-xs font-medium transition-all flex items-center gap-2 ${
                  activeTab === 'feed_simulator'
                    ? 'bg-neural/15 text-neural border border-neural/20'
                    : 'text-text-tertiary hover:text-white'
                }`}
              >
                <Play className="w-3.5 h-3.5" /> Social Feed
              </button>
            </div>

            <AnimatePresence mode="wait">
              {activeTab === 'overview' && (
                <motion.div
                  key="analysis"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={tabSwitch}
                  className="grid grid-cols-1 lg:grid-cols-8 gap-6"
                >
                  {/* Left column - main content (8 cols on lg) */}
                  <div className="lg:col-span-5 space-y-6">
                  {/* 3D Brain Heatmap (desktop) / 2D Scorecard (mobile) */}
                  {isMobile ? (
                    <div className="glass-panel p-5">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                          <Brain className="w-4 h-4 text-neural" />
                          <h4 className="text-sm font-semibold text-white">Content Analysis</h4>
                        </div>
                        <span className={`badge ${analysis.analysis_response?.mode === 'real' ? 'badge-neural' : 'badge-ghost'}`}>
                          {analysis.analysis_response?.mode === 'real' ? 'REAL' : 'EARLY ESTIMATE'}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        {[
                          { label: 'Visual Cortex', value: analysis.analysis_response?.cortical_response?.visual_cortex || 0 },
                          { label: 'Auditory Cortex', value: analysis.analysis_response?.cortical_response?.auditory_cortex || 0 },
                          { label: 'Language Center', value: analysis.analysis_response?.cortical_response?.language_center || 0 },
                          { label: 'Amygdala', value: analysis.analysis_response?.cortical_response?.amygdala || 0 },
                          { label: 'Prefrontal', value: analysis.analysis_response?.cortical_response?.prefrontal_cortex || 0 },
                          { label: 'Reward Center', value: analysis.analysis_response?.cortical_response?.reward_center || 0 },
                        ].map(item => (
                          <div key={item.label} className="p-3 rounded-lg bg-white/[0.02]">
                            <p className="text-[10px] mono text-text-tertiary mb-1">{item.label}</p>
                            <p className="text-lg font-bold mono text-neural">{item.value.toFixed(1)}%</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <Suspense fallback={<div className="w-full h-[300px] glass-panel flex items-center justify-center"><div className="w-6 h-6 border-2 border-neural border-t-transparent rounded-full animate-spin" /></div>}>
                      <Brain3D brainData={analysis.analysis_response} />
                    </Suspense>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="glass-panel p-5">
                      <div className="flex items-center justify-between mb-5">
                        <div className="flex items-center gap-2">
                          <Brain className="w-4 h-4 text-neural" />
                          <h4 className="text-sm font-semibold text-white">Content Analysis</h4>
                        </div>
                        <span className={`badge ${analysis.analysis_response?.mode === 'real' ? 'badge-neural' : 'badge-ghost'}`}>
                          {analysis.analysis_response?.mode === 'real' ? 'REAL' : 'EARLY ESTIMATE'}
                        </span>
                      </div>
                      <DashboardRadar radarData={radarData} />
                    </div>

                    <div className="glass-panel p-5">
                      <div className="flex items-center justify-between mb-5">
                        <div className="flex items-center gap-2">
                          <MessageSquare className="w-4 h-4 text-swarm" />
                          <h4 className="text-sm font-semibold text-white">Sentiment</h4>
                        </div>
                        <span className={`badge ${analysis.mirofish_simulation?.mode === 'real' ? 'badge-swarm' : 'badge-ghost'}`}>
                          {analysis.mirofish_simulation?.mode === 'real' ? 'REAL' : 'EARLY ESTIMATE'}
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

                  {!feedbackSubmitted && (
                    <div className="glass-panel p-5">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-semibold text-white mb-1">How did this video perform?</h4>
                          <p className="text-xs text-text-tertiary">Share actual results to help us improve predictions.</p>
                        </div>
                        <button
                          onClick={() => setShowFeedbackForm(true)}
                          className="btn-ghost text-sm flex items-center gap-1"
                        >
                          <MessageSquare className="w-3 h-3" />
                          Share Results
                        </button>
                      </div>
                    </div>
                  )}

                  {feedbackSubmitted && (
                    <div className="glass-panel p-5 border-neural/20">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-neural" />
                        <p className="text-sm text-text-secondary">Thanks! Your data helps improve predictions for everyone.</p>
                      </div>
                    </div>
                  )}

                  {/* What-If Simulation */}
                  <div className="glass-panel p-5">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <Sliders className="w-4 h-4 text-swarm" />
                        <h4 className="text-sm font-semibold text-white">What-If Simulation</h4>
                      </div>
                      <span className={`text-[10px] mono ${analysis.mirofish_simulation?.mode === 'real' ? 'text-neural' : 'text-amber-400/70'}`}>
                        {analysis.mirofish_simulation?.mode === 'real' ? 'REAL' : 'SIM'}
                      </span>
                    </div>
                    <div className="space-y-3">
                      <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
                        <input type="checkbox" checked={whatIfMods.emotional_tone} onChange={(e) => setWhatIfMods({ ...whatIfMods, emotional_tone: e.target.checked })} className="rounded bg-white/[0.04] border-white/[0.08] text-neural focus:ring-0" />
                        More emotional tone
                      </label>
                      <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
                        <input type="checkbox" checked={whatIfMods.earlier_product_mention} onChange={(e) => setWhatIfMods({ ...whatIfMods, earlier_product_mention: e.target.checked })} className="rounded bg-white/[0.04] border-white/[0.08] text-neural focus:ring-0" />
                        Earlier product mention
                      </label>
                      <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
                        <input type="checkbox" checked={whatIfMods.aggressive_cta} onChange={(e) => setWhatIfMods({ ...whatIfMods, aggressive_cta: e.target.checked })} className="rounded bg-white/[0.04] border-white/[0.08] text-neural focus:ring-0" />
                        More aggressive CTA
                      </label>
                      <div className="flex items-center gap-3 pt-1">
                        <span className="text-xs text-text-tertiary">Price decrease:</span>
                        <input type="range" min="0" max="50" value={whatIfMods.price_decrease} onChange={(e) => setWhatIfMods({ ...whatIfMods, price_decrease: parseInt(e.target.value) })} className="flex-1" />
                        <span className="text-xs mono text-white w-8">{whatIfMods.price_decrease}%</span>
                      </div>
                      <motion.button onClick={runWhatIf} disabled={whatIfRunning || !selectedVideo} className="btn-swarm text-xs py-2 px-4 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2" whileHover={!whatIfRunning ? { scale: 1.02 } : {}} whileTap={!whatIfRunning ? { scale: 0.98 } : {}}>
                        {whatIfRunning ? (<><div className="w-3 h-3 border-2 border-swarm border-t-transparent rounded-full animate-spin" />Running...</>) : (<><Sliders className="w-3.5 h-3.5" />Run What-If</>)}
                      </motion.button>
                    </div>
                    {whatIfResult && (
                      <div className="mt-4 p-4 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                        <p className="text-xs mono text-text-tertiary mb-2">Results</p>
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div><p className="text-text-tertiary">Sentiment</p><p className="text-white mono text-lg">{whatIfResult.final_sentiment?.toFixed(1) || '--'}</p></div>
                          <div><p className="text-text-tertiary">Viral</p><p className="text-swarm mono text-sm">{whatIfResult.viral_prediction || '--'}</p></div>
                          <div><p className="text-text-tertiary">Share</p><p className="text-white mono text-lg">{whatIfResult.share_prediction || '--'}</p></div>
                          <div><p className="text-text-tertiary">Backlash</p><p className="text-white mono text-sm">{whatIfResult.backlash_prediction || '--'}</p></div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Validation Study */}
                  {!validationSubmitted && (
                    <div className="glass-panel p-5">
                      <div className="flex items-center gap-2 mb-4">
                        <Target className="w-4 h-4 text-neural" />
                        <h4 className="text-sm font-semibold text-white">Validate Prediction</h4>
                      </div>
                      <p className="text-xs text-text-tertiary mb-4">Submit actual performance data to improve accuracy.</p>
                      <div className="space-y-3">
                        <input type="number" value={validationData.views} onChange={(e) => setValidationData({ ...validationData, views: e.target.value })} placeholder="Actual views" className="w-full p-2.5 rounded-lg bg-white/[0.03] border border-white/[0.06] text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/30" />
                        <input type="number" step="0.1" value={validationData.engagement} onChange={(e) => setValidationData({ ...validationData, engagement: e.target.value })} placeholder="Engagement %" className="w-full p-2.5 rounded-lg bg-white/[0.03] border border-white/[0.06] text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/30" />
                        <button onClick={submitValidation} className="w-full btn-neural text-xs py-2.5 flex items-center justify-center gap-2"><Target className="w-3.5 h-3.5" />Submit Validation</button>
                      </div>
                    </div>
                  )}
                  {validationSubmitted && (
                    <div className="glass-panel p-5 border-neural/20">
                      <div className="flex items-center gap-2"><CheckCircle className="w-4 h-4 text-neural" /><p className="text-sm text-text-secondary">Validation data submitted!</p></div>
                    </div>
                  )}

                  {/* Benchmark Comparison */}
                  <div className="glass-panel p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <TrendingUp className="w-4 h-4 text-swarm" />
                      <h4 className="text-sm font-semibold text-white">Benchmark</h4>
                    </div>
                    <div className="flex items-center gap-3 mb-3">
                      <select value={benchmarkCohort} onChange={(e) => setBenchmarkCohort(e.target.value)} className="flex-1 p-2.5 rounded-lg bg-white/[0.03] border border-white/[0.06] text-sm text-white focus:outline-none focus:border-neural/30">
                        <option value="all">All Videos</option>
                        <option value="education">Education</option>
                        <option value="entertainment">Entertainment</option>
                        <option value="gaming">Gaming</option>
                        <option value="music">Music</option>
                      </select>
                      <button onClick={loadBenchmark} disabled={!selectedVideo} className="btn-swarm text-xs py-2 px-4 disabled:opacity-40 disabled:cursor-not-allowed">Compare</button>
                    </div>
                    {benchmarkData && (
                      <div className="space-y-2">
                        <p className="text-xs mono text-text-tertiary">vs {benchmarkData.cohort} (n={benchmarkData.cohort_n})</p>
                        {Object.entries(benchmarkData.comparison || {}).map(([key, val]: [string, any]) => (
                          <div key={key} className="flex items-center justify-between text-xs">
                            <span className="text-text-tertiary">{key.replace(/_/g, ' ')}</span>
                            <span className={`mono ${val.percentile >= 50 ? 'text-neural' : 'text-orange-400'}`}>P{val.percentile}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  </div>

                  {/* Right column - sidebar */}
                  <div className="lg:col-span-3 space-y-4">
                    {/* Active Models */}
                    <div className="glass-panel p-4">
                      <h4 className="text-[10px] mono text-text-tertiary uppercase tracking-wider mb-3">Systems</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02]">
                          <div className="flex items-center gap-2">
                            <span className="status-dot status-neural"></span>
                            <div>
                              <span className="text-xs text-white font-medium">Neural</span>
                              <p className="text-[10px] text-text-tertiary">Encoding</p>
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
                      <div className="glass-panel p-4 max-h-[300px] overflow-y-auto">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-[10px] mono text-text-tertiary uppercase tracking-wider">Recent</h4>
                          {compareIds.length === 2 && (
                            <button onClick={goToComparison} className="text-[10px] mono text-neural hover:underline cursor-pointer">
                              Compare →
                            </button>
                          )}
                        </div>
                        <div className="space-y-1.5">
                          {videos.slice(-5).reverse().map(video => (
                            <div 
                              key={video.id}
                              className="p-2.5 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors cursor-pointer flex items-center gap-2"
                              onClick={() => selectVideo(video.id)}
                            >
                              <input
                                type="checkbox"
                                checked={compareIds.includes(video.id)}
                                onChange={e => { e.stopPropagation(); toggleCompare(video.id) }}
                                onClick={e => e.stopPropagation()}
                                className="w-3 h-3 rounded bg-white/[0.04] border border-white/[0.08] text-neural focus:ring-0 cursor-pointer"
                              />
                              <div className="flex-1 min-w-0">
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
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}

              {activeTab === 'analysis' && (
                <motion.div
                  key="analysis-workspace"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={tabSwitch}
                  className="grid grid-cols-1 lg:grid-cols-8 gap-6"
                >
                  {/* Left Hand Side - Original Full Transcript (5 columns) */}
                  <div className="lg:col-span-5 flex flex-col space-y-4">
                    <div className="glass-panel p-6 flex flex-col h-[580px]">
                      <div className="flex items-center justify-between pb-4 border-b border-white/[0.06] mb-4">
                        <div className="flex items-center gap-2.5">
                          <div className="p-2 rounded-lg bg-neural/10 text-neural border border-neural/20">
                            <FileText className="w-4 h-4" />
                          </div>
                          <div>
                            <h3 className="text-sm font-semibold text-white">Original Script / Transcript</h3>
                            <p className="text-[10px] text-text-tertiary">Read and analyze the raw narrative data</p>
                          </div>
                        </div>
                        <span className="badge badge-neural mono text-[10px]">
                          {analysis.full_transcript ? 'FULL' : 'TRUNCATED'}
                        </span>
                      </div>
                      
                      {/* Script Reader Body */}
                      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                        <p className="text-sm text-text-secondary whitespace-pre-wrap font-mono leading-relaxed bg-white/[0.01] p-4 rounded-xl border border-white/[0.03] select-text">
                          {analysis.full_transcript || analysis.transcript || "No script text found."}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Right Hand Side - Premium Script Doctors & Settings (3 columns) */}
                  <div className="lg:col-span-3 space-y-4 flex flex-col">
                    {/* Settings card */}
                    <div className="glass-panel p-5 space-y-4">
                      <div className="flex items-center gap-2">
                        <Sliders className="w-4 h-4 text-neural" />
                        <h4 className="text-sm font-semibold text-white">AI Co-Pilot Settings</h4>
                      </div>
                      <div>
                        <label className="text-xs text-text-secondary block mb-1.5 font-medium">Custom Rewrite Context (Optional)</label>
                        <textarea
                          placeholder="e.g. 'Make the tone more aggressive', 'Focus on product benefits', 'Make it super relatable'..."
                          value={additionalInstructions}
                          onChange={(e) => setAdditionalInstructions(e.target.value)}
                          rows={3}
                          className="w-full p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] text-xs text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/30 transition-colors resize-none font-mono leading-relaxed"
                        />
                      </div>
                    </div>

                    {/* Boost Cards */}
                    <div className="space-y-3">
                      {/* Card 1: Hook Doctor */}
                      <div className="glass-panel-elevated p-5 flex flex-col justify-between hover:border-neural/20 transition-all group">
                        <div className="mb-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Brain className="w-4 h-4 text-neural" />
                              <h4 className="text-xs font-semibold text-white uppercase tracking-wider">Hook Doctor</h4>
                            </div>
                            <span className="text-[10px] bg-neural/10 text-neural border border-neural/20 px-2 py-0.5 rounded mono">Target: Opening 3s</span>
                          </div>
                          <p className="text-xs text-text-secondary leading-relaxed">
                            Injects high-impact pattern interrupts and curiosity loops in the opening 3 seconds of the video to hook viewer attention and maximize LO/A5 scores.
                          </p>
                        </div>
                        <button
                          onClick={() => handleRewriteScript('hook')}
                          className="w-full btn-neural text-xs py-2.5 flex items-center justify-center gap-2 group-hover:scale-[1.01] transition-transform"
                        >
                          <Sparkles className="w-3.5 h-3.5" /> Boost Hook Retention
                        </button>
                      </div>

                      {/* Card 2: Authenticity Calibrator */}
                      <div className="glass-panel-elevated p-5 flex flex-col justify-between hover:border-swarm/20 transition-all group">
                        <div className="mb-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Users className="w-4 h-4 text-swarm" />
                              <h4 className="text-xs font-semibold text-white uppercase tracking-wider">Authenticity Calibrator</h4>
                            </div>
                            <span className="text-[10px] bg-swarm/10 text-swarm border border-swarm/20 px-2 py-0.5 rounded mono">Target: TPJ / Area45</span>
                          </div>
                          <p className="text-xs text-text-secondary leading-relaxed">
                            Strips corporate speech and sales-heavy words. Calibrates narrative copy to a conversational, peer-to-peer, vulnerable tone that viewers trust.
                          </p>
                        </div>
                        <button
                          onClick={() => handleRewriteScript('authenticity')}
                          className="w-full btn-swarm text-xs py-2.5 flex items-center justify-center gap-2 group-hover:scale-[1.01] transition-transform"
                        >
                          <Sparkles className="w-3.5 h-3.5" /> Calibrate Authenticity
                        </button>
                      </div>

                      {/* Card 3: CTA Amplifier */}
                      <div className="glass-panel-elevated p-5 flex flex-col justify-between hover:border-purple-500/20 transition-all group">
                        <div className="mb-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Zap className="w-4 h-4 text-purple-400" />
                              <h4 className="text-xs font-semibold text-white uppercase tracking-wider">CTA Amplifier</h4>
                            </div>
                            <span className="text-[10px] bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded mono">Target: Conversion</span>
                          </div>
                          <p className="text-xs text-text-secondary leading-relaxed">
                            Reframes your final call to action to reduce friction, clearly map benefits, and integrate smoothly into the script's visual payoff.
                          </p>
                        </div>
                        <button
                          onClick={() => handleRewriteScript('cta')}
                          className="w-full bg-purple-600 hover:bg-purple-500 text-white text-xs py-2.5 rounded-lg flex items-center justify-center gap-2 border border-purple-500/20 font-semibold group-hover:scale-[1.01] transition-transform"
                        >
                          <Sparkles className="w-3.5 h-3.5" /> Amplify Call-to-Action
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {activeTab === 'abtesting' && (
                <motion.div 
                  key="abtesting"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={tabSwitch}
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
                      <p className="text-text-tertiary text-xs mono">Neural ΓåÆ ROI ΓåÆ MiroFish Swarm</p>
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
                      </div>                        {abResults.version_a.social && abResults.version_b.social && (
                        <div className="glass-panel p-5">
                          <h4 className="text-sm font-semibold text-white mb-4">7-Day Propagation</h4>
                          <DashboardABAreaChart abResults={abResults} />
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

              {activeTab === 'llm_compare' && (
                <motion.div
                  key="llm_compare"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={tabSwitch}
                  className="space-y-6"
                >
                  <div className="glass-panel p-6">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                          <Sparkles className="w-4 h-4" />
                        </div>
                        <div>
                          <h3 className="text-sm font-semibold text-white">LLM vs Heuristic Score Comparison</h3>
                          <p className="text-[10px] text-text-tertiary">Gemini 2.5 Flash evaluates the same content for deeper ROI insights</p>
                        </div>
                      </div>
                      <button
                        onClick={() => selectedVideo && loadComparison(selectedVideo)}
                        className="btn-ghost text-xs flex items-center gap-1.5"
                        disabled={loadingComparison}
                      >
                        <RefreshCw className={`w-3 h-3 ${loadingComparison ? 'animate-spin' : ''}`} />
                        Refresh
                      </button>
                    </div>

                    {loadingComparison && (
                      <div className="py-16 flex flex-col items-center justify-center">
                        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mb-3" />
                        <p className="text-xs text-text-tertiary mono">Analyzing with Gemini 2.5 Flash...</p>
                      </div>
                    )}

                    {!loadingComparison && compareData?.error && (
                      <div className="glass-panel p-4 border border-signal-orange/30">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-signal-orange" />
                          <p className="text-sm text-text-primary">{compareData.error}</p>
                        </div>
                      </div>
                    )}

                    {!loadingComparison && compareData?.llm_mode === 'disabled' && (
                      <div className="py-12 flex flex-col items-center justify-center text-center">
                        <div className="p-3 rounded-full bg-white/[0.03] border border-white/[0.06] mb-4">
                          <Sparkles className="w-8 h-8 text-text-tertiary" />
                        </div>
                        <p className="text-sm text-text-secondary mb-1">LLM Scorer Not Available</p>
                        <p className="text-xs text-text-tertiary max-w-md">
                          The Gemini API key is not configured. LLM-powered scoring requires a GEMINI_API_KEY
                          to be set on the backend.
                        </p>
                      </div>
                    )}

                    {!loadingComparison && compareData?.llm && (
                      <div className="space-y-6">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                          {['A5', 'LO', 'Area45', 'TPJ'].map((dim) => {
                            const hVal = compareData.heuristic?.[dim] ?? 0
                            const lVal = compareData.llm?.[dim] ?? 0
                            const delta = compareData.deltas?.[dim] ?? 0
                            const isHigher = delta > 0
                            const isLower = delta < 0

                            return (
                              <div key={dim} className="glass-panel-elevated p-5">
                                <div className="flex items-center justify-between mb-3">
                                  <span className="text-xs font-semibold text-white uppercase tracking-wider">{dim}</span>
                                  <span className={`text-[10px] mono px-2 py-0.5 rounded ${isHigher ? 'bg-green-500/10 text-green-400 border border-green-500/20' : isLower ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-white/[0.03] text-text-tertiary border border-white/[0.06]'}`}>
                                    {isHigher ? `+${delta.toFixed(3)}` : isLower ? delta.toFixed(3) : '—'}
                                  </span>
                                </div>

                                <div className="space-y-3">
                                  <div>
                                    <div className="flex justify-between text-[11px] mb-1">
                                      <span className="text-text-tertiary">Heuristic</span>
                                      <span className="mono text-white font-medium">{(hVal * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="progress-track h-2">
                                      <div className="progress-fill progress-neural h-full rounded" style={{ width: `${hVal * 100}%` }} />
                                    </div>
                                  </div>

                                  <div>
                                    <div className="flex justify-between text-[11px] mb-1">
                                      <span className="text-text-tertiary">LLM (Gemini)</span>
                                      <span className="mono text-purple-400 font-medium">{(lVal * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="progress-track h-2">
                                      <div className="progress-fill h-full rounded" style={{ width: `${lVal * 100}%`, background: 'linear-gradient(90deg, #a855f7, #c084fc)' }} />
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )
                          })}
                        </div>

                        {compareData.llm_rationale && (
                          <div className="glass-panel p-5">
                            <div className="flex items-center gap-2 mb-3">
                              <MessageSquare className="w-4 h-4 text-purple-400" />
                              <h4 className="text-xs font-semibold text-white uppercase tracking-wider">LLM Rationale</h4>
                            </div>
                            <p className="text-xs text-text-secondary leading-relaxed">{compareData.llm_rationale}</p>
                          </div>
                        )}

                        <div className="glass-panel p-4 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-text-tertiary" />
                            <span className="text-xs text-text-tertiary">Transcript word count</span>
                          </div>
                          <span className="mono text-white text-xs">{compareData.transcript_word_count?.toLocaleString()}</span>
                        </div>
                      </div>
                    )}

                    {!loadingComparison && !compareData && (
                      <div className="py-12 flex flex-col items-center justify-center text-center">
                        <div className="p-3 rounded-full bg-white/[0.03] border border-white/[0.06] mb-4">
                          <Sparkles className="w-8 h-8 text-text-tertiary" />
                        </div>
                        <p className="text-sm text-text-secondary mb-1">No comparison data loaded</p>
                        <p className="text-xs text-text-tertiary">Select a video and click Refresh to load the comparison.</p>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}

              {activeTab === 'feed_simulator' && (
                <motion.div
                  key="feed_simulator"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={tabSwitch}
                  className="space-y-6"
                >
                  <SimulatedPhone video_id={selectedVideo || ''} analysis={analysis} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </main>

      {showShareModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowShareModal(false)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative w-full max-w-md mx-4 rounded-2xl border border-white/[0.08] bg-[#0a0a0a] shadow-2xl p-6"
          >
            <button onClick={() => setShowShareModal(false)} className="absolute top-4 right-4 text-text-tertiary hover:text-white cursor-pointer">
              <X className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-swarm/10 border border-swarm/20 flex items-center justify-center">
                <Share2 className="w-5 h-5 text-swarm" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Share Analysis</h3>
                <p className="text-sm text-text-tertiary">Anyone with this link can view</p>
              </div>
            </div>
            <div className="flex items-center gap-2 p-3 rounded-xl bg-white/[0.04] border border-white/[0.08]">
              <input
                type="text"
                readOnly
                value={shareUrl}
                className="flex-1 bg-transparent text-sm text-white focus:outline-none"
              />
              <button
                onClick={handleCopyLink}
                className="p-2 rounded-lg bg-neural/10 border border-neural/20 text-neural hover:bg-neural/20 transition-colors cursor-pointer"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
            {copied && (
              <p className="text-xs text-green-400 mt-2 text-center">Copied to clipboard!</p>
            )}
          </motion.div>
        </div>
      )}

      {showFeedbackForm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowFeedbackForm(false)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative w-full max-w-md mx-4 rounded-2xl border border-white/[0.08] bg-[#0a0a0a] shadow-2xl p-6"
          >
            <button onClick={() => setShowFeedbackForm(false)} className="absolute top-4 right-4 text-text-tertiary hover:text-white cursor-pointer">
              <X className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-neural/10 border border-neural/20 flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-neural" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Video Performance</h3>
                <p className="text-sm text-text-tertiary">Help us improve predictions</p>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-text-secondary mb-1 block">Actual Views</label>
                <input
                  type="number"
                  value={feedbackData.views}
                  onChange={(e) => setFeedbackData({ ...feedbackData, views: e.target.value })}
                  placeholder="e.g. 15000"
                  className="w-full p-3 rounded-xl bg-white/[0.04] border border-white/[0.08] text-sm text-white focus:outline-none focus:border-neural/40"
                />
              </div>
              <div>
                <label className="text-xs text-text-secondary mb-1 block">Engagement Rate (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={feedbackData.engagement}
                  onChange={(e) => setFeedbackData({ ...feedbackData, engagement: e.target.value })}
                  placeholder="e.g. 4.2"
                  className="w-full p-3 rounded-xl bg-white/[0.04] border border-white/[0.08] text-sm text-white focus:outline-none focus:border-neural/40"
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.04] border border-white/[0.08]">
                <span className="text-sm text-text-secondary">Would you publish this?</span>
                <button
                  onClick={() => setFeedbackData({ ...feedbackData, wouldPublish: !feedbackData.wouldPublish })}
                  className={`w-12 h-6 rounded-full transition-colors ${feedbackData.wouldPublish ? 'bg-neural' : 'bg-white/20'}`}
                >
                  <div className={`w-5 h-5 rounded-full bg-white shadow transition-transform ${feedbackData.wouldPublish ? 'translate-x-6' : 'translate-x-0.5'}`} />
                </button>
              </div>
              <button
                onClick={async () => {
                  if (!selectedVideo) return
                  try {
                    await fetch(`${API_URL}/api/v1/feedback`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        video_id: selectedVideo,
                        actual_views: parseInt(feedbackData.views) || 0,
                        actual_engagement: parseFloat(feedbackData.engagement) || 0,
                        would_publish: feedbackData.wouldPublish,
                      }),
                    })
                    setFeedbackSubmitted(true)
                  } catch {
                    console.error('Failed to submit feedback')
                  }
                  setShowFeedbackForm(false)
                }}
                className="w-full btn-neural py-3"
              >
                Submit Feedback
              </button>
            </div>
          </motion.div>
        </div>
      )}
      {showRewriteModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/75 backdrop-blur-md" onClick={() => !isRewriting && setShowRewriteModal(false)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative w-full max-w-5xl rounded-2xl border border-white/[0.08] bg-[#0c0c0e] shadow-2xl p-6 overflow-hidden max-h-[90vh] flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.06] mb-6 flex-shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-neural/10 border border-neural/20 flex items-center justify-center text-neural">
                  <Sparkles className="w-5 h-5 animate-pulse" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    AI Script Rewrite Co-Pilot 
                    <span className="text-xs bg-neural/10 text-neural border border-neural/20 px-2 py-0.5 rounded uppercase mono">
                      {activeRewriteDimension}
                    </span>
                  </h3>
                  <p className="text-xs text-text-tertiary">Side-by-side comparison of original vs optimized script</p>
                </div>
              </div>
              {!isRewriting && (
                <button 
                  onClick={() => setShowRewriteModal(false)} 
                  className="w-8 h-8 rounded-lg hover:bg-white/5 flex items-center justify-center text-text-tertiary hover:text-white transition-colors cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Modal Body Content */}
            <div className="flex-1 overflow-y-auto min-h-0 space-y-6 pr-2 custom-scrollbar">
              {isRewriting ? (
                /* Scanning / Loading Skeletons */
                <div className="space-y-6 py-8 flex flex-col items-center justify-center">
                  <div className="relative">
                    <div className="w-16 h-16 rounded-full border border-neural/30 flex items-center justify-center bg-neural/5 animate-pulse">
                      <Brain className="w-8 h-8 text-neural animate-bounce" />
                    </div>
                    <div className="absolute inset-0 border-2 border-neural border-t-transparent rounded-full animate-spin" />
                  </div>
                  <div className="space-y-2 text-center max-w-sm">
                    <h4 className="text-sm font-semibold text-white">Synthesizing Boosted Narrative...</h4>
                    <p className="text-xs text-text-tertiary animate-pulse">
                      {activeRewriteDimension === 'hook' && "Pattern-interrupting opening hooks being crafted..."}
                      {activeRewriteDimension === 'authenticity' && "Calibrating conversational flow and stripping corporate speak..."}
                      {activeRewriteDimension === 'cta' && "Structuring frictionless action call and mapping value payoffs..."}
                    </p>
                  </div>

                  {/* Dummy side-by-side skeletons */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full mt-4">
                    <div className="glass-panel p-4 space-y-3 h-[250px] animate-pulse">
                      <div className="h-3 w-1/4 bg-white/10 rounded" />
                      <div className="h-2 w-full bg-white/5 rounded" />
                      <div className="h-2 w-5/6 bg-white/5 rounded" />
                      <div className="h-2 w-4/5 bg-white/5 rounded" />
                    </div>
                    <div className="glass-panel p-4 space-y-3 h-[250px] animate-pulse">
                      <div className="h-3 w-1/4 bg-neural/10 rounded animate-pulse" />
                      <div className="h-2 w-full bg-neural/5 rounded animate-pulse" />
                      <div className="h-2 w-5/6 bg-neural/5 rounded animate-pulse" />
                      <div className="h-2 w-4/5 bg-neural/5 rounded animate-pulse" />
                    </div>
                  </div>
                </div>
              ) : rewriteError ? (
                /* Error display */
                <div className="glass-panel border-red-500/20 bg-red-500/[0.02] p-6 text-center space-y-4">
                  <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 mx-auto flex items-center justify-center text-red-400">
                    <AlertTriangle className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-sm font-semibold text-white">Rewrite Failed</h4>
                    <p className="text-xs text-text-secondary max-w-md mx-auto leading-relaxed">{rewriteError}</p>
                  </div>
                  <button 
                    onClick={() => setShowRewriteModal(false)} 
                    className="btn-ghost text-xs px-4 py-2"
                  >
                    Close Modal
                  </button>
                </div>
              ) : rewriteResult ? (
                /* Success Comparison Layout */
                <div className="space-y-6">
                  {/* Side-by-Side Editor Panels */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Left - Original */}
                    <div className="flex flex-col space-y-2">
                      <div className="flex items-center justify-between text-xs px-1">
                        <span className="font-semibold text-text-secondary uppercase tracking-wider">Original Script</span>
                        <span className="text-[10px] text-text-tertiary mono">Original Text</span>
                      </div>
                      <div className="glass-panel p-4 bg-white/[0.01] h-[280px] overflow-y-auto">
                        <p className="text-xs font-mono text-text-secondary whitespace-pre-wrap leading-relaxed select-text">
                          {analysis.full_transcript || analysis.transcript || "No original script found."}
                        </p>
                      </div>
                    </div>

                    {/* Right - Boosted */}
                    <div className="flex flex-col space-y-2">
                      <div className="flex items-center justify-between text-xs px-1">
                        <span className="font-semibold text-neural uppercase tracking-wider flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5" /> Boosted Optimization
                        </span>
                          <span className="text-[10px] text-neural mono">AI Vision</span>
                      </div>
                      <div className="glass-panel p-4 bg-neural/[0.02] border-neural/20 h-[280px] overflow-y-auto ring-1 ring-neural/10">
                        <p className="text-xs font-mono text-neural-light whitespace-pre-wrap leading-relaxed select-text">
                          {rewriteResult.rewritten_script}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Impact Evaluation Scorecard & explanation */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Scores Comparison */}
                    <div className="glass-panel p-4 bg-white/[0.01] flex flex-col justify-center items-center text-center">
                      <p className="text-[10px] uppercase font-bold text-text-tertiary mb-3 tracking-wider">Score Projection</p>
                      <div className="flex items-center gap-4">
                        <div>
                          <p className="text-2xl font-black text-text-tertiary mono">
                            {rewriteResult.estimated_improvements?.before_score || 50}
                          </p>
                          <p className="text-[9px] text-text-tertiary uppercase">Before</p>
                        </div>
                        <ChevronRight className="w-5 h-5 text-text-tertiary" />
                        <div className="bg-neural/10 border border-neural/20 px-4 py-2 rounded-xl">
                          <p className="text-3xl font-black text-neural mono animate-pulse">
                            {rewriteResult.estimated_improvements?.after_score || 85}
                          </p>
                          <p className="text-[9px] text-neural uppercase font-bold">Projected</p>
                        </div>
                      </div>
                      <p className="text-[10px] text-text-tertiary mt-4 leading-relaxed italic">
                        "{rewriteResult.estimated_improvements?.rationale || "AI optimized metric projection"}"
                      </p>
                    </div>

                    {/* Change explanation card (spans 2 cols) */}
                    <div className="glass-panel p-4 bg-white/[0.01] md:col-span-2 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center gap-1.5 mb-2.5">
                          <Brain className="w-4 h-4 text-neural" />
                          <p className="text-xs uppercase font-bold text-white tracking-wider">Doctor's Explanation</p>
                        </div>
                        <p className="text-xs text-text-secondary leading-relaxed">
                          {rewriteResult.explanation || "No explanation provided."}
                        </p>
                      </div>
                      <div className="text-[10px] text-text-tertiary pt-3 border-t border-white/[0.04] mt-3">
                        Applying this rewrite will copy the script into your main editor draft workspace.
                      </div>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>

            {/* Actions Footer */}
            {!isRewriting && (
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/[0.06] mt-6 flex-shrink-0">
                <button
                  onClick={() => setShowRewriteModal(false)}
                  className="btn-ghost text-xs px-4 py-2.5"
                >
                  Discard & Close
                </button>
                {rewriteResult && (
                  <button
                    onClick={applyRewrittenScript}
                    className="btn-neural text-xs px-6 py-2.5 flex items-center gap-2"
                  >
                    <Check className="w-4 h-4" /> Apply Rewritten Script
                  </button>
                )}
              </div>
            )}
          </motion.div>
        </div>
      )}
    </div>
  )
}
