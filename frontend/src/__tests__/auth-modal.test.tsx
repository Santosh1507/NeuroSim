import { describe, it, expect, afterEach, vi } from 'vitest'
import { render, screen, cleanup, fireEvent, waitFor } from '@testing-library/react'
import { AuthModal } from '../app/components/AuthModal'

// Mock useAuth from auth-context
const mockSignIn = vi.fn()
const mockSignUp = vi.fn()
const mockSignInAnonymously = vi.fn()

vi.mock('../lib/auth-context', () => ({
  useAuth: () => ({
    signIn: mockSignIn,
    signUp: mockSignUp,
    signInAnonymously: mockSignInAnonymously,
  }),
}))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('AuthModal', () => {
  it('renders nothing when closed', () => {
    const { container } = render(<AuthModal open={false} onClose={() => {}} />)
    // When closed, the AnimatePresence should not render anything
    expect(container.innerHTML).toBe('')
  })

  it('renders sign-in form when open', () => {
    render(<AuthModal open={true} onClose={() => {}} />)
    expect(screen.getByText('Sign in to NeuroSim')).toBeDefined()
    expect(screen.getByLabelText('Email')).toBeDefined()
    expect(screen.getByLabelText('Password')).toBeDefined()
    expect(screen.getByText('Sign in')).toBeDefined()
    expect(screen.getByText('Continue as guest')).toBeDefined()
  })

  it('switches to sign-up mode', () => {
    render(<AuthModal open={true} onClose={() => {}} />)
    // Click "Sign up" link to switch mode
    fireEvent.click(screen.getByText('Sign up'))
    expect(screen.getByText('Create your account')).toBeDefined()
    expect(screen.getByText('Create account')).toBeDefined()
  })

  it('switches back to sign-in mode from sign-up', () => {
    render(<AuthModal open={true} onClose={() => {}} />)
    // Switch to sign-up first
    fireEvent.click(screen.getByText('Sign up'))
    expect(screen.getByText('Create your account')).toBeDefined()

    // Switch back to sign-in
    fireEvent.click(screen.getByText('Sign in'))
    expect(screen.getByText('Sign in to NeuroSim')).toBeDefined()
  })

  it('calls onClose when clicking the overlay backdrop', () => {
    const onClose = vi.fn()
    render(<AuthModal open={true} onClose={onClose} />)
    // The backdrop is the first div with aria-hidden="true" inside the modal
    const backdrop = document.querySelector('[aria-hidden="true"]')
    expect(backdrop).toBeDefined()
    if (backdrop) {
      fireEvent.click(backdrop)
      expect(onClose).toHaveBeenCalledOnce()
    }
  })

  it('calls onClose when clicking the close button', () => {
    const onClose = vi.fn()
    render(<AuthModal open={true} onClose={onClose} />)
    const closeBtn = screen.getByLabelText('Close dialog')
    fireEvent.click(closeBtn)
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('submits sign-in form with email and password', async () => {
    mockSignIn.mockResolvedValue({ error: null })
    render(<AuthModal open={true} onClose={() => {}} />)

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByText('Sign in'))

    expect(mockSignIn).toHaveBeenCalledWith('test@example.com', 'password123')
  })

  it('submits sign-up form with email and password', async () => {
    mockSignUp.mockResolvedValue({ error: null })
    render(<AuthModal open={true} onClose={() => {}} />)

    // Switch to sign-up
    fireEvent.click(screen.getByText('Sign up'))

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'new@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'newpass123' },
    })
    fireEvent.click(screen.getByText('Create account'))

    expect(mockSignUp).toHaveBeenCalledWith('new@example.com', 'newpass123')
  })

  it('shows error message on sign-in failure', async () => {
    mockSignIn.mockResolvedValue({ error: 'Invalid credentials' })
    render(<AuthModal open={true} onClose={() => {}} />)

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'bad@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'wrong' },
    })
    fireEvent.click(screen.getByText('Sign in'))

    // Wait for the error alert to appear
    const errorAlert = await screen.findByText('Invalid credentials')
    expect(errorAlert).toBeDefined()
    expect(errorAlert.getAttribute('role')).toBe('alert')
  })

  it('shows success message and does NOT close on sign-up', async () => {
    mockSignUp.mockResolvedValue({ error: null })
    const onClose = vi.fn()
    render(<AuthModal open={true} onClose={onClose} />)

    fireEvent.click(screen.getByText('Sign up'))
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'new@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'newpass123' },
    })
    fireEvent.click(screen.getByText('Create account'))

    const successMsg = await screen.findByText(/Account created/)
    expect(successMsg).toBeDefined()
    // Sign-up should not close the modal
    expect(onClose).not.toHaveBeenCalled()
  })

  it('calls signInAnonymously when clicking Continue as guest', async () => {
    const onClose = vi.fn()
    mockSignInAnonymously.mockResolvedValue(undefined)
    render(<AuthModal open={true} onClose={onClose} />)

    fireEvent.click(screen.getByText('Continue as guest'))
    expect(mockSignInAnonymously).toHaveBeenCalledOnce()

    // handleDemo is async — onClose is called after await resolves
    // Use waitFor to flush pending microtasks
    await waitFor(() => {
      expect(onClose).toHaveBeenCalledOnce()
    })
  })

  it('sets aria-busy on submit button while loading', async () => {
    // Create a promise we can control
    let resolveSignIn!: (value: { error: null }) => void
    mockSignIn.mockReturnValue(new Promise((resolve) => {
      resolveSignIn = resolve
    }))

    render(<AuthModal open={true} onClose={() => {}} />)
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'test@test.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByText('Sign in'))

    const submitBtn = screen.getByText('Please wait...')
    expect(submitBtn).toBeDefined()
    expect(submitBtn.closest('button')?.getAttribute('aria-busy')).toBe('true')

    // Resolve to clean up
    resolveSignIn({ error: null })
  })
})
