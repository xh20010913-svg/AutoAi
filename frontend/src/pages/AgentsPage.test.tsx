import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AgentsPage } from './AgentsPage'

describe('AgentsPage with PixelCharacter', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // --- Page structure ---
  it('renders the Agents heading', () => {
    render(<AgentsPage />)
    expect(screen.getByText('Agents', { selector: 'h1' })).toBeTruthy()
  })

  it('shows total agent count', () => {
    render(<AgentsPage />)
    expect(screen.getByText('Total: 8')).toBeTruthy()
  })

  it('shows running agent count', () => {
    render(<AgentsPage />)
    expect(screen.getByText(/Running: 4/)).toBeTruthy()
  })

  it('shows error agent count', () => {
    render(<AgentsPage />)
    expect(screen.getByText(/Error: 1/)).toBeTruthy()
  })

  // --- Agent cards ---
  it('renders all 8 agent cards with unique names', () => {
    render(<AgentsPage />)
    // Use h3 selector to avoid matching the role text in <p>
    const headings = screen.getAllByRole('heading', { level: 3 })
    expect(headings.length).toBe(8)

    const expectedNames = [
      'Project Manager',
      'Backend Dev #1',
      'Backend Dev #2',
      'Backend Dev #3',
      'Frontend Dev',
      'Tester #1',
      'Tester #2',
      'Tester #3',
    ]
    const headingTexts = headings.map(h => h.textContent)
    for (const name of expectedNames) {
      expect(headingTexts).toContain(name)
    }
  })

  it('renders correct roles for agents', () => {
    render(<AgentsPage />)
    // Backend Developer appears 3 times, QA Tester 3 times
    expect(screen.getAllByText('Backend Developer').length).toBe(3)
    expect(screen.getAllByText('QA Tester').length).toBe(3)
    // Frontend Developer appears as role (and name includes it too)
    expect(screen.getAllByText('Frontend Developer').length).toBeGreaterThanOrEqual(1)
  })

  it('renders model info for each agent', () => {
    render(<AgentsPage />)
    expect(screen.getAllByText('claude-sonnet-4-6').length).toBeGreaterThan(0)
    expect(screen.getAllByText('claude-haiku-4-5').length).toBeGreaterThan(0)
  })

  it('renders completed tasks count', () => {
    render(<AgentsPage />)
    expect(screen.getByText('23 tasks done')).toBeTruthy()
    expect(screen.getByText('45 tasks done')).toBeTruthy()
  })

  // --- PixelCharacter integration ---
  it('renders pixel character grids for all agents', () => {
    const { container } = render(<AgentsPage />)
    const grids = container.querySelectorAll('[style*="grid-template-columns"]')
    // Each agent has 1 pixel character, each with a grid
    expect(grids.length).toBe(8)
  })

  it('renders desk scenes for running agents', () => {
    const { container } = render(<AgentsPage />)
    // Desk scenes have brown desk color: rgb(146, 64, 14)
    const deskElements = container.querySelectorAll('[style*="background-color: rgb(146, 64, 14)"]')
    // 4 running agents each have desk elements
    expect(deskElements.length).toBeGreaterThanOrEqual(4)
  })

  it('renders sofa scenes for idle agents', () => {
    const { container } = render(<AgentsPage />)
    // Sofa scenes have purple color: rgb(124, 58, 237)
    const sofaElements = container.querySelectorAll('[style*="background-color: rgb(124, 58, 237)"]')
    // 3 idle agents: Backend Dev #2, Tester #1, Tester #3
    expect(sofaElements.length).toBeGreaterThanOrEqual(3)
  })

  it('renders desk scene for error agent with error animation', () => {
    const { container } = render(<AgentsPage />)
    // Error agent uses desk scene with error animation
    const errorAnimated = container.querySelectorAll('[class*="pixelError"]')
    expect(errorAnimated.length).toBe(1)
  })

  // --- Color differentiation ---
  it('renders distinct shirt colors for different agents', () => {
    const { container } = render(<AgentsPage />)
    const html = container.innerHTML
    // Check that multiple different color presets are rendered (shirt colors)
    expect(html).toContain('rgb(59, 130, 246)')  // blue shirt
    expect(html).toContain('rgb(34, 197, 94)')   // green shirt
    expect(html).toContain('rgb(139, 92, 246)')  // purple shirt
    expect(html).toContain('rgb(234, 179, 8)')   // amber shirt
    expect(html).toContain('rgb(244, 114, 182)') // pink shirt
    expect(html).toContain('rgb(14, 165, 233)')  // cyan shirt
    expect(html).toContain('rgb(248, 113, 113)') // red shirt
    expect(html).toContain('rgb(45, 212, 191)')  // teal shirt
  })

  // --- Hover controls ---
  it('shows action buttons on hover', () => {
    const { container } = render(<AgentsPage />)
    const card = container.querySelector('.group')

    // Initially no action buttons visible
    expect(screen.queryByTitle('Start')).toBeNull()

    // Hover over the card
    fireEvent.mouseEnter(card!)

    expect(screen.getByTitle('Start')).toBeTruthy()
    expect(screen.getByTitle('Stop')).toBeTruthy()
    expect(screen.getByTitle('Settings')).toBeTruthy()
  })

  it('hides action buttons when mouse leaves', () => {
    const { container } = render(<AgentsPage />)
    const card = container.querySelector('.group')

    fireEvent.mouseEnter(card!)
    expect(screen.getByTitle('Start')).toBeTruthy()

    fireEvent.mouseLeave(card!)
    expect(screen.queryByTitle('Start')).toBeNull()
  })

  // --- Grid layout ---
  it('uses responsive grid layout', () => {
    const { container } = render(<AgentsPage />)
    const grid = container.querySelector('.grid')
    expect(grid?.className).toContain('grid-cols-1')
    expect(grid?.className).toContain('md:grid-cols-2')
    expect(grid?.className).toContain('lg:grid-cols-3')
  })

  // --- Status indicators ---
  it('renders status indicators for all agents', () => {
    const { container } = render(<AgentsPage />)
    // Running status: emerald green pulse dots (4 agents + 1 in header = 5)
    const runningDots = container.querySelectorAll('.bg-emerald-500')
    expect(runningDots.length).toBe(5)

    // Error status: red pulse dots (1 agent + 1 in header = 2)
    const errorDots = container.querySelectorAll('.bg-red-500')
    expect(errorDots.length).toBe(2)

    // Idle status: zinc dots (3 agents)
    const idleDots = container.querySelectorAll('.bg-zinc-500')
    expect(idleDots.length).toBe(3)
  })
})
