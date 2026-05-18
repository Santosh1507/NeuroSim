'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import type { User } from '@supabase/supabase-js'
import { supabase, isSupabaseConfigured } from './supabase'

interface AuthContextType {
  user: User | null
  isSignedIn: boolean
  isLoaded: boolean
  isDemoMode: boolean
  signIn: (email: string, password: string) => Promise<{ error: string | null }>
  signUp: (email: string, password: string) => Promise<{ error: string | null }>
  signInAnonymously: () => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isSignedIn: false,
  isLoaded: true,
  isDemoMode: false,
  signIn: async () => ({ error: 'Not available' }),
  signUp: async () => ({ error: 'Not available' }),
  signInAnonymously: async () => {},
  signOut: async () => {},
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

  const signIn = async (email: string, password: string) => {
    if (!supabase) return { error: 'Supabase not configured' }
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) return { error: error.message }
    setUser(data.user)
    setIsDemoMode(false)
    return { error: null }
  }

  const signUp = async (email: string, password: string) => {
    if (!supabase) return { error: 'Supabase not configured' }
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) return { error: error.message }
    if (data.user) {
      setUser(data.user)
      setIsDemoMode(false)
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
    <AuthContext.Provider value={{ user, isSignedIn: !!user, isLoaded, isDemoMode, signIn, signUp, signInAnonymously, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
