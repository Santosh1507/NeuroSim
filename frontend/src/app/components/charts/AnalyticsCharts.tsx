'use client'

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line,
} from 'recharts'

export function AnalyticsBarChart({ data }: { data: { name: string; value: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
        <XAxis dataKey="name" stroke="#444" fontSize={11} />
        <YAxis domain={[0, 100]} stroke="#444" fontSize={11} />
        <Tooltip
          contentStyle={{ background: '#0f0f16', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px' }}
          labelStyle={{ color: '#fff' }}
        />
        <Bar dataKey="value" fill="#4deeea" radius={[4, 4, 0, 0]} fillOpacity={0.7} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function AnalyticsLineChart({ data }: { data: { label: string; current: number; previous: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
        <XAxis dataKey="label" stroke="#444" fontSize={11} />
        <YAxis domain={[0, 100]} stroke="#444" fontSize={11} />
        <Tooltip
          contentStyle={{ background: '#0f0f16', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px' }}
          labelStyle={{ color: '#fff' }}
        />
        <Line type="monotone" dataKey="current" stroke="#4deeea" strokeWidth={2} dot={{ fill: '#4deeea', r: 4 }} name="Current" />
        <Line type="monotone" dataKey="previous" stroke="#a78bfa" strokeWidth={2} strokeDasharray="4 4" dot={{ fill: '#a78bfa', r: 4 }} name="Previous" />
      </LineChart>
    </ResponsiveContainer>
  )
}
