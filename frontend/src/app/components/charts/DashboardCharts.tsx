'use client'

import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ResponsiveContainer, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip,
} from 'recharts'

interface DashboardChartsProps {
  radarData: { subject: string; value: number; fullMark: number }[]
  abResults: any
}

export function DashboardRadar({ radarData }: { radarData: DashboardChartsProps['radarData'] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <RadarChart data={radarData}>
        <PolarGrid stroke="rgba(255,255,255,0.05)" />
        <PolarAngleAxis dataKey="subject" tick={{ fill: '#555', fontSize: 10 }} />
        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#333' }} />
        <Radar name="Response" dataKey="value" stroke="#4deeea" fill="#4deeea" fillOpacity={0.1} strokeWidth={1.5} />
      </RadarChart>
    </ResponsiveContainer>
  )
}

export function DashboardABAreaChart({ abResults }: { abResults: any }) {
  if (!abResults?.version_a?.social?.seven_day_curve || !abResults?.version_b?.social?.seven_day_curve) {
    return null
  }

  const aCurve = abResults.version_a.social.seven_day_curve
  const bCurve = abResults.version_b.social.seven_day_curve
  const maxLen = Math.max(aCurve.length, bCurve.length)
  const chartData = Array.from({ length: maxLen }, (_, i) => ({
    day: i + 1,
    a: aCurve[i] ?? 0,
    b: bCurve[i] ?? 0,
  }))

  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id="gradA" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#4deeea" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#4deeea" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradB" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#a78bfa" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#a78bfa" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
        <XAxis dataKey="day" stroke="#444" fontSize={10} />
        <YAxis stroke="#444" fontSize={10} />
        <Tooltip
          contentStyle={{ background: '#0f0f16', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px' }}
          labelStyle={{ color: '#fff' }}
        />
        <Area type="monotone" dataKey="a" stroke="#4deeea" fill="url(#gradA)" strokeWidth={1.5} name="Version A" />
        <Area type="monotone" dataKey="b" stroke="#a78bfa" fill="url(#gradB)" strokeWidth={1.5} name="Version B" />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function DashboardABRadarOverlay({ abResults }: { abResults: any }) {
  if (!abResults?.version_a?.brain_regions || !abResults?.version_b?.brain_regions) {
    return null
  }

  const brainRegionLabels: Record<string, string> = {
    visual_cortex: 'Visual Cortex',
    auditory_cortex: 'Auditory Cortex',
    amygdala: 'Amygdala',
    prefrontal: 'Prefrontal',
    memory: 'Memory',
    social_cognition: 'Social Cog'
  }

  const chartData = Object.keys(brainRegionLabels).map(key => ({
    subject: brainRegionLabels[key],
    a: (abResults.version_a.brain_regions[key] ?? 0.5) * 100,
    b: (abResults.version_b.brain_regions[key] ?? 0.5) * 100,
  }))

  return (
    <ResponsiveContainer width="100%" height={240}>
      <RadarChart data={chartData}>
        <PolarGrid stroke="rgba(255,255,255,0.05)" />
        <PolarAngleAxis dataKey="subject" tick={{ fill: '#888', fontSize: 10 }} />
        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#444', fontSize: 8 }} />
        <Radar name="Version A" dataKey="a" stroke="#4deeea" fill="#4deeea" fillOpacity={0.15} strokeWidth={2} />
        <Radar name="Version B" dataKey="b" stroke="#a78bfa" fill="#a78bfa" fillOpacity={0.15} strokeWidth={2} />
        <Tooltip
          contentStyle={{ background: '#0f0f16', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px' }}
          labelStyle={{ color: '#fff' }}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}

