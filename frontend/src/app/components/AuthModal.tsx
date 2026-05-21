'use client'

import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../../lib/auth-context'
import { X, Mail, Lock } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { fadeIn } from '../../lib/easing'

export function AuthModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { signIn, signUp, signInAnonymously } = useAuth()
  const [mode, setMode] = useState<'signin' | 'signup'>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState('')
  const [touchedEmail, setTouchedEmail] = useState(false)
  const [touchedPassword, setTouchedPassword] = useState(false)

  const dialogRef = useRef<HTMLDivElement>(null)
  const firstInputRef = useRef<HTMLInputElement>(null)

  // Focus trap + auto-focus when modal opens
  useEffect(() => {
    if (!open) return

    // Auto-focus first input on open
    const timer = setTimeout(() => {
      firstInputRef.current?.focus()
    }, 50)

    // Focus trap: Tab and Shift+Tab cycle within modal
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab' || !dialogRef.current) return

      const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      if (focusable.length === 0) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault()
          last.focus()
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)

    // Prevent body scroll while modal is open
    const originalOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    return () => {
      clearTimeout(timer)
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = originalOverflow
    }
  }, [open])

  // Close on Escape
  useEffect(() => {
    if (!open) return
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [open, onClose])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setTouchedEmail(true)
    setTouchedPassword(true)
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

  return (
    <AnimatePresence>
      {open && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="auth-modal-title"
        >
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
            aria-hidden="true"
          />
          <motion.div
            ref={dialogRef}
            initial={{ opacity: 0, scale: 0.96, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 12 }}
            transition={fadeIn}
            className="relative w-full max-w-md mx-4 rounded-2xl border border-white/[0.08] bg-[#0a0a0a] shadow-2xl p-6"
          >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-text-tertiary hover:text-white cursor-pointer"
          aria-label="Close dialog"
        >
          <X className="w-4 h-4" />
        </button>

        <h2 id="auth-modal-title" className="text-lg font-semibold text-white mb-1">
          {mode === 'signin' ? 'Sign in to NeuroSim' : 'Create your account'}
        </h2>
        <p className="text-sm text-text-tertiary mb-5">
          {mode === 'signin' ? 'Enter your credentials to continue' : 'Start analyzing content for free'}
        </p>

        <form onSubmit={handleSubmit} className="space-y-3" noValidate>
          <div>
            <label htmlFor="auth-email" className="text-xs text-text-tertiary mb-1 block">
              Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" aria-hidden="true" />
              <input
                ref={firstInputRef}
                id="auth-email"
                type="email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setTouchedEmail(true) }}
                onBlur={() => setTouchedEmail(true)}
                placeholder="you@example.com"
                required
                autoComplete="email"
                aria-required="true"
                aria-invalid={!!error && touchedEmail ? 'true' : 'false'}
                aria-describedby={error && touchedEmail ? 'auth-error' : undefined}
                className={`w-full pl-9 pr-3 py-2 rounded-lg bg-white/[0.04] border text-sm text-white placeholder:text-text-tertiary focus:outline-none transition-colors ${
                  error && touchedEmail
                    ? 'border-red-400/40 focus:border-red-400/60'
                    : 'border-white/[0.08] focus:border-neural/40 hover:border-white/[0.15]'
                }`}
              />
            </div>
          </div>

          <div>
            <label htmlFor="auth-password" className="text-xs text-text-tertiary mb-1 block">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" aria-hidden="true" />
              <input
                id="auth-password"
                type="password"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setTouchedPassword(true) }}
                onBlur={() => setTouchedPassword(true)}
                placeholder="••••••••"
                required
                minLength={6}
                autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                aria-required="true"
                aria-invalid={!!error && touchedPassword ? 'true' : 'false'}
                aria-describedby={error && touchedPassword ? 'auth-error' : undefined}
                className={`w-full pl-9 pr-3 py-2 rounded-lg bg-white/[0.04] border text-sm text-white placeholder:text-text-tertiary focus:outline-none transition-colors ${
                  error && touchedPassword
                    ? 'border-red-400/40 focus:border-red-400/60'
                    : 'border-white/[0.08] focus:border-neural/40 hover:border-white/[0.15]'
                }`}
              />
            </div>
          </div>

          {error && (
            <p id="auth-error" className="text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2" role="alert">
              {error}
            </p>
          )}
          {success && (
            <p className="text-xs text-green-400 bg-green-400/10 border border-green-400/20 rounded-lg px-3 py-2" role="alert">
              {success}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            aria-busy={loading}
            className="w-full py-2 rounded-lg bg-neural/15 border border-neural/30 text-sm font-medium text-white hover:bg-neural/25 transition-colors disabled:opacity-50 cursor-pointer"
          >
            {loading ? 'Please wait...' : mode === 'signin' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <div className="mt-4 pt-4 border-t border-white/[0.06] space-y-3">
          <button
            onClick={handleDemo}
            className="w-full py-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm text-text-secondary hover:text-white hover:bg-white/[0.08] transition-colors cursor-pointer"
            aria-label="Continue as guest without signing in"
          >
            Continue as guest
          </button>

          <p className="text-center text-xs text-text-tertiary">
            {mode === 'signin' ? (
              <>Don&apos;t have an account?{' '}
                <button onClick={() => { setMode('signup'); setError(''); setSuccess('') }} className="text-neural hover:underline cursor-pointer" aria-label="Switch to sign up form">
                  Sign up
                </button>
              </>
            ) : (
              <>Already have an account?{' '}
                <button onClick={() => { setMode('signin'); setError(''); setSuccess('') }} className="text-neural hover:underline cursor-pointer" aria-label="Switch to sign in form">
                  Sign in
                </button>
              </>
            )}
          </p>
        </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
