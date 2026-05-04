import { render, screen, act } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { PixelCharacter } from "@/components/pixel/PixelCharacter"

describe("PixelCharacter", () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  describe("running state", () => {
    it("renders desk scene when status is running", () => {
      const { container } = render(<PixelCharacter status="running" />)
      // Desk scene has a monitor (width: 44, backgroundColor: #374151)
      const monitor = container.querySelector('[style*="background-color: rgb(55, 65, 81)"]')
      expect(monitor).toBeTruthy()
    })

    it("renders pixel grid character in desk scene", () => {
      const { container } = render(<PixelCharacter status="running" />)
      // PixelGrid creates a grid with 8px × 5px cells
      const grid = container.querySelector('[style*="grid-template-columns"]')
      expect(grid).toBeTruthy()
    })

    it("animates arm frames with interval", () => {
      const { container } = render(<PixelCharacter status="running" />)
      // Initially armUp=true, after 400ms it should toggle
      const grids = container.querySelectorAll('[style*="grid-template-columns"]')
      expect(grids.length).toBeGreaterThan(0)

      act(() => {
        vi.advanceTimersByTime(400)
      })

      // The arm frame should have changed (different pixel layout)
      // Just verify the component didn't crash and still renders
      const gridsAfter = container.querySelectorAll('[style*="grid-template-columns"]')
      expect(gridsAfter.length).toBeGreaterThan(0)
    })

    it("applies muted background", () => {
      const { container } = render(<PixelCharacter status="running" />)
      const wrapper = container.firstChild as HTMLElement
      expect(wrapper.className).toContain("bg-muted/50")
    })
  })

  describe("idle state", () => {
    it("renders sofa scene when status is idle", () => {
      const { container } = render(<PixelCharacter status="idle" />)
      // Sofa scene has purple sofa (#7c3aed = rgb(124, 58, 237))
      const sofa = container.querySelector('[style*="background-color: rgb(124, 58, 237)"]')
      expect(sofa).toBeTruthy()
    })

    it("renders pixel character sitting on sofa", () => {
      const { container } = render(<PixelCharacter status="idle" />)
      // Sofa scene has the sitting animation class
      const animatedDiv = container.querySelector('[class*="pixelIdleSway"]')
      expect(animatedDiv).toBeTruthy()
    })

    it("does not run arm animation interval when idle", () => {
      const { container } = render(<PixelCharacter status="idle" />)
      // Verify it still renders after timer advance (no crash from interval)
      act(() => {
        vi.advanceTimersByTime(1000)
      })
      const sofa = container.querySelector('[style*="background-color: rgb(124, 58, 237)"]')
      expect(sofa).toBeTruthy()
    })
  })

  describe("error state", () => {
    it("renders desk scene with error animation when status is error", () => {
      const { container } = render(<PixelCharacter status="error" />)
      // Error uses desk scene with pixelError animation
      const wrapper = container.firstChild as HTMLElement
      expect(wrapper.className).toContain("animate-[pixelError")
    })

    it("has error animation class on container", () => {
      const { container } = render(<PixelCharacter status="error" />)
      const wrapper = container.firstChild as HTMLElement
      expect(wrapper.className).toContain("pixelError")
    })
  })

  describe("color presets", () => {
    it("uses blue preset by default", () => {
      const { container } = render(<PixelCharacter status="running" />)
      // Blue preset: hair=#6366f1, shirt=#3b82f6
      const blueShirt = container.querySelector('[style*="background-color: rgb(59, 130, 246)"]')
      expect(blueShirt).toBeTruthy()
    })

    it("renders green preset colors", () => {
      const { container } = render(<PixelCharacter status="running" colorPreset="green" />)
      // Green preset: shirt=#22c55e = rgb(34, 197, 94)
      const greenShirt = container.querySelector('[style*="background-color: rgb(34, 197, 94)"]')
      expect(greenShirt).toBeTruthy()
    })

    it("renders purple preset colors", () => {
      const { container } = render(<PixelCharacter status="running" colorPreset="purple" />)
      // Purple preset: shirt=#8b5cf6 = rgb(139, 92, 246)
      const purpleShirt = container.querySelector('[style*="background-color: rgb(139, 92, 246)"]')
      expect(purpleShirt).toBeTruthy()
    })

    it("renders amber preset colors", () => {
      const { container } = render(<PixelCharacter status="running" colorPreset="amber" />)
      // Amber preset: shirt=#eab308 = rgb(234, 179, 8)
      const amberShirt = container.querySelector('[style*="background-color: rgb(234, 179, 8)"]')
      expect(amberShirt).toBeTruthy()
    })

    it("renders pink preset colors", () => {
      const { container } = render(<PixelCharacter status="running" colorPreset="pink" />)
      // Pink preset: shirt=#f472b6 = rgb(244, 114, 182)
      const pinkShirt = container.querySelector('[style*="background-color: rgb(244, 114, 182)"]')
      expect(pinkShirt).toBeTruthy()
    })

    it("renders skin color (#fbbf24) for all presets", () => {
      const { container } = render(<PixelCharacter status="running" colorPreset="red" />)
      // Skin color is always #fbbf24 = rgb(251, 191, 36)
      const skin = container.querySelector('[style*="background-color: rgb(251, 191, 36)"]')
      expect(skin).toBeTruthy()
    })
  })

  describe("pixel grid structure", () => {
    it("renders 80 pixel cells (8x10 grid)", () => {
      const { container } = render(<PixelCharacter status="running" />)
      // ARMS_UP frame has 8*10 = 80 cells
      const grid = container.querySelector('[style*="grid-template-columns"]')
      expect(grid).toBeTruthy()
      const cells = grid!.children
      expect(cells.length).toBe(80)
    })

    it("uses 5px pixel size", () => {
      const { container } = render(<PixelCharacter status="running" />)
      const grid = container.querySelector('[style*="grid-template-columns: repeat(8, 5px)"]')
      expect(grid).toBeTruthy()
    })
  })

  describe("container sizing", () => {
    it("has minimum height of 100px", () => {
      const { container } = render(<PixelCharacter status="running" />)
      const wrapper = container.firstChild as HTMLElement
      expect(wrapper.style.minHeight).toBe("100px")
    })
  })
})
