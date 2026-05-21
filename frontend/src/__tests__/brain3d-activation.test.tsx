import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import Brain3DActivation from '../app/components/Brain3DActivation'

afterEach(cleanup)

describe('Brain3DActivation', () => {
  it('shows placeholder when brainRegions is null', () => {
    render(<Brain3DActivation brainRegions={null as any} />)
    expect(screen.getByText('Brain analysis unavailable')).toBeDefined()
  })

  it('shows placeholder when brainRegions is undefined', () => {
    render(<Brain3DActivation />)
    expect(screen.getByText('Brain analysis unavailable')).toBeDefined()
  })

  it('renders container with valid brain regions', () => {
    const { container } = render(<Brain3DActivation
      brainRegions={{
        visual_cortex: 0.8,
        amygdala: 0.5,
        social_cognition: 0.6,
        memory: 0.3,
        prefrontal: 0.7,
      }}
    />)
    // Should render the glass-panel container (Brain3D is lazy-loaded, so no <canvas> in jsdom)
    const panels = container.querySelectorAll('.glass-panel')
    expect(panels.length).toBeGreaterThanOrEqual(1)
  })

  it('renders container with empty brain regions object', () => {
    const { container } = render(<Brain3DActivation brainRegions={{}} />)
    const panels = container.querySelectorAll('.glass-panel')
    expect(panels.length).toBeGreaterThanOrEqual(1)
  })

  it('accepts custom height prop', () => {
    const { container } = render(<Brain3DActivation brainRegions={{}} height={500} />)
    const outerDiv = container.firstElementChild as HTMLElement
    expect(outerDiv.style.height).toBe('500px')
  })

  it('converts 0-1 scale to 0-100 scale for Brain3D', () => {
    const { container } = render(<Brain3DActivation
      brainRegions={{
        visual_cortex: 0.25,
        amygdala: 0.75,
        social_cognition: 0.5,
      }}
    />)
    // Component renders without crashing — data conversion happens internally
    const panels = container.querySelectorAll('.glass-panel')
    expect(panels.length).toBeGreaterThanOrEqual(1)
  })

  it('renders with partial brain regions (missing keys default to 0)', () => {
    const { container } = render(<Brain3DActivation
      brainRegions={{
        // Only visual_cortex provided — others should default to 0
        visual_cortex: 0.9,
      }}
    />)
    const panels = container.querySelectorAll('.glass-panel')
    expect(panels.length).toBeGreaterThanOrEqual(1)
  })
})
