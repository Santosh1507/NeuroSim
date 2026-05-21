import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/react'
import OnboardingTour from '../app/components/OnboardingTour'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  localStorage.clear()
})

describe('OnboardingTour', () => {
  it('renders when onboarding not seen yet', () => {
    // Ensure localStorage doesn't have the flag
    localStorage.removeItem('neurosim_onboarding_seen')
    const onComplete = vi.fn()
    render(<OnboardingTour onComplete={onComplete} />)

    // First step should be visible
    expect(screen.getByText('Welcome to NeuroSim v3.0')).toBeDefined()
    expect(screen.getByText(/Enter the era of predictive creative intelligence/)).toBeDefined()
  })

  it('does not render when onboarding already seen', () => {
    localStorage.setItem('neurosim_onboarding_seen', 'true')
    const onComplete = vi.fn()
    const { container } = render(<OnboardingTour onComplete={onComplete} />)

    // Should not render anything
    expect(container.innerHTML).toBe('')
  })

  it('closes and calls onComplete when backdrop is clicked', () => {
    localStorage.removeItem('neurosim_onboarding_seen')
    const onComplete = vi.fn()
    render(<OnboardingTour onComplete={onComplete} />)

    // Click the backdrop (the outer motion.div with onClick={handleComplete})
    const backdrop = screen.getByRole('dialog').parentElement!
    fireEvent.click(backdrop)

    expect(onComplete).toHaveBeenCalledTimes(1)
    expect(localStorage.getItem('neurosim_onboarding_seen')).toBe('true')
  })

  it('closes and calls onComplete when close button is clicked', () => {
    localStorage.removeItem('neurosim_onboarding_seen')
    const onComplete = vi.fn()
    render(<OnboardingTour onComplete={onComplete} />)

    // Click the close button
    const closeBtn = screen.getByLabelText('Close onboarding')
    fireEvent.click(closeBtn)

    expect(onComplete).toHaveBeenCalledTimes(1)
  })

  it('navigates to next step on Next click', () => {
    localStorage.removeItem('neurosim_onboarding_seen')
    const onComplete = vi.fn()
    render(<OnboardingTour onComplete={onComplete} />)

    // Should show first step
    expect(screen.getByText('Welcome to NeuroSim v3.0')).toBeDefined()

    // Click Next
    fireEvent.click(screen.getByText('Next'))

    // Should now show second step
    expect(screen.getByText('Tri-Engine Input')).toBeDefined()
  })

  it('goes through all 5 steps and shows Get Started on last', () => {
    localStorage.removeItem('neurosim_onboarding_seen')
    const onComplete = vi.fn()
    render(<OnboardingTour onComplete={onComplete} />)

    // Step 1
    expect(screen.getByText('Welcome to NeuroSim v3.0')).toBeDefined()
    fireEvent.click(screen.getByText('Next'))

    // Step 2
    expect(screen.getByText('Tri-Engine Input')).toBeDefined()
    fireEvent.click(screen.getByText('Next'))

    // Step 3
    expect(screen.getByText('Tri-Engine Prediction')).toBeDefined()
    fireEvent.click(screen.getByText('Next'))

    // Step 4
    expect(screen.getByText('Deep Creative Signals')).toBeDefined()
    fireEvent.click(screen.getByText('Next'))

    // Step 5 - should show "Get Started" instead of "Next"
    expect(screen.getByText('Publish with Certainty')).toBeDefined()
    expect(screen.getByText('Get Started')).toBeDefined()
  })

  it('calls onComplete when Get Started is clicked on last step', () => {
    localStorage.removeItem('neurosim_onboarding_seen')
    const onComplete = vi.fn()
    render(<OnboardingTour onComplete={onComplete} />)

    // Navigate to last step
    for (let i = 0; i < 4; i++) {
      fireEvent.click(screen.getByText('Next'))
    }

    // Click Get Started
    fireEvent.click(screen.getByText('Get Started'))

    expect(onComplete).toHaveBeenCalledTimes(1)
    expect(localStorage.getItem('neurosim_onboarding_seen')).toBe('true')
  })

  it('goes back to previous step on Back click', () => {
    localStorage.removeItem('neurosim_onboarding_seen')
    const onComplete = vi.fn()
    render(<OnboardingTour onComplete={onComplete} />)

    // Go to step 2
    fireEvent.click(screen.getByText('Next'))
    expect(screen.getByText('Tri-Engine Input')).toBeDefined()

    // Go back to step 1
    fireEvent.click(screen.getByText('Back'))
    expect(screen.getByText('Welcome to NeuroSim v3.0')).toBeDefined()
  })

  it('disables Back button on first step', () => {
    localStorage.removeItem('neurosim_onboarding_seen')
    const onComplete = vi.fn()
    render(<OnboardingTour onComplete={onComplete} />)

    const backBtn = screen.getByText('Back')
    expect(backBtn).toBeDefined()
    // First step should have disabled back button
    expect((backBtn as HTMLButtonElement).disabled).toBe(true)
  })

  it('does not close when clicking inside the dialog', () => {
    localStorage.removeItem('neurosim_onboarding_seen')
    const onComplete = vi.fn()
    render(<OnboardingTour onComplete={onComplete} />)

    // Click inside the dialog (which has e.stopPropagation())
    const dialog = screen.getByRole('dialog')
    fireEvent.click(dialog)

    // Should NOT close because e.stopPropagation() is called
    expect(screen.getByText('Welcome to NeuroSim v3.0')).toBeDefined()
    expect(onComplete).not.toHaveBeenCalled()
  })

  it('has accessible dialog attributes', () => {
    localStorage.removeItem('neurosim_onboarding_seen')
    render(<OnboardingTour onComplete={vi.fn()} />)

    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeDefined()
    expect(dialog.getAttribute('aria-modal')).toBe('true')
    expect(dialog.getAttribute('aria-labelledby')).toBe('onboarding-title')
  })
})
