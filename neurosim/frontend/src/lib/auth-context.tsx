'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import type { User } from '@supabase/supabase-js'
import { supabase, isSupabaseConfigured } from './supabase'

interface AuthContextType {
  user: User | null
  isSignedIn: boolean
  isLoaded: boolean
  isDemoMode: boolean
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isSignedIn: false,
  isLoaded: true,
  isDemoMode: false,
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

  const signOut = async () => {
    if (isDemoMode) {
      window.location.href = '/'
      return
    }
    if (supabase) await supabase.auth.signOut()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isSignedIn: !!user, isLoaded, isDemoMode, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
