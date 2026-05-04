import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act } from '@testing-library/react'
import { PixelCharacter } from './PixelCharacter'
import type { ColorPreset } from './PixelCharacter'

describe('PixelCharacter', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // --- Rendering ---
  it('renders without crashing for all statuses', () => {
    for (const status of ['running', 'idle', 'error'] as const) {
      const { container, unmount } = render(<PixelCharacter status={status} />)
      expect(container.querySelector('.rounded-md')).toBeTruthy()
      unmount()
    }
  })

  it('renders with default colorPreset (blue)', () => {
    const { container } = render(<PixelCharacter status="running" />)
    // Blue preset shirt color: #3b82f6 → rgb(59, 130, 246)
    // (ARMS_UP frame has no hair pixels, so check shirt instead)
    expect(container.innerHTML).toContain('rgb(59, 130, 246)')
  })

  // --- Status → scene mapping ---
  it('shows SofaScene when idle', () => {
    const { container } = render(<PixelCharacter status="idle" />)
    // Sofa scene has purple sofa: #7c3aed → rgb(124, 58, 237)
    expect(container.innerHTML).toContain('rgb(124, 58, 237)')
  })

  it('shows DeskScene when running', () => {
    const { container } = render(<PixelCharacter status="running" />)
    // Desk scene has brown desk: #92400e → rgb(146, 64, 14)
    expect(container.innerHTML).toContain('rgb(146, 64, 14)')
  })

  it('shows DeskScene when error', () => {
    const { container } = render(<PixelCharacter status="error" />)
    expect(container.innerHTML).toContain('rgb(146, 64, 14)')
  })

  // --- Error animation ---
  it('applies error animation class when status is error', () => {
    const { container } = render(<PixelCharacter status="error" />)
    const wrapper = container.querySelector('.rounded-md')
    expect(wrapper?.className).toContain('pixelError')
  })

  it('does not apply error animation class when status is running', () => {
    const { container } = render(<PixelCharacter status="running" />)
    const wrapper = container.querySelector('.rounded-md')
    expect(wrapper?.className).not.toContain('pixelError')
  })

  it('does not apply error animation class when status is idle', () => {
    const { container } = render(<PixelCharacter status="idle" />)
    const wrapper = container.querySelector('.rounded-md')
    expect(wrapper?.className).not.toContain('pixelError')
  })

  // --- Color presets ---
  const colorPresets: ColorPreset[] = ['blue', 'green', 'purple', 'amber', 'pink', 'cyan', 'red', 'teal']

  it.each(colorPresets)('renders with colorPreset "%s" without crashing', (preset) => {
    const { container } = render(<PixelCharacter status="running" colorPreset={preset} />)
    expect(container.querySelector('.rounded-md')).toBeTruthy()
  })

  // --- Arm animation (running state) ---
  it('alternates arm frames when running', () => {
    const { container } = render(<PixelCharacter status="running" />)

    // Get initial arm pixel grid
    const grids = container.querySelectorAll('[style*="grid-template-columns"]')
    expect(grids.length).toBeGreaterThan(0)

    const getFirstArmPixel = () => {
      const grid = container.querySelectorAll('[style*="grid-template-columns"]')[0]
      return grid?.innerHTML
    }

    const initial = getFirstArmPixel()

    // Advance timer by 400ms to trigger arm toggle
    act(() => {
      vi.advanceTimersByTime(400)
    })

    const afterToggle = getFirstArmPixel()
    // After toggling, the frame should change (ARMS_UP ↔ ARMS_DOWN)
    expect(afterToggle).not.toBe(initial)
  })

  it('does not alternate arms when idle', () => {
    const { container } = render(<PixelCharacter status="idle" />)

    const grids = container.querySelectorAll('[style*="grid-template-columns"]')
    const initialHTML = grids[0]?.innerHTML

    act(() => {
      vi.advanceTimersByTime(800)
    })

    const afterHTML = container.querySelectorAll('[style*="grid-template-columns"]')[0]?.innerHTML
    expect(afterHTML).toBe(initialHTML)
  })

  it('does not alternate arms when error', () => {
    const { container } = render(<PixelCharacter status="error" />)

    const grids = container.querySelectorAll('[style*="grid-template-columns"]')
    const initialHTML = grids[0]?.innerHTML

    act(() => {
      vi.advanceTimersByTime(800)
    })

    const afterHTML = container.querySelectorAll('[style*="grid-template-columns"]')[0]?.innerHTML
    expect(afterHTML).toBe(initialHTML)
  })

  // --- Pixel grid structure ---
  it('renders a pixel grid with correct dimensions (8x10)', () => {
    const { container } = render(<PixelCharacter status="idle" />)
    const grid = container.querySelector('[style*="grid-template-columns"]')
    expect(grid).toBeTruthy()
    // 8 columns × 10 rows = 80 child divs
    expect(grid?.children.length).toBe(80)
  })

  it('uses correct pixel size (5px)', () => {
    const { container } = render(<PixelCharacter status="idle" />)
    const grid = container.querySelector('[style*="grid-template-columns"]') as HTMLElement
    expect(grid?.style.gridTemplateColumns).toBe('repeat(8, 5px)')
    expect(grid?.style.gridTemplateRows).toBe('repeat(10, 5px)')
  })

  // --- Skin color consistency ---
  it('uses consistent skin color across all presets', () => {
    for (const preset of colorPresets) {
      const { container, unmount } = render(<PixelCharacter status="running" colorPreset={preset} />)
      // Skin: #fbbf24 → rgb(251, 191, 36)
      expect(container.innerHTML).toContain('rgb(251, 191, 36)')
      unmount()
    }
  })

  // --- Minimum height ---
  it('has minimum height of 100px', () => {
    const { container } = render(<PixelCharacter status="running" />)
    const wrapper = container.querySelector('.rounded-md') as HTMLElement
    expect(wrapper?.style.minHeight).toBe('100px')
  })
})
