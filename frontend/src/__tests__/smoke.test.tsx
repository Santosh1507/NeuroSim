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

  it('predict page imports cleanly', async () => {
    const mod = await import('../app/predict/page')
    expect(mod.default).toBeDefined()
  })

  it('comparison page imports cleanly', async () => {
    const mod = await import('../app/comparison/page')
    expect(mod.default).toBeDefined()
  })

  it('digest page imports cleanly', async () => {
    const mod = await import('../app/digest/page')
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

  it('ProgressStageIndicator imports cleanly', async () => {
    const mod = await import('../app/components/ProgressStageIndicator')
    expect(mod.default).toBeDefined()
  })

  it('AuthModal imports cleanly', async () => {
    const mod = await import('../app/components/AuthModal')
    expect(mod.AuthModal).toBeDefined()
  })

  it('Brain3D imports cleanly', async () => {
    const mod = await import('../app/components/Brain3D')
    expect(mod.default).toBeDefined()
  })

  it('Brain3DActivation imports cleanly', async () => {
    const mod = await import('../app/components/Brain3DActivation')
    expect(mod.default).toBeDefined()
  })
})

describe('chart wrapper components resolve (dynamic imports)', () => {
  it('DashboardCharts resolves via dynamic import', async () => {
    const mod = await import('../app/components/charts/DashboardCharts')
    expect(mod.DashboardRadar).toBeDefined()
    expect(mod.DashboardABAreaChart).toBeDefined()
  })

  it('AnalyticsCharts resolves via dynamic import', async () => {
    const mod = await import('../app/components/charts/AnalyticsCharts')
    expect(mod.AnalyticsBarChart).toBeDefined()
    expect(mod.AnalyticsLineChart).toBeDefined()
  })

  it('ComparisonCharts resolves via dynamic import', async () => {
    const mod = await import('../app/components/charts/ComparisonCharts')
    expect(mod.ComparisonBarChart).toBeDefined()
  })

  it('PredictCharts resolves via dynamic import', async () => {
    const mod = await import('../app/components/charts/PredictCharts')
    expect(mod.PredictLineChart).toBeDefined()
  })

  it('SharedAnalysisCharts resolves via dynamic import', async () => {
    const mod = await import('../app/components/charts/SharedAnalysisCharts')
    expect(mod.SharedRadarChart).toBeDefined()
  })

  it('next/dynamic lazy-imports work for dashboard pages', async () => {
    // These are the actual dynamic(() => import(...)) calls used in page files
    const dashRadar = () => import('../app/components/charts/DashboardCharts').then(m => ({ default: m.DashboardRadar }))
    const dashArea = () => import('../app/components/charts/DashboardCharts').then(m => ({ default: m.DashboardABAreaChart }))
    const [radar, area] = await Promise.all([dashRadar(), dashArea()])
    expect(radar.default).toBeDefined()
    expect(area.default).toBeDefined()
  })

  it('next/dynamic lazy-imports work for analytics pages', async () => {
    const bar = () => import('../app/components/charts/AnalyticsCharts').then(m => ({ default: m.AnalyticsBarChart }))
    const line = () => import('../app/components/charts/AnalyticsCharts').then(m => ({ default: m.AnalyticsLineChart }))
    const [barMod, lineMod] = await Promise.all([bar(), line()])
    expect(barMod.default).toBeDefined()
    expect(lineMod.default).toBeDefined()
  })
})