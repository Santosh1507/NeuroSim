import { describe, it, expect } from 'vitest'

describe('page imports resolve', () => {
  it('home page imports cleanly', async () => {
    const mod = await import('../app/page')
    expect(mod.default).toBeDefined()
  })

  it('dashboard page imports cleanly', async () => {
    const mod = await import('../app/dashboard/page')
    expect(mod.default).toBeDefined()
  })

  it('pricing page imports cleanly', async () => {
    const mod = await import('../app/pricing/page')
    expect(mod.default).toBeDefined()
  })

  it('waitlist page imports cleanly', async () => {
    const mod = await import('../app/waitlist/page')
    expect(mod.default).toBeDefined()
  })

  it('analytics page imports cleanly', async () => {
    const mod = await import('../app/analytics/page')
    expect(mod.default).toBeDefined()
  })

  it('share page imports cleanly', async () => {
    const mod = await import('../app/r/[id]/page')
    expect(mod.default).toBeDefined()
  })

  it('embed page imports cleanly', async () => {
    const mod = await import('../app/embed/[id]/page')
    expect(mod.default).toBeDefined()
  })
})

describe('component imports resolve', () => {
  it('Navbar imports cleanly', async () => {
    const mod = await import('../app/components/Navbar')
    expect(mod.Navbar).toBeDefined()
  })

  it('ComparisonSlider imports cleanly', async () => {
    const mod = await import('../app/components/ComparisonSlider')
    expect(mod.default).toBeDefined()
  })
})