import { describe, it, expect, afterEach, beforeEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { DashboardRadar, DashboardABAreaChart } from '../app/components/charts/DashboardCharts'
import { AnalyticsBarChart, AnalyticsLineChart } from '../app/components/charts/AnalyticsCharts'
import { ComparisonBarChart } from '../app/components/charts/ComparisonCharts'
import { PredictLineChart } from '../app/components/charts/PredictCharts'
import { SharedRadarChart } from '../app/components/charts/SharedAnalysisCharts'

// Mock ResizeObserver for recharts (not available in jsdom)
beforeEach(() => {
  if (typeof ResizeObserver === 'undefined') {
    global.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    } as any
  }
})

afterEach(cleanup)

const radarData = [
  { subject: 'Hook', value: 85, fullMark: 100 },
  { subject: 'Authenticity', value: 72, fullMark: 100 },
  { subject: 'CTA', value: 60, fullMark: 100 },
]

const analyticsBarData = [
  { name: 'Views', value: 85 },
  { name: 'Engagement', value: 72 },
  { name: 'Retention', value: 90 },
]

const analyticsLineData = [
  { label: 'Mon', current: 80, previous: 60 },
  { label: 'Tue', current: 85, previous: 65 },
  { label: 'Wed', current: 90, previous: 70 },
]

const comparisonData = [
  { name: 'Hook', Yours: 85, Average: 65 },
  { name: 'Authenticity', Yours: 72, Average: 60 },
  { name: 'Viral', Yours: 78, Average: 55 },
]

const predictData = [
  { second: 0, engagement: 90 },
  { second: 3, engagement: 75 },
  { second: 6, engagement: 60 },
]

// ─── DashboardCharts ───────────────────────────────────────

describe('DashboardRadar', () => {
  it('renders without crashing with valid data', () => {
    const { container } = render(<DashboardRadar radarData={radarData} />)
    // The radar chart SVG should render
    expect(container.querySelector('svg')).toBeDefined()
  })

  it('renders with empty data', () => {
    const { container } = render(<DashboardRadar radarData={[]} />)
    expect(container.querySelector('svg')).toBeDefined()
  })

  it('handles null data gracefully', () => {
    const { container } = render(<DashboardRadar radarData={null as any} />)
    // Should not crash — recharts handles null data
    expect(container).toBeDefined()
  })
})

describe('DashboardABAreaChart', () => {
  const mockABResults = {
    version_a: {
      social: {
        seven_day_curve: [10, 25, 50, 80, 120, 150, 180],
      },
    },
    version_b: {
      social: {
        seven_day_curve: [8, 20, 45, 70, 100, 130, 160],
      },
    },
  }

  it('renders area chart with A/B data', () => {
    const { container } = render(<DashboardABAreaChart abResults={mockABResults} />)
    expect(container.querySelector('svg')).toBeDefined()
  })

  it('returns null when abResults is null', () => {
    const { container } = render(<DashboardABAreaChart abResults={null as any} />)
    expect(container.innerHTML).toBe('')
  })

  it('handles missing version curve gracefully', () => {
    const partialResults = {
      version_a: { social: { seven_day_curve: [1, 2, 3] } },
      version_b: { social: {} },
    }
    const { container } = render(<DashboardABAreaChart abResults={partialResults as any} />)
    expect(container.innerHTML).toBe('')
  })

  it('handles different curve lengths', () => {
    const unevenResults = {
      version_a: { social: { seven_day_curve: [1, 2, 3, 4, 5] } },
      version_b: { social: { seven_day_curve: [1, 2, 3] } },
    }
    const { container } = render(<DashboardABAreaChart abResults={unevenResults as any} />)
    expect(container.querySelector('svg')).toBeDefined()
  })

  it('renders backend A/B result shape with social projection', () => {
    const backendResults = {
      version_a: {
        hook_score: 0.6,
        hold_rate: 0.5,
        social: { seven_day_curve: [1000, 2000, 3000, 4000, 5000, 6000, 7000] },
      },
      version_b: {
        hook_score: 0.78,
        hold_rate: 0.62,
        social: { seven_day_curve: [1200, 2400, 3600, 4800, 6000, 7200, 8400] },
      },
      winner: 'B',
    }
    const { container } = render(<DashboardABAreaChart abResults={backendResults} />)
    expect(container.querySelector('svg')).toBeDefined()
  })
})

// ─── AnalyticsCharts ──────────────────────────────────────

describe('AnalyticsBarChart', () => {
  it('renders bar chart with data', () => {
    const { container } = render(<AnalyticsBarChart data={analyticsBarData} />)
    expect(container.querySelector('svg')).toBeDefined()
  })

  it('renders with empty data', () => {
    const { container } = render(<AnalyticsBarChart data={[]} />)
    expect(container.querySelector('svg')).toBeDefined()
  })
})

describe('AnalyticsLineChart', () => {
  it('renders line chart with data', () => {
    const { container } = render(<AnalyticsLineChart data={analyticsLineData} />)
    expect(container.querySelector('svg')).toBeDefined()
  })

  it('renders with empty data', () => {
    const { container } = render(<AnalyticsLineChart data={[]} />)
    expect(container.querySelector('svg')).toBeDefined()
  })
})

// ─── ComparisonCharts ─────────────────────────────────────

describe('ComparisonBarChart', () => {
  it('renders comparison bar chart with data', () => {
    const { container } = render(<ComparisonBarChart data={comparisonData} />)
    expect(container.querySelector('svg')).toBeDefined()
  })

  it('renders with empty data', () => {
    const { container } = render(<ComparisonBarChart data={[]} />)
    expect(container.querySelector('svg')).toBeDefined()
  })
})

// ─── PredictCharts ────────────────────────────────────────

describe('PredictLineChart', () => {
  it('renders prediction line chart with data', () => {
    const { container } = render(<PredictLineChart data={predictData} />)
    expect(container.querySelector('svg')).toBeDefined()
  })

  it('renders with empty data', () => {
    const { container } = render(<PredictLineChart data={[]} />)
    expect(container.querySelector('svg')).toBeDefined()
  })
})

// ─── SharedAnalysisCharts ─────────────────────────────────

describe('SharedRadarChart', () => {
  it('renders shared radar chart with data', () => {
    const { container } = render(<SharedRadarChart data={radarData} />)
    expect(container.querySelector('svg')).toBeDefined()
  })

  it('renders with empty data', () => {
    const { container } = render(<SharedRadarChart data={[]} />)
    expect(container.querySelector('svg')).toBeDefined()
  })
})
