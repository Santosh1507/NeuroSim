import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

beforeEach(() => {
  vi.stubEnv('NODE_ENV', 'test')
  vi.resetModules()
  // Mock fetch to return a promise with .catch so the chained .catch(() => {}) works
  vi.stubGlobal('fetch', vi.fn().mockReturnValue(Promise.resolve(new Response())))
})

afterEach(() => {
  vi.unstubAllEnvs()
  vi.restoreAllMocks()
})

describe('reportError', () => {
  it('reports an Error object', async () => {
    vi.stubEnv('NODE_ENV', 'production')
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.test.com')

    const { reportError } = await import('../lib/error-reporter')
    reportError(new Error('Test error'))

    const fetchMock = vi.mocked(fetch)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const callUrl = fetchMock.mock.calls[0][0]
    const callBody = JSON.parse(fetchMock.mock.calls[0][1]!.body as string)

    expect(callUrl).toContain('/api/v1/error-report')
    expect(callBody.message).toBe('Test error')
    expect(callBody.url).toBeDefined()
    expect(callBody.timestamp).toBeDefined()
  })

  it('reports a string error with context', async () => {
    vi.stubEnv('NODE_ENV', 'production')
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.test.com')

    const { reportError } = await import('../lib/error-reporter')
    reportError('String error', { component: 'Test' })

    const fetchMock = vi.mocked(fetch)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const callBody = JSON.parse(fetchMock.mock.calls[0][1]!.body as string)
    expect(callBody.message).toBe('String error')
  })

  it('includes stack trace for Error objects', async () => {
    vi.stubEnv('NODE_ENV', 'production')
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.test.com')

    const { reportError } = await import('../lib/error-reporter')
    const error = new Error('Stack trace test')
    reportError(error)

    const fetchMock = vi.mocked(fetch)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const callBody = JSON.parse(fetchMock.mock.calls[0][1]!.body as string)
    expect(callBody.stack).toBeDefined()
  })

  it('does not send fetch in development mode', async () => {
    vi.stubEnv('NODE_ENV', 'development')
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.test.com')

    const { reportError } = await import('../lib/error-reporter')
    reportError('Dev error')

    expect(vi.mocked(fetch)).not.toHaveBeenCalled()
  })

  it('does not throw when fetch fails', async () => {
    vi.stubEnv('NODE_ENV', 'production')
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.test.com')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')))

    const { reportError } = await import('../lib/error-reporter')

    // Should not throw — the catch(() => {}) swallows errors
    expect(() => reportError('Network error')).not.toThrow()
  })
})

describe('window error event listeners', () => {
  it('registers global error and unhandledrejection listeners', async () => {
    const addEventListenerSpy = vi.spyOn(window, 'addEventListener')
    vi.stubEnv('NODE_ENV', 'development')

    // Re-import to trigger the side effects
    await import('../lib/error-reporter')

    expect(addEventListenerSpy).toHaveBeenCalledWith('error', expect.any(Function))
    expect(addEventListenerSpy).toHaveBeenCalledWith('unhandledrejection', expect.any(Function))
  })
})
