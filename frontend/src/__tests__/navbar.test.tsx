import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, cleanup, fireEvent } from '@testing-library/react'

// Mutable mock state — updated per test
const mockAuth = vi.hoisted(() => ({
  isSignedIn: false,
  user: null,
  isLoaded: true,
  signOut: vi.fn(),
}))

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => '/',
}))

// Mock auth context with mutable state
vi.mock('../lib/auth-context', () => ({
  useAuth: () => ({
    isSignedIn: mockAuth.isSignedIn,
    user: mockAuth.user,
    isLoaded: mockAuth.isLoaded,
    signOut: mockAuth.signOut,
  }),
}))

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  Brain: () => <div data-testid="icon-brain" />,
  Menu: () => <div data-testid="icon-menu" />,
  X: () => <div data-testid="icon-x" />,
  LogOut: () => <div data-testid="icon-logout" />,
  BarChart2: () => <div data-testid="icon-chart" />,
  DollarSign: () => <div data-testid="icon-dollar" />,
  TrendingUp: () => <div data-testid="icon-trending" />,
  Zap: () => <div data-testid="icon-zap" />,
}))

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  // Reset auth state to defaults
  mockAuth.isSignedIn = false
  mockAuth.user = null
  mockAuth.isLoaded = true
  mockAuth.signOut = vi.fn()
})

describe('Navbar', () => {
  it('renders the brand name and logo', async () => {
    const { Navbar } = await import('../app/components/Navbar')
    render(<Navbar />)
    expect(screen.getByText('NeuroSim')).toBeDefined()
    expect(screen.getByText('v3.0')).toBeDefined()
  })

  it('shows navigation links for signed-out users', async () => {
    const { Navbar } = await import('../app/components/Navbar')
    render(<Navbar />)
    expect(screen.getByText('Features')).toBeDefined()
    expect(screen.getByText('How it works')).toBeDefined()
    expect(screen.getByText('Pricing')).toBeDefined()
    expect(screen.getByText('Predict')).toBeDefined()
  })

  it('shows auth buttons for signed-out users', async () => {
    const { Navbar } = await import('../app/components/Navbar')
    render(<Navbar />)
    expect(screen.getByText('Sign in')).toBeDefined()
    expect(screen.getByText('Get Started Free')).toBeDefined()
  })

  it('shows dashboard and analytics links when signed in', async () => {
    mockAuth.isSignedIn = true
    mockAuth.user = { email: 'test@test.com', user_metadata: { name: 'Test User' } } as any
    const { Navbar } = await import('../app/components/Navbar')
    render(<Navbar />)
    expect(screen.getByText('Analytics')).toBeDefined()
  })

  it('shows user name when signed in', async () => {
    mockAuth.isSignedIn = true
    mockAuth.user = { email: 'test@test.com', user_metadata: { name: 'Test User' } } as any
    const { Navbar } = await import('../app/components/Navbar')
    render(<Navbar />)
    expect(screen.getByText('Test User')).toBeDefined()
  })

  it('calls signOut when logout button is clicked', async () => {
    mockAuth.isSignedIn = true
    mockAuth.user = { email: 'test@test.com', user_metadata: { name: 'Test' } } as any
    const { Navbar } = await import('../app/components/Navbar')
    render(<Navbar />)
    
    const logoutBtn = screen.getByTestId('icon-logout').closest('button')
    expect(logoutBtn).not.toBeNull()
    fireEvent.click(logoutBtn!)
    expect(mockAuth.signOut).toHaveBeenCalledTimes(1)
  })

  it('toggles mobile menu', async () => {
    const { Navbar } = await import('../app/components/Navbar')
    render(<Navbar />)

    // Desktop nav should show Features
    const featuresLinks = screen.getAllByText('Features')
    expect(featuresLinks.length).toBeGreaterThanOrEqual(1)

    // Click the mobile menu toggle
    const menuToggle = screen.getByTestId('icon-menu').closest('button')
    expect(menuToggle).not.toBeNull()
    fireEvent.click(menuToggle!)
  })

  it('shows sign-in buttons for signed-out users', async () => {
    const { Navbar } = await import('../app/components/Navbar')
    render(<Navbar />)
    expect(screen.getByText('Sign in')).toBeDefined()
    expect(screen.getByText('Get Started Free')).toBeDefined()
  })

  it('returns null when not loaded', async () => {
    mockAuth.isLoaded = false
    const { Navbar } = await import('../app/components/Navbar')
    const { container } = render(<Navbar />)
    expect(container.innerHTML).toBe('')
  })
})
