'use client'

import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { Zap, Brain, Heart, TrendingUp, MessageSquare } from 'lucide-react'

export default function ComparisonSlider({
  analysisA,
  analysisB,
  labelA = 'Version A',
  labelB = 'Version B',
}: {
  analysisA: any
  analysisB: any
  labelA?: string
  labelB?: string
}) {
  const [sliderPos, setSliderPos] = useState(50)
  const containerRef = useRef<HTMLDivElement>(null)

  const handleMouseDown = () => {
    const handleMouseMove = (e: MouseEvent) => {
      const rect = containerRef.current?.getBoundingClientRect()
      if (rect) setSliderPos(Math.max(5, Math.min(95, ((e.clientX - rect.left) / rect.width) * 100)))
    }
    const handleMouseUp = () => { window.removeEventListener('mousemove', handleMouseMove); window.removeEventListener('mouseup', handleMouseUp) }
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
  }

  const scoreA = analysisA?.success_probability ?? 0
  const scoreB = analysisB?.success_probability ?? 0
  const winner = scoreA > scoreB ? 'A' : scoreB > scoreA ? 'B' : null

  const cardsA = [
    { label: 'Hook', value: analysisA?.hook_score ?? 0, accent: 'text-neural', bg: 'border-neural/20' },
    { label: 'Authenticity', value: analysisA?.authenticity_score ?? 0, accent: 'text-swarm', bg: 'border-swarm/20' },
    { label: 'Viral', value: analysisA?.viral_potential ?? 0, accent: 'text-orange-400', bg: 'border-orange-400/20' },
    { label: 'Success', value: scoreA, accent: 'text-green-400', bg: 'border-green-400/20' },
  ]
  const cardsB = [
    { label: 'Hook', value: analysisB?.hook_score ?? 0, accent: 'text-neural', bg: 'border-neural/20' },
    { label: 'Authenticity', value: analysisB?.authenticity_score ?? 0, accent: 'text-swarm', bg: 'border-swarm/20' },
    { label: 'Viral', value: analysisB?.viral_potential ?? 0, accent: 'text-orange-400', bg: 'border-orange-400/20' },
    { label: 'Success', value: scoreB, accent: 'text-green-400', bg: 'border-green-400/20' },
  ]

  const icons = [Brain, Heart, TrendingUp, MessageSquare]

  const ScoreColumn = ({ cards, side }: { cards: typeof cardsA; side: 'A' | 'B' }) => (
    <div className="flex flex-col items-center justify-center gap-3 h-full px-6">
      {cards.map((c, i) => {
        const Icon = icons[i]
        return (
          <div
            key={c.label}
            className={`glass-panel w-full max-w-[160px] px-4 py-2.5 border ${winner === side ? 'border-green-500/20 bg-green-500/5' : c.bg}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <Icon className={`w-3 h-3 ${c.accent}`} />
              <span className="text-[10px] mono text-text-tertiary">{c.label}</span>
            </div>
            <p className={`text-2xl font-bold mono ${winner === side ? 'text-green-400' : c.accent}`}>
              {c.value}%
            </p>
          </div>
        )
      })}
    </div>
  )

  return (
    <div className="w-full" ref={containerRef}>
      <div className="relative h-[340px] rounded-2xl overflow-hidden border border-white/[0.06] bg-depth-1 select-none">
        <div
          className="absolute inset-0 z-10"
          style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-green-500/5 to-transparent" />
          <div className="absolute inset-0 flex">
            <div className="flex-1 flex items-center justify-center">
              <ScoreColumn cards={cardsA} side="A" />
            </div>
            <div className="w-0" />
          </div>
          <div className="absolute top-4 left-4">
            <span className="text-[11px] font-semibold text-white/80">{labelA}</span>
            {winner === 'A' && (
              <span className="badge badge-neural ml-2"><Zap className="w-3 h-3" /> WINNER</span>
            )}
          </div>
        </div>

        <div
          className="absolute inset-0 z-20"
          style={{ clipPath: `inset(0 0 0 ${sliderPos}%)` }}
        >
          <div className="absolute inset-0 bg-gradient-to-l from-green-500/5 to-transparent" />
          <div className="absolute inset-0 flex">
            <div className="w-0" />
            <div className="flex-1 flex items-center justify-center">
              <ScoreColumn cards={cardsB} side="B" />
            </div>
          </div>
          <div className="absolute top-4 right-4 text-right">
            <span className="text-[11px] font-semibold text-white/80">{labelB}</span>
            {winner === 'B' && (
              <span className="badge badge-neural ml-2"><Zap className="w-3 h-3" /> WINNER</span>
            )}
          </div>
        </div>

        <motion.div
          className="absolute inset-y-0 z-30 cursor-col-resize flex items-center justify-center"
          style={{ left: `${sliderPos}%`, width: '4px', transform: 'translateX(-2px)' }}
          onMouseDown={handleMouseDown}
          layout
        >
          <div className="w-full h-full bg-white/30 backdrop-blur-sm" />
          <div className="absolute w-10 h-10 rounded-full bg-white/20 backdrop-blur-md border border-white/40 flex items-center justify-center shadow-lg">
            <div className="w-0.5 h-4 bg-white/70 rounded-full -ml-1" />
            <div className="w-0.5 h-4 bg-white/70 rounded-full ml-1" />
          </div>
        </motion.div>
      </div>
    </div>
  )
}
