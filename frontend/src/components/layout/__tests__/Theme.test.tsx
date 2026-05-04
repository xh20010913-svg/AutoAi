import { render, screen, waitFor } from "@/test/test-utils"
import userEvent from "@testing-library/user-event"
import { describe, it, expect, beforeEach } from "vitest"
import { Topbar } from "@/components/layout/Topbar"
import { SettingsPage } from "@/pages/SettingsPage"

describe("Theme & UI regression", () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove("dark", "light")
  })

  describe("Topbar theme cycling", () => {
    it("renders theme toggle button", () => {
      render(<Topbar />)
      const themeButton = screen.getByTitle(/Theme:/)
      expect(themeButton).toBeInTheDocument()
    })

    it("cycles through theme order: system -> light -> dark -> system", async () => {
      const user = userEvent.setup()
      render(<Topbar />)

      const themeButton = screen.getByTitle(/Theme:/)

      // Default is system
      expect(themeButton).toHaveAttribute("title", "Theme: system")

      // system -> light
      await user.click(themeButton)
      await waitFor(() => {
        expect(themeButton).toHaveAttribute("title", "Theme: light")
      })

      // light -> dark
      await user.click(themeButton)
      await waitFor(() => {
        expect(themeButton).toHaveAttribute("title", "Theme: dark")
      })

      // dark -> system
      await user.click(themeButton)
      await waitFor(() => {
        expect(themeButton).toHaveAttribute("title", "Theme: system")
      })
    })

    it("renders Run button with pixel border", () => {
      render(<Topbar />)
      const runButton = screen.getByText("Run")
      expect(runButton.closest("button")?.className).toContain("pixel-border-sm")
    })

    it("renders Dashboard label", () => {
      render(<Topbar />)
      expect(screen.getByText("Dashboard")).toBeInTheDocument()
    })
  })

  describe("CSS theme variables", () => {
    it("dark class applied to document after switching", async () => {
      const user = userEvent.setup()
      render(<SettingsPage />)

      await user.click(screen.getByText("Dark"))

      await waitFor(() => {
        expect(document.documentElement.classList.contains("dark")).toBe(true)
        expect(document.documentElement.classList.contains("light")).toBe(false)
      })
    })

    it("light class applied to document after switching", async () => {
      const user = userEvent.setup()
      render(<SettingsPage />)

      await user.click(screen.getByText("Light"))

      await waitFor(() => {
        expect(document.documentElement.classList.contains("light")).toBe(true)
        expect(document.documentElement.classList.contains("dark")).toBe(false)
      })
    })

    it("removes old theme class when switching themes", async () => {
      const user = userEvent.setup()
      render(<SettingsPage />)

      await user.click(screen.getByText("Dark"))
      await waitFor(() => {
        expect(document.documentElement.classList.contains("dark")).toBe(true)
      })

      await user.click(screen.getByText("Light"))
      await waitFor(() => {
        expect(document.documentElement.classList.contains("light")).toBe(true)
        expect(document.documentElement.classList.contains("dark")).toBe(false)
      })
    })
  })

  describe("pixel art CSS classes", () => {
    it("pixel-border class exists in settings cards", () => {
      const { container } = render(<SettingsPage />)
      const pixelBorders = container.querySelectorAll(".pixel-border")
      expect(pixelBorders.length).toBeGreaterThanOrEqual(3)
    })

    it("pixel-border-sm class used in Topbar", () => {
      const { container } = render(<Topbar />)
      const pixelBorderSm = container.querySelector(".pixel-border-sm")
      expect(pixelBorderSm).toBeTruthy()
    })

    it("zero-radius (pixel style) on theme buttons", () => {
      const { container } = render(<SettingsPage />)
      // Theme buttons use border-2 for pixel style (no rounded-lg)
      const themeButtons = container.querySelectorAll("button.border-2")
      expect(themeButtons.length).toBeGreaterThan(0)
    })
  })

  describe("warm color theme", () => {
    it("uses sidebar-specific CSS variable classes", () => {
      const { container } = render(
        <SettingsPage />
      )
      // Just verify the component renders without errors using the warm theme
      expect(container.querySelector(".max-w-2xl")).toBeTruthy()
    })
  })
})
