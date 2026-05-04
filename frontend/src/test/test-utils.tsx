import { type ReactNode } from "react"
import { render, type RenderOptions } from "@testing-library/react"
import { BrowserRouter } from "react-router-dom"
import { ThemeProvider } from "@/context/theme-context"

function AllProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </ThemeProvider>
  )
}

function customRender(ui: React.ReactElement, options?: Omit<RenderOptions, "wrapper">) {
  return render(ui, { wrapper: AllProviders, ...options })
}

export * from "@testing-library/react"
export { customRender as render }
