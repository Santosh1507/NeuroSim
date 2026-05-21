'use client'

import dynamic from 'next/dynamic'

const Brain3D = dynamic(() => import('../components/Brain3D'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[350px] glass-panel flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-neural border-t-transparent rounded-full animate-spin" />
    </div>
  ),
})

/**
 * Brain3DActivation — adapter for vision scorer brain_regions data.
 *
 * Takes the vision_scorer output format (0-1 scale) and converts it
 * to the Brain3D component's expected format (0-100 scale).
 */
export default function Brain3DActivation({
  brainRegions,
  height = 350,
}: {
  brainRegions?: Record<string, number>
  height?: number
}) {
  if (!brainRegions) {
    return (
      <div className="w-full glass-panel flex items-center justify-center" style={{ height: `${height}px` }}>
        <p className="text-text-tertiary text-xs mono">Brain analysis unavailable</p>
      </div>
    )
  }

  // Convert vision_scorer format (0-1) to Brain3D format (0-100)
  const brainData = {
    cortical_response: {
      visual_cortex: (brainRegions.visual_cortex || 0) * 100,
      auditory_cortex: (brainRegions.auditory_cortex || 0) * 100,
      language_center: (brainRegions.social_cognition || 0) * 100,
      amygdala: (brainRegions.amygdala || 0) * 100,
      prefrontal_cortex: (brainRegions.prefrontal || 0) * 100,
      reward_center: (((brainRegions.visual_cortex || 0) + (brainRegions.amygdala || 0)) / 2) * 100,
      social_cognition: (brainRegions.social_cognition || 0) * 100,
      memory_formation: (brainRegions.memory || 0) * 100,
    },
  }

  return (
    <div className="w-full glass-panel p-2" style={{ height: `${height}px` }}>
      <Brain3D brainData={brainData} />
    </div>
  )
}
