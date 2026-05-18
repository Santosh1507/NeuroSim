'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../lib/auth-context'
import { supabase } from '../../lib/supabase'
import { Brain, Menu, X, LogOut, BarChart2 } from 'lucide-react'

export function Navbar() {
  const { isSignedIn, user, isLoaded } = useAuth()
  const { signOut } = useAuth()
  const router = useRouter()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])

  const handleSignIn = async () => {
    if (!supabase) {
      router.push('/dashboard')
      return
    }
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin + '/dashboard' }
    })
    if (error) console.error('Sign in error:', error)
  }

  if (!mounted || !isLoaded) return null

  return (
    <nav className="sticky top-0 z-50 border-b border-white/[0.04] bg-black/60 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
        <button onClick={() => router.push('/')} className="flex items-center gap-3 cursor-pointer">
          <div className="w-8 h-8 rounded-lg bg-neural/10 border border-neural/20 flex items-center justify-center">
            <Brain className="w-4 h-4 text-neural" />
          </div>
          <span className="text-sm font-semibold text-white tracking-tight">NeuroSim</span>
          <span className="text-[10px] mono text-text-tertiary hidden sm:inline">v2.0</span>
        </button>

        <div className="hidden md:flex items-center gap-6">
          <a href="/#features" className="text-xs text-text-tertiary hover:text-white transition-colors">Features</a>
          <a href="/#pipeline" className="text-xs text-text-tertiary hover:text-white transition-colors">How it works</a>
          {isSignedIn && (
            <button onClick={() => router.push('/dashboard')} className="text-xs text-text-tertiary hover:text-white transition-colors flex items-center gap-1 cursor-pointer">
              <BarChart2 className="w-3.5 h-3.5" /> Dashboard
            </button>
          )}
        </div>

        <div className="flex items-center gap-3">
          {isSignedIn ? (
            <div className="flex items-center gap-3">
              <button onClick={() => router.push('/dashboard')} className="btn-neural text-xs py-1.5 px-3 hidden md:flex items-center gap-1.5 cursor-pointer">
                <BarChart2 className="w-3.5 h-3.5" /> Dashboard
              </button>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.06]">
                <div className="w-6 h-6 rounded-full bg-neural/20 flex items-center justify-center">
                  <span className="text-[10px] font-semibold text-neural">
                    {user?.user_metadata?.name?.[0] || user?.email?.[0]?.toUpperCase() || '?'}
                  </span>
                </div>
                <span className="text-xs text-text-secondary hidden sm:inline">
                  {user?.user_metadata?.name || user?.email?.split('@')[0]}
                </span>
                <button onClick={signOut} className="text-text-tertiary hover:text-red-400 transition-colors ml-1 cursor-pointer">
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button onClick={handleSignIn} className="btn-ghost text-xs py-1.5 px-3 cursor-pointer">Sign in</button>
              <button onClick={handleSignIn} className="btn-neural text-xs py-1.5 px-3 cursor-pointer">Get Started Free</button>
            </div>
          )}
          <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-2 text-text-tertiary hover:text-white cursor-pointer">
            {mobileOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden border-t border-white/[0.04] bg-black/80 backdrop-blur-xl">
          <div className="px-6 py-4 space-y-3">
            <a href="/#features" onClick={() => setMobileOpen(false)} className="block text-sm text-text-tertiary hover:text-white">Features</a>
            <a href="/#pipeline" onClick={() => setMobileOpen(false)} className="block text-sm text-text-tertiary hover:text-white">How it works</a>
            {isSignedIn && (
              <button onClick={() => { router.push('/dashboard'); setMobileOpen(false) }} className="block text-sm text-text-tertiary hover:text-white cursor-pointer">Dashboard</button>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}
