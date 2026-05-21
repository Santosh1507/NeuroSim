'use client'

import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'

export function SharedRadarChart({ data }: { data: { subject: string; value: number; fullMark: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <RadarChart data={data}>
        <PolarGrid stroke="rgba(255,255,255,0.05)" />
        <PolarAngleAxis dataKey="subject" tick={{ fill: '#555', fontSize: 10 }} />
        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#333' }} />
        <Radar name="Response" dataKey="value" stroke="#4deeea" fill="#4deeea" fillOpacity={0.1} strokeWidth={1.5} />
      </RadarChart>
    </ResponsiveContainer>
  )
}
