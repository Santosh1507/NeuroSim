'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import type { User } from '@supabase/supabase-js'
import { supabase, isSupabaseConfigured } from './supabase'
import { API_URL } from './api'

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
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const [isDemoMode, setIsDemoMode] = useState(false)
  const [guestSessionId, setGuestSessionId] = useState('')

  useEffect(() => {
    setGuestSessionId(getOrCreateGuestId())
  }, [])

  useEffect(() => {
    if (!isSupabaseConfigured || !supabase) {
      if (process.env.NODE_ENV === 'development') {
        setUser(DEMO_USER)
        setIsDemoMode(true)
      }
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
    let retries = 2
    while (retries >= 0) {
      try {
        const session = supabase ? (await supabase.auth.getSession()).data.session : null
        const token = session?.access_token
        const headers: Record<string, string> = { 'Content-Type': 'application/json' }
        if (token) {
          headers['Authorization'] = `Bearer ${token}`
        } else if (isDemoMode) {
          headers['Authorization'] = `Bearer ${user.id}`
        }
        const response = await fetch(`${API_URL}/api/v1/auth/guest/merge`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ guest_session_id: guestSessionId, user_id: user.id }),
        })
        if (response.ok) {
          localStorage.removeItem('neurosim_guest_id')
          setGuestSessionId('')
          return
        }
        console.error(`Guest merge failed with status ${response.status}`)
      } catch (err) {
        console.error('Guest merge failed:', err)
      }
      retries -= 1
      if (retries >= 0) {
        await new Promise(r => setTimeout(r, 1000))
      }
    }
    console.error('Guest merge failed after retries — data may be lost')
  }

  const recoverGuestSession = async () => {
    const guestId = typeof window !== 'undefined' ? localStorage.getItem('neurosim_guest_id') : null
    if (!guestId || !user) return

    try {
      const session = supabase ? (await supabase.auth.getSession()).data.session : null
      const token = session?.access_token
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      } else if (isDemoMode) {
        headers['Authorization'] = `Bearer ${user.id}`
      }

      const response = await fetch(`${API_URL}/api/v1/auth/guest/merge`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ guest_session_id: guestId, user_id: user.id }),
      })
      if (response.ok) {
        localStorage.removeItem('neurosim_guest_id')
        // Use router navigation instead of hard reload for smoother UX
        router.refresh()
        router.push('/dashboard')
      }
    } catch (error) {
      console.error('Guest session recovery failed:', error)
    }
  }

  const signIn = async (email: string, password: string) => {
    if (!supabase) return { error: 'Supabase not configured' }
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) return { error: error.message }
    setIsDemoMode(false)
    await mergeGuestSession()
    return { error: null }
  }

  const signUp = async (email: string, password: string) => {
    if (!supabase) return { error: 'Supabase not configured' }
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) return { error: error.message }
    if (data.user) {
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
    if (typeof window !== 'undefined') {
      localStorage.removeItem('neurosim_guest_id')
      setGuestSessionId(getOrCreateGuestId())
    }
  }

  return (
    <AuthContext.Provider value={{ user, isSignedIn: !!user, isLoaded, isDemoMode, guestSessionId, signIn, signUp, signInAnonymously, signOut, mergeGuestSession, recoverGuestSession }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
