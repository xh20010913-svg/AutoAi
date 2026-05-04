import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { RuntimePage } from '@/pages/RuntimePage'

describe('RuntimePage', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  it('renders the page title', () => {
    render(<RuntimePage />)
    expect(screen.getByText('Runtime')).toBeInTheDocument()
  })

  it('shows running status by default', () => {
    render(<RuntimePage />)
    expect(screen.getByText('Running')).toBeInTheDocument()
  })

  it('renders initial mock logs', () => {
    render(<RuntimePage />)
    expect(screen.getByText('Runtime initialized successfully')).toBeInTheDocument()
    expect(screen.getByText('Loading agent configuration from workspace')).toBeInTheDocument()
  })

  it('shows all three log levels', () => {
    render(<RuntimePage />)
    expect(screen.getAllByText('[info]').length).toBeGreaterThan(0)
    expect(screen.getAllByText('[warn]').length).toBeGreaterThan(0)
    expect(screen.getAllByText('[error]').length).toBeGreaterThan(0)
  })

  it('toggles between running and stopped', () => {
    render(<RuntimePage />)
    expect(screen.getByText('Running')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Stop'))
    expect(screen.getByText('Stopped')).toBeInTheDocument()
    expect(screen.getByText('Run')).toBeInTheDocument()
  })

  it('filters logs by search query', () => {
    render(<RuntimePage />)
    const searchInput = screen.getByPlaceholderText('Search logs...')
    fireEvent.change(searchInput, { target: { value: 'timeout' } })
    expect(screen.getByText("Agent 'Backend Dev #3' connection timeout after 30s")).toBeInTheDocument()
    expect(screen.queryByText('Runtime initialized successfully')).not.toBeInTheDocument()
  })

  it('shows all logs when search is cleared', () => {
    render(<RuntimePage />)
    const searchInput = screen.getByPlaceholderText('Search logs...')
    fireEvent.change(searchInput, { target: { value: 'timeout' } })
    fireEvent.change(searchInput, { target: { value: '' } })
    expect(screen.getByText('Runtime initialized successfully')).toBeInTheDocument()
  })

  it('renders search input', () => {
    render(<RuntimePage />)
    expect(screen.getByPlaceholderText('Search logs...')).toBeInTheDocument()
  })

  it('has correct log level color classes', () => {
    const { container } = render(<RuntimePage />)
    const infoLevel = container.querySelector('.text-amber-300')
    expect(infoLevel).toBeInTheDocument()
    const warnLevel = container.querySelector('.text-yellow-400')
    expect(warnLevel).toBeInTheDocument()
    const errorLevel = container.querySelector('.text-red-400')
    expect(errorLevel).toBeInTheDocument()
  })

  it('does not add logs when stopped', () => {
    const { container } = render(<RuntimePage />)
    fireEvent.click(screen.getByText('Stop'))

    // Count log rows by their flex gap container
    const countLogRows = () => container.querySelectorAll('.flex.gap-3').length
    const countAfterStop = countLogRows()

    act(() => {
      vi.advanceTimersByTime(6000)
    })

    expect(countLogRows()).toBe(countAfterStop)
  })
})
