'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

interface UsageData {
  plan: string
  analyses_used: number
  analyses_limit: number | null
  remaining: number
  period_end: string
  is_premium: boolean
  premium_enabled: boolean
}

export function UsageCounter() {
  const [data, setData] = useState<UsageData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetch = async () => {
      try {
        const token = localStorage.getItem('neurosim_token')
        const res = await axios.get(`${API_URL}/api/v1/subscription/status`, {
          headers: { Authorization: `Bearer ${token || ''}` },
        })
        setData(res.data)
      } catch {
        setData(null)
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [])

  if (loading || !data || !data.premium_enabled) return null

  if (data.is_premium) {
    return (
      <div className="flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-lg border border-neural/30 text-neural">
        <span className="w-1.5 h-1.5 rounded-full bg-neural/60 animate-pulse" />
        Pro
      </div>
    )
  }

  const pct = data.analyses_limit ? (data.analyses_used / data.analyses_limit) * 100 : 0
  const near = pct >= 80

  return (
    <div className={`flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-lg border ${
      near ? 'border-amber-400/30 text-amber-400' : 'border-white/10 text-text-tertiary'
    }`}>
      <span>{data.analyses_used} / {data.analyses_limit} analyses</span>
      {near && (
        <span>
          <span className="mx-1 opacity-30">·</span>
          <Link href="/pricing" className="text-neural underline underline-offset-2">Upgrade</Link>
        </span>
      )}
    </div>
  )
}
