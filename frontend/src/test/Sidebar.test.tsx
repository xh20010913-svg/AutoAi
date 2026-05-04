import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Sidebar } from '@/components/layout/Sidebar'

function renderSidebar() {
  return render(
    <BrowserRouter>
      <Sidebar />
    </BrowserRouter>
  )
}

describe('Sidebar', () => {
  it('renders the AutoAI logo text', () => {
    renderSidebar()
    expect(screen.getByText('AutoAI')).toBeInTheDocument()
  })

  it('renders version text', () => {
    renderSidebar()
    expect(screen.getByText('v0.2')).toBeInTheDocument()
  })

  it('renders all navigation items', () => {
    renderSidebar()
    expect(screen.getByText('Board')).toBeInTheDocument()
    expect(screen.getByText('Agents')).toBeInTheDocument()
    expect(screen.getByText('Runtime')).toBeInTheDocument()
    expect(screen.getByText('Models')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('renders navigation links with correct hrefs', () => {
    renderSidebar()
    const boardLink = screen.getByText('Board').closest('a')
    const agentsLink = screen.getByText('Agents').closest('a')
    const runtimeLink = screen.getByText('Runtime').closest('a')
    const modelsLink = screen.getByText('Models').closest('a')
    const settingsLink = screen.getByText('Settings').closest('a')

    expect(boardLink).toHaveAttribute('href', '/')
    expect(agentsLink).toHaveAttribute('href', '/agents')
    expect(runtimeLink).toHaveAttribute('href', '/runtime')
    expect(modelsLink).toHaveAttribute('href', '/models')
    expect(settingsLink).toHaveAttribute('href', '/settings')
  })

  it('renders System Online indicator', () => {
    renderSidebar()
    expect(screen.getByText('System Online')).toBeInTheDocument()
  })

  it('renders navigation section label', () => {
    renderSidebar()
    expect(screen.getByText('Navigation')).toBeInTheDocument()
  })

  it('renders pixel logo grid', () => {
    const { container } = renderSidebar()
    const grid = container.querySelector('.grid.grid-cols-4')
    expect(grid).toBeInTheDocument()
  })

  it('has correct sidebar width', () => {
    const { container } = renderSidebar()
    const aside = container.querySelector('aside')
    expect(aside).toHaveClass('w-56')
  })
})
