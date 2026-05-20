'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import type { User } from '@supabase/supabase-js'
import { supabase, isSupabaseConfigured } from './supabase'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function getOrCreateGuestId(): string {
  if (typeof window === 'undefined') return ''
  let id = localStorage.getItem('neurosim_guest_id')
  if (!id) {
    id = 'guest_' + crypto.randomUUID()
    localStorage.setItem('neurosim_guest_id', id)
  }
  return id
}

interface AuthContextType {
  user: User | null
  isSignedIn: boolean
  isLoaded: boolean
  isDemoMode: boolean
  guestSessionId: string
  signIn: (email: string, password: string) => Promise<{ error: string | null }>
  signUp: (email: string, password: string) => Promise<{ error: string | null }>
  signInAnonymously: () => Promise<void>
  signOut: () => Promise<void>
  mergeGuestSession: () => Promise<void>
  recoverGuestSession: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isSignedIn: false,
  isLoaded: true,
  isDemoMode: false,
  guestSessionId: '',
  signIn: async () => ({ error: 'Not available' }),
  signUp: async () => ({ error: 'Not available' }),
  signInAnonymously: async () => {},
  signOut: async () => {},
  mergeGuestSession: async () => {},
  recoverGuestSession: async () => {},
})

const DEMO_USER = {
  id: 'demo-user',
  email: 'demo@neurosim.ai',
  user_metadata: { name: 'Demo User', avatar_url: null, full_name: 'Demo User' },
  app_metadata: {},
  aud: 'authenticated',
  created_at: new Date().toISOString(),
} as User

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const [isDemoMode, setIsDemoMode] = useState(false)
  const [guestSessionId, setGuestSessionId] = useState('')

  useEffect(() => {
    setGuestSessionId(getOrCreateGuestId())
  }, [])

  useEffect(() => {
    if (!isSupabaseConfigured || !supabase) {
      setUser(DEMO_USER)
      setIsDemoMode(true)
      setIsLoaded(true)
      return
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setIsLoaded(true)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  const mergeGuestSession = async () => {
    if (!guestSessionId || !user) return
    try {
      await fetch(`${API_URL}/api/v1/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guest_session_id: guestSessionId, user_id: user.id }),
      })
      localStorage.removeItem('neurosim_guest_id')
      setGuestSessionId('')
    } catch (err) {
      console.error('Guest merge failed:', err)
    }
  }

  const recoverGuestSession = async () => {
    const guestId = typeof window !== 'undefined' ? localStorage.getItem('neurosim_guest_id') : null
    if (!guestId || !user) return

    try {
      const response = await fetch(`${API_URL}/api/v1/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guest_session_id: guestId, user_id: user.id }),
      })
      if (response.ok) {
        localStorage.removeItem('neurosim_guest_id')
        window.location.reload()
      }
    } catch (error) {
      console.error('Guest session recovery failed:', error)
    }
  }

  const signIn = async (email: string, password: string) => {
    if (!supabase) return { error: 'Supabase not configured' }
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) return { error: error.message }
    setUser(data.user)
    setIsDemoMode(false)
    await mergeGuestSession()
    return { error: null }
  }

  const signUp = async (email: string, password: string) => {
    if (!supabase) return { error: 'Supabase not configured' }
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) return { error: error.message }
    if (data.user) {
      setUser(data.user)
      setIsDemoMode(false)
      await mergeGuestSession()
    }
    return { error: null }
  }

  const signInAnonymously = async () => {
    setUser(DEMO_USER)
    setIsDemoMode(true)
  }

  const signOut = async () => {
    if (isDemoMode) {
      setUser(null)
      setIsDemoMode(false)
      return
    }
    if (supabase) await supabase.auth.signOut()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isSignedIn: !!user, isLoaded, isDemoMode, guestSessionId, signIn, signUp, signInAnonymously, signOut, mergeGuestSession, recoverGuestSession }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
