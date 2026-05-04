import { render, screen } from "@/test/test-utils"
import { describe, it, expect } from "vitest"
import { Sidebar } from "@/components/layout/Sidebar"

describe("Sidebar", () => {
  describe("navigation links", () => {
    it("renders all 5 navigation links", () => {
      render(<Sidebar />)
      const links = screen.getAllByRole("link")
      expect(links).toHaveLength(5)
    })

    it("renders Board link with correct href", () => {
      render(<Sidebar />)
      const boardLink = screen.getByRole("link", { name: /Board/i })
      expect(boardLink).toHaveAttribute("href", "/")
    })

    it("renders Agents link with correct href", () => {
      render(<Sidebar />)
      const agentsLink = screen.getByRole("link", { name: /Agents/i })
      expect(agentsLink).toHaveAttribute("href", "/agents")
    })

    it("renders Runtime link with correct href", () => {
      render(<Sidebar />)
      const link = screen.getByRole("link", { name: /Runtime/i })
      expect(link).toHaveAttribute("href", "/runtime")
    })

    it("renders Models link with correct href", () => {
      render(<Sidebar />)
      const link = screen.getByRole("link", { name: /Models/i })
      expect(link).toHaveAttribute("href", "/models")
    })

    it("renders Settings link with correct href", () => {
      render(<Sidebar />)
      const link = screen.getByRole("link", { name: /Settings/i })
      expect(link).toHaveAttribute("href", "/settings")
    })

    it("all links are clickable (have href)", () => {
      render(<Sidebar />)
      const links = screen.getAllByRole("link")
      links.forEach((link) => {
        expect(link).toHaveAttribute("href")
      })
    })
  })

  describe("pixel logo", () => {
    it("renders AutoAI brand text", () => {
      render(<Sidebar />)
      expect(screen.getByText("AutoAI")).toBeInTheDocument()
    })

    it("renders version label v0.2", () => {
      render(<Sidebar />)
      expect(screen.getByText("v0.2")).toBeInTheDocument()
    })

    it("renders pixel grid logo (4x4 blocks)", () => {
      const { container } = render(<Sidebar />)
      const pixelGrid = container.querySelector(".grid.grid-cols-4")
      expect(pixelGrid).toBeTruthy()
      // 4x4 = 16 children
      expect(pixelGrid!.children.length).toBe(16)
    })
  })

  describe("pixel art styling", () => {
    it("uses pixel border on sidebar", () => {
      const { container } = render(<Sidebar />)
      const aside = container.querySelector("aside")
      expect(aside?.className).toContain("border-r-2")
      expect(aside?.className).toContain("border-sidebar-border")
    })

    it("renders Navigation section label", () => {
      render(<Sidebar />)
      expect(screen.getByText("Navigation")).toBeInTheDocument()
    })

    it("renders System Online status", () => {
      render(<Sidebar />)
      expect(screen.getByText("System Online")).toBeInTheDocument()
    })

    it("renders pixel blinking dot for status indicator", () => {
      const { container } = render(<Sidebar />)
      const statusDot = container.querySelector('[style*="pixelBlink"]')
      expect(statusDot).toBeTruthy()
    })

    it("uses sidebar background color class", () => {
      const { container } = render(<Sidebar />)
      const aside = container.querySelector("aside")
      expect(aside?.className).toContain("bg-sidebar-background")
    })
  })
})
