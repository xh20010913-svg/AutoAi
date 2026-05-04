import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, act } from '@testing-library/react'
import { PixelCharacter } from '@/components/pixel/PixelCharacter'

describe('PixelCharacter', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  it('renders desk scene when status is running', () => {
    const { container } = render(<PixelCharacter status="running" />)
    const sceneContainer = container.querySelector('[style*="width: 130"]')
    expect(sceneContainer).toBeInTheDocument()
  })

  it('renders sofa scene when status is idle', () => {
    const { container } = render(<PixelCharacter status="idle" />)
    const sceneContainer = container.querySelector('[style*="width: 130"]')
    expect(sceneContainer).toBeInTheDocument()
  })

  it('applies error animation class when status is error', () => {
    const { container } = render(<PixelCharacter status="error" />)
    const outerDiv = container.querySelector('div.mt-3')
    expect(outerDiv?.className).toContain('pixelError')
  })

  it('does not apply error animation when status is running', () => {
    const { container } = render(<PixelCharacter status="running" />)
    const outerDiv = container.querySelector('div.mt-3')
    expect(outerDiv?.className).not.toContain('pixelError')
  })

  it('does not apply error animation when status is idle', () => {
    const { container } = render(<PixelCharacter status="idle" />)
    const outerDiv = container.querySelector('div.mt-3')
    expect(outerDiv?.className).not.toContain('pixelError')
  })

  it('renders colored pixels with the correct preset in running state', () => {
    const { container } = render(<PixelCharacter status="running" />)
    // ARMS_UP frame has shirt pixels (3) -> blue preset shirt = #3b82f6 = rgb(59, 130, 246)
    const coloredPixels = container.querySelectorAll('div[style*="background-color"]')
    expect(coloredPixels.length).toBeGreaterThan(0)
    const hasShirtColor = Array.from(coloredPixels).some(
      (el) => el.getAttribute('style')?.includes('59, 130, 246') ||
              el.getAttribute('style')?.includes('#3b82f6')
    )
    expect(hasShirtColor).toBe(true)
  })

  it('renders hair color pixels in idle state', () => {
    const { container } = render(<PixelCharacter status="idle" />)
    // SITTING_FRAME has hair pixels (1) -> blue preset hair = #6366f1 = rgb(99, 102, 241)
    const coloredPixels = container.querySelectorAll('div[style*="background-color"]')
    const hasHairColor = Array.from(coloredPixels).some(
      (el) => el.getAttribute('style')?.includes('99, 102, 241') ||
              el.getAttribute('style')?.includes('#6366f1')
    )
    expect(hasHairColor).toBe(true)
  })

  it('renders with different color presets', () => {
    const presets = ['green', 'purple', 'amber', 'pink', 'cyan', 'red', 'teal'] as const
    for (const preset of presets) {
      const { container, unmount } = render(<PixelCharacter status="running" colorPreset={preset} />)
      const pixels = container.querySelectorAll('div[style*="background-color"]')
      expect(pixels.length).toBeGreaterThan(0)
      unmount()
    }
  })

  it('renders a pixel grid with correct dimensions (8 columns)', () => {
    const { container } = render(<PixelCharacter status="running" />)
    const grid = container.querySelector('[style*="grid-template-columns"]')
    expect(grid).toBeInTheDocument()
    expect(grid?.getAttribute('style')).toContain('repeat(8')
  })

  it('has typing animation class in running state', () => {
    const { container } = render(<PixelCharacter status="running" />)
    const typingChar = container.querySelector('[class*="pixelArmType"]')
    expect(typingChar).toBeInTheDocument()
  })

  it('has sway animation class in idle state', () => {
    const { container } = render(<PixelCharacter status="idle" />)
    const swayElement = container.querySelector('[class*="pixelIdleSway"]')
    expect(swayElement).toBeInTheDocument()
  })

  it('has monitor glow animation in desk scene', () => {
    const { container } = render(<PixelCharacter status="running" />)
    const screen = container.querySelector('[style*="animation: pixelMonitorGlow"]')
    expect(screen).toBeInTheDocument()
  })

  it('cleans up interval on unmount', () => {
    const clearIntervalSpy = vi.spyOn(global, 'clearInterval')
    const { unmount } = render(<PixelCharacter status="running" />)
    unmount()
    expect(clearIntervalSpy).toHaveBeenCalled()
    clearIntervalSpy.mockRestore()
  })

  it('does not set interval when not running', () => {
    const setIntervalSpy = vi.spyOn(global, 'setInterval')
    render(<PixelCharacter status="idle" />)
    const typingCalls = setIntervalSpy.mock.calls.filter(
      (call) => call[1] === 400
    )
    expect(typingCalls.length).toBe(0)
    setIntervalSpy.mockRestore()
  })

  it('renders skin color pixels', () => {
    const { container } = render(<PixelCharacter status="idle" />)
    const skinPixel = container.querySelector('div[style*="background-color: rgb(251, 191, 36)"]')
    expect(skinPixel).toBeInTheDocument()
  })

  it('renders pants color pixels', () => {
    const { container } = render(<PixelCharacter status="idle" />)
    const pantsPixel = container.querySelector('div[style*="background-color: rgb(71, 85, 105)"]')
    expect(pantsPixel).toBeInTheDocument()
  })
})
