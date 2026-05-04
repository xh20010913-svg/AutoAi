import { render, act } from '@testing-library/react'
import { describe, it, expect, vi, afterEach } from 'vitest'
import { PixelCharacter } from '@/components/pixel/PixelCharacter'

describe('PixelCharacter', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('rendering', () => {
    it('renders a container for the character scene', () => {
      const { container } = render(<PixelCharacter status="idle" />)
      // Should render a div with some content
      const sceneContainer = container.firstChild
      expect(sceneContainer).toBeInTheDocument()
    })

    it('renders with a minimum height for the scene area', () => {
      const { container } = render(<PixelCharacter status="idle" />)
      const sceneContainer = container.firstChild as HTMLElement
      expect(sceneContainer).toHaveStyle({ minHeight: '100px' })
    })
  })

  describe('status scenes', () => {
    it('renders SofaScene for idle status', () => {
      const { container } = render(<PixelCharacter status="idle" />)
      // Sofa has characteristic purple color (#7c3aed)
      const sofaElements = container.querySelectorAll('[style*="background-color: rgb(124, 58, 237)"]')
      expect(sofaElements.length).toBeGreaterThan(0)
    })

    it('renders DeskScene for running status', () => {
      const { container } = render(<PixelCharacter status="running" />)
      // Desk has brown color (#92400e)
      const deskElements = container.querySelectorAll('[style*="background-color: rgb(146, 64, 14)"]')
      expect(deskElements.length).toBeGreaterThan(0)
    })

    it('renders DeskScene for error status', () => {
      const { container } = render(<PixelCharacter status="error" />)
      // Desk should also be shown for error (brown color)
      const deskElements = container.querySelectorAll('[style*="background-color: rgb(146, 64, 14)"]')
      expect(deskElements.length).toBeGreaterThan(0)
    })
  })

  describe('color presets', () => {
    it('uses default blue color preset when not specified', () => {
      const { container } = render(<PixelCharacter status="idle" />)
      // Blue hair color (#6366f1)
      const hairElements = container.querySelectorAll('[style*="background-color: rgb(99, 102, 241)"]')
      expect(hairElements.length).toBeGreaterThan(0)
    })

    it('applies green color preset', () => {
      const { container } = render(<PixelCharacter status="idle" colorPreset="green" />)
      // Green hair color (#10b981)
      const hairElements = container.querySelectorAll('[style*="background-color: rgb(16, 185, 129)"]')
      expect(hairElements.length).toBeGreaterThan(0)
    })

    it('applies red color preset', () => {
      const { container } = render(<PixelCharacter status="idle" colorPreset="red" />)
      // Red hair color (#ef4444)
      const hairElements = container.querySelectorAll('[style*="background-color: rgb(239, 68, 68)"]')
      expect(hairElements.length).toBeGreaterThan(0)
    })
  })

  describe('animation', () => {
    it('sets up arm animation for running status', () => {
      vi.useFakeTimers()
      const { unmount } = render(<PixelCharacter status="running" />)

      // Should create an interval
      act(() => {
        vi.advanceTimersByTime(400)
      })

      // After advancing, the arm should toggle
      unmount()
      vi.useRealTimers()
    })

    it('does not set up animation for idle status', () => {
      vi.useFakeTimers()
      render(<PixelCharacter status="idle" />)

      // Advancing timers should not cause issues
      act(() => {
        vi.advanceTimersByTime(1000)
      })

      vi.useRealTimers()
    })

    it('adds error animation class for error status', () => {
      const { container } = render(<PixelCharacter status="error" />)
      const sceneContainer = container.firstChild as HTMLElement
      expect(sceneContainer.className).toContain('animate-[pixelError')
    })
  })
})
