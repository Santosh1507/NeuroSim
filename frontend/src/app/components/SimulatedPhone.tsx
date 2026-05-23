'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { easeOutExpo, easeSmooth, micro } from '../../lib/easing'
import {
  Smartphone, Volume2, Flame, RefreshCw, AlertCircle,
  TrendingUp, RotateCcw, Trash2, Compass, Hash, Music, Play, Pause,
  ChevronRight, ArrowUpRight, Zap, Activity
} from 'lucide-react'
import {
  AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip,
  ResponsiveContainer, LineChart, Line, ReferenceLine
} from 'recharts'

interface SimulatedPhoneProps {
  video_id: string
  analysis: any
}

export default function SimulatedPhone({ video_id, analysis }: SimulatedPhoneProps) {
  const [platform, setPlatform] = useState<'tiktok' | 'shorts' | 'reels'>('tiktok')
  const [soundTrend, setSoundTrend] = useState<number>(0.5)
  const [isPlaying, setIsPlaying] = useState<boolean>(true)
  const [currentSecond, setCurrentSecond] = useState<number>(0)
  const [simulation, setSimulation] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<any[]>([])

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

  // Fetch simulation from backend
  const runSimulation = useCallback(async (plat = platform, trend = soundTrend) => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.post(`${API_URL}/api/v1/simulation/social-feed`, {
        video_id,
        platform: plat,
        sound_trend_factor: trend
      })
      setSimulation(res.data)
      // Refresh history list
      const histRes = await axios.get(`${API_URL}/api/v1/simulation/social-feed/history/${video_id}`)
      setHistory(histRes.data)
    } catch (err: any) {
      console.error(err)
      setError(err?.response?.data?.detail || 'Failed to simulate social feed metrics.')
    } finally {
      setLoading(false)
    }
  }, [video_id, platform, soundTrend, API_URL])

  // Run simulation on mount, platform change, or soundTrend adjustment
  useEffect(() => {
    runSimulation()
  }, [platform])

  // Custom debounced trend update
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      runSimulation(platform, soundTrend)
    }, 600)
    return () => clearTimeout(delayDebounce)
  }, [soundTrend])

  // Handle play/pause and time scrubbing
  useEffect(() => {
    let interval: any = null
    if (isPlaying && simulation?.retention_data?.retention_curve) {
      const maxSeconds = simulation.retention_data.retention_curve.length - 1
      interval = setInterval(() => {
        setCurrentSecond((prev) => (prev >= maxSeconds ? 0 : prev + 1))
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [isPlaying, simulation])

  const deleteSim = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await axios.delete(`${API_URL}/api/v1/simulation/social-feed/${id}`)
      setHistory(prev => prev.filter(item => item.id !== id))
      if (simulation?.id === id) {
        setSimulation(null)
      }
    } catch (err) {
      console.error('Delete simulation failed', err)
    }
  }

  // Pre-calculate colors based on platform
  const theme = useMemo(() => {
    switch (platform) {
      case 'tiktok':
        return {
          glow: 'shadow-[0_0_20px_rgba(77,238,234,0.35)]',
          border: 'border-[#4deeea]/30',
          accent: '#4deeea',
          bgGradient: 'from-[#112233] via-[#05111d] to-[#01070c]',
          textColor: 'text-[#4deeea]',
          badgeBg: 'bg-[#4deeea]/10',
          iconColor: '#4deeea'
        }
      case 'shorts':
        return {
          glow: 'shadow-[0_0_20px_rgba(239,68,68,0.35)]',
          border: 'border-red-500/30',
          accent: '#ef4444',
          bgGradient: 'from-[#2e0909] via-[#140202] to-[#080000]',
          textColor: 'text-red-500',
          badgeBg: 'bg-red-500/10',
          iconColor: '#ef4444'
        }
      case 'reels':
        return {
          glow: 'shadow-[0_0_20px_rgba(236,72,153,0.35)]',
          border: 'border-pink-500/30',
          accent: '#ec4899',
          bgGradient: 'from-[#2b0c20] via-[#10030b] to-[#040003]',
          textColor: 'text-pink-500',
          badgeBg: 'bg-pink-500/10',
          iconColor: '#ec4899'
        }
    }
  }, [platform])

  const curveData = useMemo(() => {
    if (!simulation?.retention_data?.retention_curve) return []
    const retCurve = simulation.retention_data.retention_curve
    const velCurve = simulation.retention_data.velocity_curve
    return retCurve.map((val: number, i: number) => ({
      second: i,
      retention: Math.round(val * 100),
      velocity: velCurve[i] || 0
    }))
  }, [simulation])

  // Check if there is an alert at the active second
  const currentAlert = useMemo(() => {
    if (!simulation?.retention_data?.alerts) return null
    return simulation.retention_data.alerts.find((a: any) => a.second === currentSecond)
  }, [simulation, currentSecond])

  return (
    <div className="space-y-8">
      {/* Simulation Setup and Platform Selection */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-5 glass-panel">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Compass className="w-4 h-4 text-neural" />
            Social Feed Simulator Engine
          </h3>
          <p className="text-xs text-text-tertiary mt-1">
            Simulate retention, choose-to-watch thresholds, and scroll velocities across platform algorithms.
          </p>
        </div>

        {/* Platform tabs with rich micro-animations */}
        <div className="flex items-center gap-1.5 p-1 bg-white/[0.02] border border-white/[0.04] rounded-lg" role="tablist" aria-label="Platform selection">
          <button
            onClick={() => { setPlatform('tiktok'); setCurrentSecond(0); }}
            role="tab"
            aria-selected={platform === 'tiktok'}
            aria-label="TikTok"
            className={`px-4 py-2 rounded-md text-xs font-semibold flex items-center gap-2 transition-[all] duration-300 ease-[var(--ease-smooth)] ${
              platform === 'tiktok'
                ? 'bg-[#4deeea]/15 text-[#4deeea] border border-[#4deeea]/30 shadow-[0_0_12px_rgba(77,238,234,0.15)] scale-[1.03]'
                : 'text-text-tertiary hover:text-white hover:bg-white/[0.03]'
            }`}
          >
            <Hash className="w-3.5 h-3.5" />
            TikTok Preset
          </button>
          <button
            onClick={() => { setPlatform('shorts'); setCurrentSecond(0); }}
            role="tab"
            aria-selected={platform === 'shorts'}
            aria-label="YouTube Shorts"
            className={`px-4 py-2 rounded-md text-xs font-semibold flex items-center gap-2 transition-[all] duration-300 ease-[var(--ease-smooth)] ${
              platform === 'shorts'
                ? 'bg-red-500/15 text-red-400 border border-red-500/30 shadow-[0_0_12px_rgba(239,68,68,0.15)] scale-[1.03]'
                : 'text-text-tertiary hover:text-white hover:bg-white/[0.03]'
            }`}
          >
            <Play className="w-3.5 h-3.5" />
            YouTube Shorts
          </button>
          <button
            onClick={() => { setPlatform('reels'); setCurrentSecond(0); }}
            role="tab"
            aria-selected={platform === 'reels'}
            aria-label="Instagram Reels"
            className={`px-4 py-2 rounded-md text-xs font-semibold flex items-center gap-2 transition-[all] duration-300 ease-[var(--ease-smooth)] ${
              platform === 'reels'
                ? 'bg-pink-500/15 text-pink-400 border border-pink-500/30 shadow-[0_0_12px_rgba(236,72,153,0.15)] scale-[1.03]'
                : 'text-text-tertiary hover:text-white hover:bg-white/[0.03]'
            }`}
          >
            <Volume2 className="w-3.5 h-3.5" />
            Instagram Reels Preset
          </button>
        </div>
      </div>

      {loading && !simulation ? (
        <div className="h-[400px] flex flex-col items-center justify-center glass-panel">
          <div className="w-8 h-8 border-2 border-neural border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-xs text-text-tertiary">Computing micro-social behavioral models...</p>
        </div>
      ) : error ? (
        <div className="p-6 glass-panel flex flex-col items-center justify-center text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-red-400 animate-pulse" />
          <p className="text-sm font-medium text-white">{error}</p>
          <button
            onClick={() => runSimulation()}
            className="px-4 py-1.5 rounded-md bg-white/[0.05] border border-white/[0.08] hover:bg-white/[0.1] text-xs text-white flex items-center gap-2 transition-[all] duration-150 ease-[var(--ease-smooth)]"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry Simulation
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* LEFT: Premium Smartphone Chassis */}
          <div className="lg:col-span-4 flex justify-center">
            <div className={`relative w-[280px] h-[550px] bg-black rounded-[42px] border-8 border-[#1f2937] shadow-2xl overflow-hidden ${theme.glow} transition-[shadow] duration-500 ease-[var(--ease-out-expo)]`}>
              
              {/* Camera Notch / Dynamic Island */}
              <div className="absolute top-3 left-1/2 transform -translate-x-1/2 w-28 h-5 bg-black rounded-full z-30 flex items-center justify-center">
                <div className="w-2.5 h-2.5 bg-[#0d0d11] rounded-full border border-gray-800" />
              </div>

              {/* Status bar */}
              <div className="absolute top-0 inset-x-0 h-10 px-6 pt-2 z-20 flex justify-between items-center text-[10px] font-medium text-white/80">
                <span>19:46</span>
                <div className="flex items-center gap-1.5">
                  <Volume2 className="w-3 h-3" />
                  <div className="w-5 h-2.5 border border-white/60 rounded-sm p-[1px] flex items-center">
                    <div className="h-full w-4 bg-white rounded-[1px]" />
                  </div>
                </div>
              </div>

              {/* Simulator Screen */}
              <div className={`absolute inset-0 bg-gradient-to-b ${theme.bgGradient} flex flex-col justify-between p-5 pt-12 pb-6 z-10 transition-[colors] duration-500 ease-[var(--ease-smooth)]`}>
                
                {/* Simulated visual player canvas */}
                <div className="relative flex-1 bg-black/40 border border-white/[0.03] rounded-2xl flex flex-col items-center justify-center overflow-hidden p-4 group">
                  {/* Dynamic soundwaves/gradient wave acting as content */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-30 pointer-events-none">
                    <div className="w-36 h-36 rounded-full bg-gradient-to-tr from-purple-500 to-cyan-400 blur-2xl animate-pulse" />
                  </div>

                  {/* Dynamic animated visual bar spectrum depending on current play state */}
                  <div className="flex items-end gap-1.5 h-24 mb-4">
                    {Array.from({ length: 9 }).map((_, idx) => {
                      const baseH = [30, 60, 90, 110, 80, 50, 75, 45, 20][idx]
                      const activeH = isPlaying ? `calc(${baseH}px * (0.6 + 0.4 * ${Math.sin(currentSecond + idx)}))` : `${baseH * 0.4}px`
                      return (
                        <div
                          key={idx}
                          style={{ height: activeH, backgroundColor: theme.accent }}
                          className="w-1.5 rounded-full transition-[height] duration-300 ease-[var(--ease-smooth)] opacity-80"
                        />
                      )
                    })}
                  </div>

                  {/* Play/Pause state */}
                  <span className="text-[10px] font-bold tracking-widest text-white/60 uppercase mb-1">
                    PLAYBACK SECOND
                  </span>
                  <div className="text-4xl font-extrabold text-white tracking-tight flex items-baseline gap-1">
                    {currentSecond}s
                    <span className="text-xs text-text-tertiary font-medium">/ {analysis?.duration || 14}s</span>
                  </div>

                  {/* Playback Controls inside device */}
                  <div className="flex items-center gap-4 mt-6 z-20">
                    <button
                      onClick={() => setIsPlaying(!isPlaying)}
                      aria-label={isPlaying ? 'Pause simulation' : 'Play simulation'}
                      className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 flex items-center justify-center transition-[all] duration-150 ease-[var(--ease-smooth)]"
                    >
                      {isPlaying ? <Pause className="w-4 h-4 text-white" /> : <Play className="w-4 h-4 text-white fill-white" />}
                    </button>
                    <button
                      onClick={() => { setIsPlaying(false); setCurrentSecond(0); }}
                      aria-label="Reset playback"
                      className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 flex items-center justify-center transition-[all] duration-150 ease-[var(--ease-smooth)]"
                    >
                      <RotateCcw className="w-4 h-4 text-white" />
                    </button>
                  </div>
                </div>

                {/* Second-by-second warnings directly inside smartphone screen */}
                <div className="h-20 mt-4 flex items-center justify-center" aria-live="polite" aria-atomic="true">
                  <AnimatePresence mode="wait">
                    {currentAlert ? (
                      <motion.div
                        key={currentSecond}
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -12 }}
                        transition={easeSmooth}
                        className={`w-full p-2.5 rounded-xl border flex items-start gap-2 text-left ${
                          currentAlert.severity === 'critical' || currentAlert.severity === 'high'
                            ? 'bg-red-500/10 border-red-500/20 text-red-200'
                            : currentAlert.severity === 'medium'
                            ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-200'
                            : 'bg-blue-500/10 border-blue-500/20 text-blue-200'
                        }`}
                        role="alert"
                      >
                        <AlertCircle className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${
                          currentAlert.severity === 'critical' || currentAlert.severity === 'high'
                            ? 'text-red-400'
                            : currentAlert.severity === 'medium'
                            ? 'text-yellow-400'
                            : 'text-blue-400'
                        }`} />
                        <div className="text-[10px] leading-relaxed">
                          <p className="font-semibold capitalize text-white">Warning: {currentAlert.severity} Drop-off</p>
                          <p className="text-white/80">{currentAlert.message}</p>
                        </div>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="idle"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 0.6 }}
                        transition={easeSmooth}
                        className="text-center text-[10px] text-text-tertiary italic"
                      >
                        No active drop-off warning at second {currentSecond}.
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Bottom swipe velocity indicator */}
                <div className="border-t border-white/[0.04] pt-3 mt-1 flex items-center justify-between text-[10px]">
                  <span className="text-text-tertiary">Swipe Velocity:</span>
                  <span className="font-mono text-white flex items-center gap-1">
                    <Activity className="w-3 h-3 text-neural" />
                    {simulation?.retention_data?.velocity_curve?.[currentSecond] || 0} scrolls/min
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT: Live Scoreboard, Controls & Recharts */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* Stateful Scoreboard */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              
              <div className="p-4 glass-panel relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-white/[0.01] to-transparent pointer-events-none" />
                <span className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wider block">
                  Algorithmic Score
                </span>
                <div className="flex items-baseline gap-2 mt-2">
                  <span className="text-3xl font-extrabold text-white tracking-tight">
                    {simulation.algorithmic_score}
                  </span>
                  <span className="text-xs text-text-tertiary">/ 100</span>
                </div>
                <div className="w-full bg-white/[0.03] h-1.5 rounded-full mt-3 overflow-hidden">
                  <div
                    style={{ width: `${simulation.algorithmic_score}%`, backgroundColor: theme.accent }}
                    className="h-full rounded-full transition-[width] duration-1000 ease-[var(--ease-out-expo)]"
                  />
                </div>
              </div>

              <div className="p-4 glass-panel relative overflow-hidden group">
                <span className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wider block">
                  View-Through Rate (VTR)
                </span>
                <div className="flex items-baseline gap-2 mt-2">
                  <span className="text-3xl font-extrabold text-white tracking-tight">
                    {Math.round(simulation.vtr * 100)}%
                  </span>
                  <span className="text-xs text-text-tertiary">threshold</span>
                </div>
                <div className="w-full bg-white/[0.03] h-1.5 rounded-full mt-3 overflow-hidden">
                  <div
                    style={{ width: `${simulation.vtr * 100}%`, backgroundColor: '#4deeea' }}
                    className="h-full rounded-full transition-[width] duration-1000 ease-[var(--ease-out-expo)]"
                  />
                </div>
              </div>

              <div className="p-4 glass-panel relative overflow-hidden group">
                <span className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wider block">
                  Reach Multiplier
                </span>
                <div className="flex items-baseline gap-1 mt-2">
                  <span className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-1">
                    {simulation.retention_data.reach_multiplier}x
                  </span>
                </div>
                <p className="text-[9px] text-text-tertiary mt-4 flex items-center gap-1">
                  <TrendingUp className="w-3.5 h-3.5 text-[#4deeea]" />
                  Estimated reach booster
                </p>
              </div>

              <div className="p-4 glass-panel relative overflow-hidden group">
                {platform === 'tiktok' ? (
                  <>
                    <span className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wider block">
                      Estimated Loops
                    </span>
                    <div className="flex items-baseline gap-2 mt-2">
                      <span className="text-3xl font-extrabold text-white tracking-tight">
                        {simulation.retention_data.loop_count}x
                      </span>
                    </div>
                    <p className="text-[9px] text-text-tertiary mt-4">
                      Average replay frequency
                    </p>
                  </>
                ) : (
                  <>
                    <span className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wider block">
                      Sound Virality Boost
                    </span>
                    <div className="flex items-baseline gap-2 mt-2">
                      <span className="text-3xl font-extrabold text-white tracking-tight">
                        {Math.round(soundTrend * 100)}%
                      </span>
                    </div>
                    <p className="text-[9px] text-text-tertiary mt-4">
                      Shared trending modifier
                    </p>
                  </>
                )}
              </div>
            </div>

            {/* Simulated interactive trend sliders */}
            <div className="p-5 glass-panel">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                    <Music className="w-4 h-4 text-neural" />
                    Platform Audio Virality Multiplier
                  </h4>
                  <p className="text-[10px] text-text-tertiary mt-1">
                    Drag the modifier to simulate video placement when backed by trending background music.
                  </p>
                </div>
                <div className="flex items-center gap-3 w-full sm:w-72">
                  <span className="text-[10px] text-text-tertiary">Cold</span>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={soundTrend}
                    onChange={(e) => setSoundTrend(parseFloat(e.target.value))}
                    aria-label="Audio virality multiplier"
                    className="flex-1 accent-neural h-1 bg-white/10 rounded-lg appearance-none cursor-pointer"
                  />
                  <span className="text-[10px] font-semibold text-[#4deeea]">{Math.round(soundTrend * 100)}%</span>
                </div>
              </div>
            </div>

            {/* Recharts Area and Scroll charts */}
            <div className="p-5 glass-panel space-y-6">
              <div>
                <h4 className="text-xs font-bold text-white flex items-center gap-2">
                  <Activity className="w-4 h-4 text-neural animate-pulse" />
                  Time-Series Scroll Retention vs Velocity
                </h4>
                <p className="text-[10px] text-text-tertiary mt-1">
                  Compare scroll drop-offs and user swipe velocity second-by-second. Scrub the playhead to view local triggers.
                </p>
              </div>

              {/* Area Chart: Retention */}
              <div className="h-[180px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={curveData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <defs>
                      <linearGradient id="simGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={theme.accent} stopOpacity={0.2} />
                        <stop offset="95%" stopColor={theme.accent} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                    <XAxis dataKey="second" stroke="rgba(255,255,255,0.2)" fontSize={9} unit="s" />
                    <YAxis domain={[0, 100]} stroke="rgba(255,255,255,0.2)" fontSize={9} unit="%" />
                    <Tooltip
                      contentStyle={{ background: '#090a0f', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px' }}
                      labelStyle={{ color: '#fff', fontSize: '10px' }}
                      itemStyle={{ fontSize: '10px' }}
                    />
                    <Area
                      type="monotone"
                      dataKey="retention"
                      stroke={theme.accent}
                      fill="url(#simGrad)"
                      strokeWidth={1.8}
                      name="Retention"
                    />
                    {/* Scrubbing playhead line */}
                    <ReferenceLine x={currentSecond} stroke="#fff" strokeDasharray="3 3" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Line Chart: Swipe Velocity */}
              <div className="h-[120px] border-t border-white/[0.04] pt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={curveData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                    <XAxis dataKey="second" stroke="rgba(255,255,255,0.2)" fontSize={9} unit="s" />
                    <YAxis domain={[0, 90]} stroke="rgba(255,255,255,0.2)" fontSize={9} />
                    <Tooltip
                      contentStyle={{ background: '#090a0f', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px' }}
                      labelStyle={{ color: '#fff', fontSize: '10px' }}
                      itemStyle={{ fontSize: '10px' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="velocity"
                      stroke="#a78bfa"
                      strokeWidth={1.5}
                      dot={false}
                      name="Swipe Speed (scrolls/min)"
                    />
                    <ReferenceLine x={currentSecond} stroke="#fff" strokeDasharray="3 3" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Warnings list and past history */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Warnings List */}
              <div className="p-5 glass-panel">
                <h4 className="text-xs font-bold text-white mb-4 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400" />
                  Retention Warnings ({simulation?.retention_data?.alerts?.length || 0})
                </h4>
                <div className="space-y-2.5 max-h-[160px] overflow-y-auto pr-1">
                  {simulation?.retention_data?.alerts?.length > 0 ? (
                    simulation.retention_data.alerts.map((a: any, idx: number) => (
                      <button
                        key={idx}
                        onClick={() => { setCurrentSecond(a.second); setIsPlaying(false); }}
                        aria-label={`Jump to second ${a.second}: ${a.severity} alert - ${a.message}`}
                        className="w-full text-left p-2 rounded-lg bg-white/[0.01] hover:bg-white/[0.04] border border-white/[0.03] hover:border-white/[0.08] flex items-start justify-between gap-3 text-xs transition-[all] duration-150 ease-[var(--ease-smooth)]"
                      >
                        <div className="flex items-start gap-2">
                          <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold capitalize ${
                            a.severity === 'critical' || a.severity === 'high'
                              ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                              : a.severity === 'medium'
                              ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                              : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          }`}>
                            {a.severity}
                          </span>
                          <span className="text-white/80 leading-normal">{a.message}</span>
                        </div>
                        <span className="text-[10px] font-mono text-neural flex-shrink-0 flex items-center">
                          {a.second}s <ChevronRight className="w-3 h-3" />
                        </span>
                      </button>
                    ))
                  ) : (
                    <p className="text-[10px] text-text-tertiary italic text-center py-6">
                      No retention drop-off events found. Excellent hook alignment!
                    </p>
                  )}
                </div>
              </div>

              {/* Simulation Run History */}
              <div className="p-5 glass-panel">
                <h4 className="text-xs font-bold text-white mb-4 flex items-center gap-2">
                  <RotateCcw className="w-4 h-4 text-neural" />
                  Simulation Run History ({history.length})
                </h4>
                <div className="space-y-2 max-h-[160px] overflow-y-auto pr-1">
                  {history.length > 0 ? (
                    history.map((h: any, idx: number) => {
                      const hTheme = h.platform === 'tiktok' ? 'text-[#4deeea]' : h.platform === 'shorts' ? 'text-red-400' : 'text-pink-400'
                      return (
                        <div
                          key={idx}
                          onClick={() => { setPlatform(h.platform); setSimulation(h); }}
                          className={`w-full p-2.5 rounded-lg bg-white/[0.01] hover:bg-white/[0.04] border flex items-center justify-between text-xs cursor-pointer transition-[all] duration-150 ease-[var(--ease-smooth)] ${
                            simulation?.id === h.id ? 'border-neural/30 bg-neural/[0.02]' : 'border-white/[0.03]'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span className={`capitalize font-bold ${hTheme}`}>{h.platform}</span>
                            <span className="text-[10px] text-text-tertiary">Score: <strong className="text-white font-semibold">{h.algorithmic_score}</strong></span>
                            <span className="text-[10px] text-text-tertiary">VTR: <strong className="text-white font-semibold">{Math.round(h.vtr * 100)}%</strong></span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-[9px] text-text-tertiary font-mono">
                              {new Date(h.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                            <button
                              onClick={(e) => deleteSim(h.id, e)}
                              aria-label={`Delete simulation ${h.platform} from ${new Date(h.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
                              className="p-1 hover:bg-red-500/10 text-text-tertiary hover:text-red-400 rounded transition-[all] duration-150 ease-[var(--ease-smooth)]"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      )
                    })
                  ) : (
                    <p className="text-[10px] text-text-tertiary italic text-center py-6">
                      No simulations run yet for this video.
                    </p>
                  )}
                </div>
              </div>

            </div>

          </div>

        </div>
      )}
    </div>
  )
}
