'use client'

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

export function ComparisonBarChart({ data }: { data: { name: string; Yours: number; Average: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
        <XAxis dataKey="name" stroke="#444" fontSize={10} />
        <YAxis stroke="#444" fontSize={10} domain={[0, 100]} />
        <Tooltip
          contentStyle={{ background: '#0f0f16', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px' }}
          labelStyle={{ color: '#fff' }}
        />
        <Bar dataKey="Yours" fill="#4deeea" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Average" fill="rgba(255,255,255,0.15)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
