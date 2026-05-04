import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider, useTheme } from '@/context/theme-context'

function ThemeConsumer() {
  const { theme, setTheme, resolvedTheme } = useTheme()
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="resolved">{resolvedTheme}</span>
      <button onClick={() => setTheme('light')}>Light</button>
      <button onClick={() => setTheme('dark')}>Dark</button>
      <button onClick={() => setTheme('system')}>System</button>
    </div>
  )
}

describe('ThemeProvider', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark', 'light')
  })

  it('defaults to system theme when no stored preference', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    expect(screen.getByTestId('theme')).toHaveTextContent('system')
  })

  it('reads stored theme from localStorage', () => {
    localStorage.setItem('theme', 'dark')
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')
  })

  it('updates theme and persists to localStorage', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    fireEvent.click(screen.getByText('Light'))
    expect(screen.getByTestId('theme')).toHaveTextContent('light')
    expect(localStorage.getItem('theme')).toBe('light')
  })

  it('adds dark class to document when dark theme selected', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    fireEvent.click(screen.getByText('Dark'))
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(document.documentElement.classList.contains('light')).toBe(false)
  })

  it('adds light class to document when light theme selected', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    fireEvent.click(screen.getByText('Light'))
    expect(document.documentElement.classList.contains('light')).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('cycles through themes correctly', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )

    fireEvent.click(screen.getByText('Light'))
    expect(screen.getByTestId('theme')).toHaveTextContent('light')

    fireEvent.click(screen.getByText('Dark'))
    expect(screen.getByTestId('theme')).toHaveTextContent('dark')

    fireEvent.click(screen.getByText('System'))
    expect(screen.getByTestId('theme')).toHaveTextContent('system')
  })

  it('resolves system theme based on matchMedia', () => {
    // Default mock returns light (matches=false)
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    fireEvent.click(screen.getByText('System'))
    expect(screen.getByTestId('resolved')).toHaveTextContent('light')
  })

  it('removes previous theme class when switching', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    )
    fireEvent.click(screen.getByText('Dark'))
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    fireEvent.click(screen.getByText('Light'))
    expect(document.documentElement.classList.contains('light')).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('throws when useTheme is used outside ThemeProvider', () => {
    // Suppress error boundary console output
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<ThemeConsumer />)).toThrow(
      'useTheme must be used within ThemeProvider'
    )
    spy.mockRestore()
  })
})
