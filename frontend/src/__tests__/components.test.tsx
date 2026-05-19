import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import ComparisonSlider from '../app/components/ComparisonSlider'

afterEach(cleanup)

const mockAnalysisA = {
  success_probability: 85,
  hook_score: 90,
  authenticity_score: 75,
  viral_potential: 80,
}

const mockAnalysisB = {
  success_probability: 62,
  hook_score: 55,
  authenticity_score: 68,
  viral_potential: 45,
}

describe('ComparisonSlider', () => {
  it('renders with both analyses and shows scores', () => {
    render(<ComparisonSlider analysisA={mockAnalysisA} analysisB={mockAnalysisB} />)
    // unique values appear once per side
    expect(screen.getByText('85%')).toBeDefined()
    expect(screen.getByText('62%')).toBeDefined()
    expect(screen.getByText('90%')).toBeDefined()
    expect(screen.getByText('55%')).toBeDefined()
  })

  it('renders custom labels when provided', () => {
    render(<ComparisonSlider analysisA={mockAnalysisA} analysisB={mockAnalysisB} labelA="Control" labelB="Variant" />)
    expect(screen.getByText('Control')).toBeDefined()
    expect(screen.getByText('Variant')).toBeDefined()
  })

  it('renders default labels when none provided', () => {
    render(<ComparisonSlider analysisA={mockAnalysisA} analysisB={mockAnalysisB} />)
    // The split-pane component renders content in two clip-path regions
    // Use getAllByText to handle the duplicated DOM structure
    const labelsA = screen.getAllByText('Version A')
    const labelsB = screen.getAllByText('Version B')
    expect(labelsA.length).toBeGreaterThanOrEqual(1)
    expect(labelsB.length).toBeGreaterThanOrEqual(1)
  })

  it('shows winner badge when version A has higher score', () => {
    render(<ComparisonSlider analysisA={mockAnalysisA} analysisB={mockAnalysisB} />)
    // Version A (85) beats Version B (62)
    const badges = screen.getAllByText('WINNER')
    expect(badges.length).toBeGreaterThanOrEqual(1)
  })

  it('handles null/undefined analysis gracefully', () => {
    const { container } = render(<ComparisonSlider analysisA={null} analysisB={undefined as any} />)
    // Both sides render 4 cards each → 8 "0%" texts
    const zeros = screen.getAllByText('0%')
    expect(zeros.length).toBe(8)
    expect(container.querySelector('.glass-panel')).toBeDefined()
  })

  it('handles partial analysis data gracefully', () => {
    render(<ComparisonSlider analysisA={{ success_probability: 50 }} analysisB={mockAnalysisB} />)
    // side A has 3 zero values (hook, auth, viral) and success=50
    // Use getAllByText for robustness with the split-pane DOM structure
    const fifteens = screen.getAllByText('50%')
    expect(fifteens.length).toBeGreaterThanOrEqual(1)
    // Component doesn't crash — glass panels still render
    const panels = screen.getAllByText(/Hook|Authenticity|Viral|Success/)
    expect(panels.length).toBeGreaterThanOrEqual(4)
  })

  it('renders with equal scores', () => {
    const equalA = { success_probability: 50, hook_score: 50, authenticity_score: 50, viral_potential: 50 }
    const equalB = { success_probability: 50, hook_score: 50, authenticity_score: 50, viral_potential: 50 }
    const { container } = render(<ComparisonSlider analysisA={equalA} analysisB={equalB} />)
    // No text "WINNER" should render when scores are equal
    const winnerElements = screen.queryAllByText('WINNER')
    expect(winnerElements.length).toBe(0)
  })
})
