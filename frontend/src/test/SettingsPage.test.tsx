import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider } from '@/context/theme-context'
import { SettingsPage } from '@/pages/SettingsPage'

function renderSettings() {
  return render(
    <ThemeProvider>
      <SettingsPage />
    </ThemeProvider>
  )
}

describe('SettingsPage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('renders the page title', () => {
    renderSettings()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('renders General section', () => {
    renderSettings()
    expect(screen.getByText('General')).toBeInTheDocument()
    expect(screen.getByText('Workspace Name')).toBeInTheDocument()
    expect(screen.getByText('Default Agent Timeout (seconds)')).toBeInTheDocument()
  })

  it('renders Appearance section with theme options', () => {
    renderSettings()
    expect(screen.getByText('Appearance')).toBeInTheDocument()
    expect(screen.getByText('Theme')).toBeInTheDocument()
    expect(screen.getByText('Light')).toBeInTheDocument()
    expect(screen.getByText('Dark')).toBeInTheDocument()
    expect(screen.getByText('System')).toBeInTheDocument()
  })

  it('renders Runtime section', () => {
    renderSettings()
    expect(screen.getByText('Runtime')).toBeInTheDocument()
    expect(screen.getByText('Max Concurrent Agents')).toBeInTheDocument()
    expect(screen.getByText('Log Level')).toBeInTheDocument()
    expect(screen.getByText('Auto-restart on failure')).toBeInTheDocument()
  })

  it('has workspace name input with default value', () => {
    renderSettings()
    const input = screen.getByDisplayValue('AutoAI')
    expect(input).toBeInTheDocument()
  })

  it('has timeout input with default value 300', () => {
    renderSettings()
    const input = screen.getByDisplayValue('300')
    expect(input).toBeInTheDocument()
  })

  it('has max concurrent agents input with default value 8', () => {
    renderSettings()
    const input = screen.getByDisplayValue('8')
    expect(input).toBeInTheDocument()
  })

  it('switches theme when theme buttons are clicked', () => {
    renderSettings()
    fireEvent.click(screen.getByText('Dark'))
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    fireEvent.click(screen.getByText('Light'))
    expect(document.documentElement.classList.contains('light')).toBe(true)
  })

  it('renders log level select with options', () => {
    renderSettings()
    const select = screen.getByRole('combobox')
    expect(select).toBeInTheDocument()
    expect(screen.getByText('Debug')).toBeInTheDocument()
    expect(screen.getByText('Info')).toBeInTheDocument()
    expect(screen.getByText('Warn')).toBeInTheDocument()
    expect(screen.getByText('Error')).toBeInTheDocument()
  })

  it('renders auto-restart toggle', () => {
    renderSettings()
    const toggle = screen.getByText('Auto-restart on failure')
    expect(toggle).toBeInTheDocument()
    expect(screen.getByText('Automatically restart agents that crash')).toBeInTheDocument()
  })

  it('highlights the active theme button', () => {
    renderSettings()
    const darkButton = screen.getByText('Dark').closest('button')!
    fireEvent.click(darkButton)
    expect(darkButton).toHaveClass('border-primary')
  })
})
