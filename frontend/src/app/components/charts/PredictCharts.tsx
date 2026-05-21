'use client'

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

export function PredictLineChart({ data }: { data: { second: number; engagement: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="second" tick={{ fill: '#555', fontSize: 10 }} label={{ value: 'Second', position: 'insideBottom', offset: -5, fill: '#555', fontSize: 10 }} />
        <YAxis domain={[0, 100]} tick={{ fill: '#555', fontSize: 10 }} />
        <Tooltip
          contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', border: '1px solid rgba(77,238,234,0.2)', borderRadius: '8px' }}
          labelStyle={{ color: '#fff', fontSize: 12 }}
        />
        <Line type="monotone" dataKey="engagement" stroke="#4deeea" strokeWidth={2} dot={{ fill: '#4deeea', r: 3 }} activeDot={{ r: 5 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}
