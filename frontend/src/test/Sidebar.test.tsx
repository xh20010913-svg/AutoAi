import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { Sidebar } from '@/components/layout/Sidebar'

function renderSidebar(initialRoute = '/') {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Sidebar />
    </MemoryRouter>
  )
}

describe('Sidebar', () => {
  describe('rendering', () => {
    it('renders the logo', () => {
      renderSidebar()
      expect(screen.getByText('AutoAI')).toBeInTheDocument()
    })

    it('renders version text', () => {
      renderSidebar()
      expect(screen.getByText('v0.2')).toBeInTheDocument()
    })

    it('renders navigation section label', () => {
      renderSidebar()
      expect(screen.getByText('Navigation')).toBeInTheDocument()
    })

    it('renders system status indicator', () => {
      renderSidebar()
      expect(screen.getByText('System Online')).toBeInTheDocument()
    })
  })

  describe('navigation links', () => {
    const navItems = [
      { label: 'Board', to: '/' },
      { label: 'Agents', to: '/agents' },
      { label: 'Runtime', to: '/runtime' },
      { label: 'Models', to: '/models' },
      { label: 'Settings', to: '/settings' },
    ]

    it.each(navItems)('renders $label navigation link', ({ label }) => {
      renderSidebar()
      expect(screen.getByText(label)).toBeInTheDocument()
    })

    it('renders all 5 navigation links', () => {
      renderSidebar()
      const nav = screen.getByRole('navigation')
      const links = nav.querySelectorAll('a')
      expect(links).toHaveLength(5)
    })
  })

  describe('active route', () => {
    it('highlights Board link when on root path', () => {
      renderSidebar('/')
      // The active link should have the active class
      const boardLink = screen.getByText('Board').closest('a')
      expect(boardLink?.className).toContain('bg-sidebar-accent')
    })

    it('highlights Agents link when on /agents', () => {
      renderSidebar('/agents')
      const agentsLink = screen.getByText('Agents').closest('a')
      expect(agentsLink?.className).toContain('bg-sidebar-accent')
    })

    it('highlights Settings link when on /settings', () => {
      renderSidebar('/settings')
      const settingsLink = screen.getByText('Settings').closest('a')
      expect(settingsLink?.className).toContain('bg-sidebar-accent')
    })

    it('does not highlight Board when on /agents', () => {
      renderSidebar('/agents')
      const boardLink = screen.getByText('Board').closest('a')
      expect(boardLink?.className).toContain('text-sidebar-foreground/70')
    })
  })
})
