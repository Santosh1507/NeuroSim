'use client'

import { useState } from 'react'
import { useAuth } from '../../lib/auth-context'
import { X, Mail, Lock } from 'lucide-react'

export function AuthModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { signIn, signUp, signInAnonymously } = useAuth()
  const [mode, setMode] = useState<'signin' | 'signup'>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    const result = mode === 'signin'
      ? await signIn(email, password)
      : await signUp(email, password)

    setLoading(false)

    if (result.error) {
      setError(result.error)
    } else if (mode === 'signup') {
      setSuccess('Account created! Check your email to confirm.')
    } else {
      onClose()
    }
  }

  const handleDemo = async () => {
    await signInAnonymously()
    onClose()
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md mx-4 rounded-2xl border border-white/[0.08] bg-[#0a0a0a] shadow-2xl p-6">
        <button onClick={onClose} className="absolute top-4 right-4 text-text-tertiary hover:text-white cursor-pointer">
          <X className="w-4 h-4" />
        </button>

        <h2 className="text-lg font-semibold text-white mb-1">
          {mode === 'signin' ? 'Sign in to NeuroSim' : 'Create your account'}
        </h2>
        <p className="text-sm text-text-tertiary mb-5">
          {mode === 'signin' ? 'Enter your credentials to continue' : 'Start analyzing content for free'}
        </p>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="text-xs text-text-tertiary mb-1 block">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/40"
              />
            </div>
          </div>

          <div>
            <label className="text-xs text-text-tertiary mb-1 block">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                minLength={6}
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:border-neural/40"
              />
            </div>
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">{error}</p>
          )}
          {success && (
            <p className="text-xs text-green-400 bg-green-400/10 border border-green-400/20 rounded-lg px-3 py-2">{success}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 rounded-lg bg-neural/15 border border-neural/30 text-sm font-medium text-white hover:bg-neural/25 transition-colors disabled:opacity-50 cursor-pointer"
          >
            {loading ? 'Please wait...' : mode === 'signin' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <div className="mt-4 pt-4 border-t border-white/[0.06] space-y-3">
          <button
            onClick={handleDemo}
            className="w-full py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-text-secondary hover:text-white hover:bg-white/[0.08] transition-colors cursor-pointer"
          >
            Continue as guest
          </button>

          <p className="text-center text-xs text-text-tertiary">
            {mode === 'signin' ? (
              <>Don't have an account? <button onClick={() => { setMode('signup'); setError('') }} className="text-neural hover:underline cursor-pointer">Sign up</button></>
            ) : (
              <>Already have an account? <button onClick={() => { setMode('signin'); setError('') }} className="text-neural hover:underline cursor-pointer">Sign in</button></>
            )}
          </p>
        </div>
      </div>
    </div>
  )
}
