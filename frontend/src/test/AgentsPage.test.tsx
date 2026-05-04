import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AgentsPage } from '@/pages/AgentsPage'

describe('AgentsPage', () => {
  it('renders the page title', () => {
    render(<AgentsPage />)
    expect(screen.getByText('Agents')).toBeInTheDocument()
  })

  it('shows total agent count', () => {
    render(<AgentsPage />)
    expect(screen.getByText('Total: 8')).toBeInTheDocument()
  })

  it('shows running agent count', () => {
    render(<AgentsPage />)
    expect(screen.getByText(/Running: 4/)).toBeInTheDocument()
  })

  it('shows error agent count when errors exist', () => {
    render(<AgentsPage />)
    expect(screen.getByText(/Error: 1/)).toBeInTheDocument()
  })

  it('renders all 8 agent cards with unique names', () => {
    render(<AgentsPage />)
    // Use getAllByText since "Project Manager" also appears as a role
    expect(screen.getAllByText('Project Manager').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Backend Dev #1')).toBeInTheDocument()
    expect(screen.getByText('Backend Dev #2')).toBeInTheDocument()
    expect(screen.getByText('Backend Dev #3')).toBeInTheDocument()
    expect(screen.getByText('Frontend Dev')).toBeInTheDocument()
    expect(screen.getByText('Tester #1')).toBeInTheDocument()
    expect(screen.getByText('Tester #2')).toBeInTheDocument()
    expect(screen.getByText('Tester #3')).toBeInTheDocument()
  })

  it('displays agent roles', () => {
    render(<AgentsPage />)
    // Backend Developer appears as role in 3 cards
    const backendRoles = screen.getAllByText('Backend Developer')
    expect(backendRoles.length).toBe(3)
    // QA Tester appears as role in 3 cards
    const qaRoles = screen.getAllByText('QA Tester')
    expect(qaRoles.length).toBe(3)
    // Frontend Developer appears as role in 1 card
    expect(screen.getByText('Frontend Developer')).toBeInTheDocument()
  })

  it('displays model names for multiple agents', () => {
    render(<AgentsPage />)
    // claude-sonnet-4-6 appears in multiple cards
    const sonnet = screen.getAllByText('claude-sonnet-4-6')
    expect(sonnet.length).toBeGreaterThanOrEqual(1)
    const haiku = screen.getAllByText('claude-haiku-4-5')
    expect(haiku.length).toBeGreaterThanOrEqual(1)
  })

  it('displays completed task counts', () => {
    render(<AgentsPage />)
    expect(screen.getByText('23 tasks done')).toBeInTheDocument()
    expect(screen.getByText('45 tasks done')).toBeInTheDocument()
  })

  it('renders PixelCharacter for each agent', () => {
    const { container } = render(<AgentsPage />)
    // Each agent card should have a pixel grid (8 columns)
    const grids = container.querySelectorAll('[style*="grid-template-columns: repeat(8, 5px)"]')
    expect(grids.length).toBe(8)
  })

  it('hovers reveal action buttons', () => {
    const { container } = render(<AgentsPage />)
    const cards = container.querySelectorAll('.group')

    // Before hover, no action buttons should be visible
    expect(screen.queryByTitle('Start')).not.toBeInTheDocument()

    // Hover over first card
    fireEvent.mouseEnter(cards[0])
    expect(screen.getByTitle('Start')).toBeInTheDocument()
    expect(screen.getByTitle('Stop')).toBeInTheDocument()
    expect(screen.getByTitle('Settings')).toBeInTheDocument()

    // Mouse leave hides buttons
    fireEvent.mouseLeave(cards[0])
    expect(screen.queryByTitle('Start')).not.toBeInTheDocument()
  })
})
