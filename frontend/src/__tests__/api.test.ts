import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('API_URL constant', () => {
  beforeEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('uses env var when set', async () => {
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.test.com')
    const { API_URL: url } = await import('../lib/api')
    expect(url).toBe('https://api.test.com')
  })
})

describe('API_URL constant fallback', () => {
  beforeEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('falls back to localhost when env var is not set', async () => {
    vi.stubEnv('NEXT_PUBLIC_API_URL', '')
    const { API_URL: url } = await import('../lib/api')
    expect(url).toBe('http://localhost:8001')
  })
})

describe('apiClient', () => {
  beforeEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', '')
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', '')
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'http://localhost:8001')
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('exports default apiClient and the API_URL constant', async () => {
    const apiModule = await import('../lib/api')
    expect(apiModule.default).toBeDefined()
    expect(apiModule.API_URL).toBeDefined()
  })

  it('has correct baseURL and timeout', async () => {
    const apiModule = await import('../lib/api')
    const client = apiModule.default
    expect(client.defaults.baseURL).toBe('http://localhost:8001')
    expect(client.defaults.timeout).toBe(30_000)
    expect(client.defaults.headers['Content-Type']).toBe('application/json')
  })

  it('has request interceptor registered', async () => {
    const apiModule = await import('../lib/api')
    const client = apiModule.default
    expect(client.interceptors.request.handlers?.length ?? 0).toBeGreaterThanOrEqual(1)
  })

  it('has response interceptor registered', async () => {
    const apiModule = await import('../lib/api')
    const client = apiModule.default
    expect(client.interceptors.response.handlers?.length ?? 0).toBeGreaterThanOrEqual(1)
  })
})
