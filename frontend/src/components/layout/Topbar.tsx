import { Moon, Sun, Monitor, Play, LogOut } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { useTheme } from "@/context/theme-context"
import { useAuth } from "@/context/auth-context"

export function Topbar() {
  const { theme, setTheme, resolvedTheme } = useTheme()
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const cycleTheme = () => {
    const order: Array<"light" | "dark" | "system"> = ["light", "dark", "system"]
    const next = order[(order.indexOf(theme) + 1) % order.length]
    setTheme(next)
  }

  const handleLogout = () => {
    logout()
    navigate("/login")
  }

  const ThemeIcon = theme === "system" ? Monitor : resolvedTheme === "dark" ? Moon : Sun

  return (
    <header className="flex h-12 items-center justify-between border-b border-border bg-background px-4">
      <div className="flex items-center gap-2">
        <span className="text-base font-semibold">AutoAI</span>
      </div>
      <div className="flex items-center gap-3">
        {user && (
          <span className="text-xs text-muted-foreground">{user.username}</span>
        )}
        <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:opacity-90 transition-opacity">
          <Play className="h-3 w-3" />
          Run
        </button>
        <button
          onClick={cycleTheme}
          className="inline-flex items-center justify-center rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
          title={`Theme: ${theme}`}
        >
          <ThemeIcon className="h-4 w-4" />
        </button>
        <button
          onClick={handleLogout}
          className="inline-flex items-center justify-center rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
          title="Logout"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}
