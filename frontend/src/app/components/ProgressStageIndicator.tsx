'use client'

import { motion } from 'framer-motion'
import { Upload, Activity, BarChart3, CheckCircle2 } from 'lucide-react'

export interface Stage {
  id: string
  label: string
  icon?: React.ReactNode
}

export interface ProgressStageIndicatorProps {
  stages?: Stage[]
  currentStage: string
  accent?: 'neural' | 'swarm'
  className?: string
}

const defaultStages: Stage[] = [
  { id: 'uploading',  label: 'Upload',   icon: <Upload className="w-3 h-3" /> },
  { id: 'transcribing', label: 'Audio',  icon: <Activity className="w-3 h-3" /> },
  { id: 'scoring',   label: 'Score',     icon: <BarChart3 className="w-3 h-3" /> },
  { id: 'saving',    label: 'Save',      icon: <CheckCircle2 className="w-3 h-3" /> },
  { id: 'done',      label: 'Done',      icon: <CheckCircle2 className="w-3 h-3" /> },
]

const accentColors = {
  neural: {
    active: 'bg-neural border-neural/20 text-neural',
    activeDot: 'bg-neural shadow-[0_0_6px_rgba(77,238,234,0.5)]',
    complete: 'bg-neural/20 border-neural/30 text-neural',
    completeLine: 'bg-neural/30',
    pending: 'bg-white/[0.03] border-white/[0.06] text-text-tertiary',
    pendingDot: 'bg-white/10',
    pendingLine: 'bg-white/[0.06]',
  },
  swarm: {
    active: 'bg-swarm/10 border-swarm/20 text-swarm',
    activeDot: 'bg-swarm shadow-[0_0_6px_rgba(167,139,250,0.5)]',
    complete: 'bg-swarm/20 border-swarm/30 text-swarm',
    completeLine: 'bg-swarm/30',
    pending: 'bg-white/[0.03] border-white/[0.06] text-text-tertiary',
    pendingDot: 'bg-white/10',
    pendingLine: 'bg-white/[0.06]',
  },
}

export default function ProgressStageIndicator({
  stages = defaultStages,
  currentStage,
  accent = 'neural',
  className = '',
}: ProgressStageIndicatorProps) {
  const currentIdx = stages.findIndex(s => s.id === currentStage)
  const colors = accentColors[accent]

  return (
    <div className={`flex items-center gap-0 ${className}`}>
      {stages.map((stage, i) => {
        const isComplete = i < currentIdx
        const isActive = i === currentIdx
        const isPending = i > currentIdx

        return (
          <div key={stage.id} className="flex items-center">
            {/* Stage dot + label */}
            <div className="flex items-center gap-1.5">
              <motion.div
                className={`w-2 h-2 rounded-full ${
                  isComplete ? colors.completeLine :
                  isActive ? colors.activeDot :
                  colors.pendingDot
                } ${isActive ? 'animate-pulse' : ''}`}
                initial={isActive ? { scale: 0.8 } : undefined}
                animate={isActive ? { scale: [0.8, 1.2, 0.8] } : undefined}
                transition={isActive ? { duration: 2, repeat: Infinity, ease: 'easeInOut' } : undefined}
              />
              <span className={`text-[10px] mono whitespace-nowrap ${
                isComplete || isActive ? 'text-neural' : 'text-text-tertiary'
              }`}>
                {stage.label}
              </span>
            </div>

            {/* Connector line */}
            {i < stages.length - 1 && (
              <div className={`w-5 h-px mx-2 transition-colors duration-500 ${
                isComplete ? colors.completeLine : colors.pendingLine
              }`} />
            )}
          </div>
        )
      })}
    </div>
  )
}
