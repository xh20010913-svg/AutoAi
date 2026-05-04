import { Moon, Sun, Monitor, Play, Zap, LogOut, Terminal } from "lucide-react"
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
    <header className="flex h-12 items-center justify-between border-b-2 border-border bg-background px-4">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center h-6 w-6 bg-primary/15 border border-primary/30">
          <Zap className="h-3.5 w-3.5 text-primary fill-primary" />
        </div>
        <span className="text-xs font-semibold text-primary tracking-[0.15em] uppercase font-mono">AutoAi</span>
        <div className="h-4 w-px bg-border" />
        <span className="text-[11px] text-muted-foreground font-mono">autai.local</span>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 mr-2">
          <div className="flex items-center gap-1 text-[9px] font-mono text-muted-foreground/40 uppercase tracking-wider">
            <div className="h-1 w-1 bg-emerald-500" style={{ animation: "pixelBlink 3s step-end infinite" }} />
            AGT
          </div>
          <div className="text-muted-foreground/20">|</div>
          <div className="flex items-center gap-1 text-[9px] font-mono text-muted-foreground/40 uppercase tracking-wider">
            <div className="h-1 w-1 bg-primary" style={{ animation: "pixelBlink 2s step-end infinite 0.5s" }} />
            API
          </div>
        </div>

        {user && (
          <span className="text-xs text-muted-foreground">{user.username}</span>
        )}
        <button className="inline-flex items-center gap-1.5 bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:opacity-90 transition-all pixel-border-sm hover:pixel-glow">
          <Play className="h-3 w-3" />
          Run
        </button>
        <button
          onClick={cycleTheme}
          className="inline-flex items-center justify-center p-1.5 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors border-2 border-transparent hover:border-border"
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
