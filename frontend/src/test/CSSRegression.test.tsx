import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider } from '@/context/theme-context'
import { SettingsPage } from '@/pages/SettingsPage'
import { AgentsPage } from '@/pages/AgentsPage'
import { ModelsPage } from '@/pages/ModelsPage'
import { RuntimePage } from '@/pages/RuntimePage'

describe('UI Regression: CSS & Theming', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark', 'light')
  })

  it('pixel-border class is applied to agent cards', () => {
    const { container } = render(<AgentsPage />)
    const pixelBorders = container.querySelectorAll('.pixel-border')
    expect(pixelBorders.length).toBeGreaterThan(0)
  })

  it('pixel-border class is applied to settings sections', () => {
    const { container } = render(
      <ThemeProvider>
        <SettingsPage />
      </ThemeProvider>
    )
    const pixelBorders = container.querySelectorAll('.pixel-border')
    expect(pixelBorders.length).toBeGreaterThan(0)
  })

  it('pixel-border class is applied to model cards', () => {
    const { container } = render(<ModelsPage />)
    const pixelBorders = container.querySelectorAll('.pixel-border')
    expect(pixelBorders.length).toBeGreaterThan(0)
  })

  it('pixel-border-sm class is applied to runtime status badge', () => {
    const { container } = render(<RuntimePage />)
    const smallBorders = container.querySelectorAll('.pixel-border-sm')
    expect(smallBorders.length).toBeGreaterThan(0)
  })

  it('theme switching updates document root class', () => {
    render(
      <ThemeProvider>
        <SettingsPage />
      </ThemeProvider>
    )

    fireEvent.click(screen.getByText('Dark'))
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    fireEvent.click(screen.getByText('Light'))
    expect(document.documentElement.classList.contains('light')).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('font-mono class is used for model tags', () => {
    const { container } = render(<ModelsPage />)
    const monoElements = container.querySelectorAll('.font-mono')
    expect(monoElements.length).toBeGreaterThan(0)
  })

  it('animate-pulse class is used for running status indicators', () => {
    const { container } = render(<AgentsPage />)
    const pulseElements = container.querySelectorAll('.animate-pulse')
    expect(pulseElements.length).toBeGreaterThan(0)
  })

  it('settings inputs use font-mono class', () => {
    const { container } = render(
      <ThemeProvider>
        <SettingsPage />
      </ThemeProvider>
    )
    const monoInputs = container.querySelectorAll('input.font-mono')
    expect(monoInputs.length).toBeGreaterThan(0)
  })

  it('log entries use monospace font class', () => {
    const { container } = render(<RuntimePage />)
    const monoContainer = container.querySelector('.font-mono')
    expect(monoContainer).toBeInTheDocument()
  })

  it('theme persistence works across re-renders', () => {
    const { rerender } = render(
      <ThemeProvider>
        <SettingsPage />
      </ThemeProvider>
    )

    fireEvent.click(screen.getByText('Dark'))
    expect(localStorage.getItem('theme')).toBe('dark')

    rerender(
      <ThemeProvider>
        <SettingsPage />
      </ThemeProvider>
    )

    // Theme should still be dark after re-render
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})
