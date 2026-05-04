import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import { Bot } from 'lucide-react'
import { AgentCard, type Agent } from '@/components/AgentCard'

function mockAgent(overrides: Partial<Agent> = {}): Agent {
  return {
    id: 'agent-1',
    name: 'Test Agent',
    role: 'Developer',
    status: 'idle',
    model: 'claude-sonnet-4-6',
    completedTasks: 42,
    icon: Bot,
    colorPreset: 'blue',
    ...overrides,
  }
}

describe('AgentCard', () => {
  describe('rendering', () => {
    it('renders agent name and role', () => {
      render(<AgentCard agent={mockAgent()} />)
      expect(screen.getByText('Test Agent')).toBeInTheDocument()
      expect(screen.getByText('Developer')).toBeInTheDocument()
    })

    it('renders model name', () => {
      render(<AgentCard agent={mockAgent()} />)
      expect(screen.getByText('claude-sonnet-4-6')).toBeInTheDocument()
    })

    it('renders completed tasks count', () => {
      render(<AgentCard agent={mockAgent({ completedTasks: 42 })} />)
      expect(screen.getByText('42 tasks done')).toBeInTheDocument()
    })

    it('renders icon', () => {
      render(<AgentCard agent={mockAgent()} />)
      // The icon should be rendered as an SVG
      const icons = document.querySelectorAll('svg')
      expect(icons.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('status display', () => {
    it('renders idle agent without pulse animation', () => {
      render(<AgentCard agent={mockAgent({ status: 'idle' })} />)
      // The status dot for idle should have bg-zinc-500
      const statusDot = document.querySelector('.bg-zinc-500')
      expect(statusDot).toBeInTheDocument()
    })

    it('renders running agent with pulse animation', () => {
      render(<AgentCard agent={mockAgent({ status: 'running' })} />)
      const statusDot = document.querySelector('.bg-emerald-500')
      expect(statusDot).toBeInTheDocument()
    })

    it('renders error agent with pulse animation', () => {
      render(<AgentCard agent={mockAgent({ status: 'error' })} />)
      const statusDot = document.querySelector('.bg-red-500')
      expect(statusDot).toBeInTheDocument()
    })
  })

  describe('hover actions', () => {
    it('shows action buttons on hover', async () => {
      const user = userEvent.setup()
      render(<AgentCard agent={mockAgent()} />)

      // Buttons should not be visible initially
      expect(screen.queryByTitle('Start')).not.toBeInTheDocument()

      await user.hover(screen.getByText('Test Agent').closest('.group')!)

      // After hover, buttons should appear
      expect(screen.getByTitle('Start')).toBeInTheDocument()
      expect(screen.getByTitle('Stop')).toBeInTheDocument()
      expect(screen.getByTitle('Settings')).toBeInTheDocument()
    })

    it('hides action buttons on mouse leave', async () => {
      const user = userEvent.setup()
      render(<AgentCard agent={mockAgent()} />)

      const card = screen.getByText('Test Agent').closest('.group')!
      await user.hover(card)
      expect(screen.getByTitle('Start')).toBeInTheDocument()

      await user.unhover(card)
      expect(screen.queryByTitle('Start')).not.toBeInTheDocument()
    })
  })
})
