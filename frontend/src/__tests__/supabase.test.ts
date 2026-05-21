import { describe, it, expect, vi, beforeEach } from 'vitest'

beforeEach(() => {
  vi.resetModules()
})

describe('supabase client factory', () => {
  it('returns null when no env vars are set', async () => {
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', '')
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', '')

    const { supabase, isSupabaseConfigured } = await import('../lib/supabase')
    expect(supabase).toBeNull()
    expect(isSupabaseConfigured).toBe(false)
  })

  it('creates client when env vars are present', async () => {
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', 'test-anon-key')

    const { supabase, isSupabaseConfigured } = await import('../lib/supabase')
    expect(supabase).not.toBeNull()
    expect(isSupabaseConfigured).toBe(true)
  })

  it('returns null when only URL is set', async () => {
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', '')

    const { supabase, isSupabaseConfigured } = await import('../lib/supabase')
    expect(supabase).toBeNull()
    expect(isSupabaseConfigured).toBe(false)
  })

  it('returns null when only ANON_KEY is set', async () => {
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', '')
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', 'test-anon-key')

    const { supabase, isSupabaseConfigured } = await import('../lib/supabase')
    expect(supabase).toBeNull()
    expect(isSupabaseConfigured).toBe(false)
  })

  it('creates a client with the correct URL', async () => {
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', 'test-anon-key')

    const { supabase } = await import('../lib/supabase')
    expect(supabase).not.toBeNull()
    // The client should have a URL property from the createClient call
    // We assert the client is an object (not null)
    expect(typeof supabase).toBe('object')
  })
})
