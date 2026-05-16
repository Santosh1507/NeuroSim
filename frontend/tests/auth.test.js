/**
 * Tests for auth composable (useAuth, provideAuth, injectAuth, getAccessToken).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock supabase client
const mockSupabase = {
  auth: {
    getSession: vi.fn(),
    signInWithPassword: vi.fn(),
    signUp: vi.fn(),
    signInWithOAuth: vi.fn(),
    signOut: vi.fn(),
    refreshSession: vi.fn(),
    onAuthStateChange: vi.fn(),
  }
}

vi.mock('../src/lib/supabase', () => ({
  supabase: mockSupabase
}))

describe('Auth library', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAccessToken', () => {
    it('returns null when no session', async () => {
      const { getAccessToken, useAuth } = await import('../src/lib/auth')
      const { init } = useAuth()
      mockSupabase.auth.getSession.mockResolvedValue({ data: { session: null } })
      await init()

      expect(getAccessToken()).toBeNull()
    })

    it('returns token when session exists', async () => {
      const { getAccessToken, useAuth } = await import('../src/lib/auth')
      const { init } = useAuth()
      mockSupabase.auth.getSession.mockResolvedValue({
        data: { session: { access_token: 'test-token-123' } }
      })
      await init()

      expect(getAccessToken()).toBe('test-token-123')
    })
  })

  describe('signIn', () => {
    it('calls supabase signInWithPassword with credentials', async () => {
      const { useAuth } = await import('../src/lib/auth')
      const { signIn } = useAuth()

      mockSupabase.auth.signInWithPassword.mockResolvedValue({ error: null })
      await signIn('test@example.com', 'password123')

      expect(mockSupabase.auth.signInWithPassword).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      })
    })

    it('throws error on failed sign in', async () => {
      const { useAuth } = await import('../src/lib/auth')
      const { signIn } = useAuth()

      mockSupabase.auth.signInWithPassword.mockResolvedValue({
        error: { message: 'Invalid login credentials' }
      })

      await expect(signIn('test@example.com', 'wrong')).rejects.toThrow('Invalid login credentials')
    })
  })

  describe('signUp', () => {
    it('calls supabase signUp with credentials', async () => {
      const { useAuth } = await import('../src/lib/auth')
      const { signUp } = useAuth()

      mockSupabase.auth.signUp.mockResolvedValue({ error: null })
      await signUp('new@example.com', 'password123')

      expect(mockSupabase.auth.signUp).toHaveBeenCalledWith({
        email: 'new@example.com',
        password: 'password123'
      })
    })
  })

  describe('signInWithOAuth', () => {
    it('calls supabase signInWithOAuth with provider', async () => {
      const { useAuth } = await import('../src/lib/auth')
      const { signInWithOAuth } = useAuth()

      mockSupabase.auth.signInWithOAuth.mockResolvedValue({ error: null })
      await signInWithOAuth('google')

      expect(mockSupabase.auth.signInWithOAuth).toHaveBeenCalledWith({ provider: 'google' })
    })
  })

  describe('signOut', () => {
    it('calls supabase signOut', async () => {
      const { useAuth } = await import('../src/lib/auth')
      const { signOut } = useAuth()

      mockSupabase.auth.signOut.mockResolvedValue({ error: null })
      await signOut()

      expect(mockSupabase.auth.signOut).toHaveBeenCalled()
    })
  })
})
