import { render, screen, waitFor } from "@/test/test-utils"
import userEvent from "@testing-library/user-event"
import { describe, it, expect, beforeEach } from "vitest"
import { SettingsPage } from "@/pages/SettingsPage"

describe("SettingsPage", () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove("dark", "light")
  })

  describe("page structure", () => {
    it("renders the settings title", () => {
      render(<SettingsPage />)
      expect(screen.getByText("Settings")).toBeInTheDocument()
    })

    it("renders General section", () => {
      render(<SettingsPage />)
      expect(screen.getByText("General")).toBeInTheDocument()
      expect(screen.getByText("Basic workspace configuration")).toBeInTheDocument()
    })

    it("renders Appearance section", () => {
      render(<SettingsPage />)
      expect(screen.getByText("Appearance")).toBeInTheDocument()
      expect(screen.getByText("Customize how AutoAI looks")).toBeInTheDocument()
    })

    it("renders Runtime section", () => {
      render(<SettingsPage />)
      expect(screen.getByText("Runtime")).toBeInTheDocument()
      expect(screen.getByText("Agent runtime configuration")).toBeInTheDocument()
    })
  })

  describe("theme switching", () => {
    it("renders Light, Dark, System theme buttons", () => {
      render(<SettingsPage />)
      expect(screen.getByText("Light")).toBeInTheDocument()
      expect(screen.getByText("Dark")).toBeInTheDocument()
      expect(screen.getByText("System")).toBeInTheDocument()
    })

    it("switches to dark theme on click", async () => {
      const user = userEvent.setup()
      render(<SettingsPage />)

      await user.click(screen.getByText("Dark"))

      await waitFor(() => {
        expect(document.documentElement.classList.contains("dark")).toBe(true)
      })
    })

    it("switches to light theme on click", async () => {
      const user = userEvent.setup()
      document.documentElement.classList.add("dark")
      render(<SettingsPage />)

      await user.click(screen.getByText("Light"))

      await waitFor(() => {
        expect(document.documentElement.classList.contains("light")).toBe(true)
      })
    })

    it("saves theme preference to localStorage", async () => {
      const user = userEvent.setup()
      render(<SettingsPage />)

      await user.click(screen.getByText("Dark"))

      await waitFor(() => {
        expect(localStorage.getItem("theme")).toBe("dark")
      })
    })

    it("highlights the active theme button with primary border", async () => {
      const user = userEvent.setup()
      render(<SettingsPage />)

      const darkButton = screen.getByText("Dark").closest("button")!
      await user.click(darkButton)

      await waitFor(() => {
        expect(darkButton.className).toContain("border-primary")
      })
    })
  })

  describe("general settings", () => {
    it("renders workspace name input with default value", () => {
      render(<SettingsPage />)
      const input = screen.getByDisplayValue("AutoAI")
      expect(input).toBeInTheDocument()
    })

    it("renders timeout input with default value", () => {
      render(<SettingsPage />)
      const input = screen.getByDisplayValue("300")
      expect(input).toBeInTheDocument()
    })
  })

  describe("runtime settings", () => {
    it("renders max concurrent agents input", () => {
      render(<SettingsPage />)
      const input = screen.getByDisplayValue("8")
      expect(input).toBeInTheDocument()
    })

    it("renders log level select with options", () => {
      render(<SettingsPage />)
      const select = screen.getByRole("combobox")
      expect(select).toBeInTheDocument()
      expect(screen.getByText("Debug")).toBeInTheDocument()
      expect(screen.getByText("Info")).toBeInTheDocument()
      expect(screen.getByText("Warn")).toBeInTheDocument()
      expect(screen.getByText("Error")).toBeInTheDocument()
    })

    it("renders auto-restart toggle", () => {
      render(<SettingsPage />)
      expect(screen.getByText("Auto-restart on failure")).toBeInTheDocument()
      expect(screen.getByText("Automatically restart agents that crash")).toBeInTheDocument()
    })
  })

  describe("pixel art styling", () => {
    it("uses pixel-border class on setting sections", () => {
      const { container } = render(<SettingsPage />)
      const pixelBorders = container.querySelectorAll(".pixel-border")
      expect(pixelBorders.length).toBeGreaterThanOrEqual(3)
    })

    it("uses monospace font on inputs", () => {
      const { container } = render(<SettingsPage />)
      const monoInputs = container.querySelectorAll(".font-mono")
      expect(monoInputs.length).toBeGreaterThan(0)
    })

    it("uses 2px border on inputs", () => {
      const { container } = render(<SettingsPage />)
      const borderedInputs = container.querySelectorAll(".border-2")
      expect(borderedInputs.length).toBeGreaterThan(0)
    })
  })
})
