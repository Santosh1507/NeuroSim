'use client'

export function EarlyEstimateBadge({ show }: { show: boolean }) {
  if (!show) return null
  return (
    <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-amber-400/70 border border-amber-400/20 px-2 py-0.5 rounded">
      <span className="w-1.5 h-1.5 rounded-full bg-amber-400/60 animate-pulse" />
      Early Estimate
    </div>
  )
}
