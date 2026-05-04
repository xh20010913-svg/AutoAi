import { Moon, Sun, Monitor, Play, Zap, Terminal } from "lucide-react"
import { useTheme } from "@/context/theme-context"

export function Topbar() {
  const { theme, setTheme, resolvedTheme } = useTheme()

  const cycleTheme = () => {
    const order: Array<"light" | "dark" | "system"> = ["light", "dark", "system"]
    const next = order[(order.indexOf(theme) + 1) % order.length]
    setTheme(next)
  }

  const ThemeIcon = theme === "system" ? Monitor : resolvedTheme === "dark" ? Moon : Sun

  return (
    <header className="flex h-12 items-center justify-between border-b-2 border-border bg-background px-4 relative">
      {/* Pixel dash decoration along bottom edge */}
      <div className="absolute bottom-0 left-0 right-0 h-[2px]">
        <div className="h-full w-full" style={{
          background: "repeating-linear-gradient(90deg, var(--primary) 0px, var(--primary) 6px, transparent 6px, transparent 12px)",
          opacity: 0.25
        }} />
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <div className="flex items-center justify-center h-6 w-6 bg-primary/15 border border-primary/30">
            <Zap className="h-3.5 w-3.5 text-primary fill-primary" />
          </div>
          <span className="text-xs font-semibold text-primary tracking-[0.15em] uppercase font-mono">Dashboard</span>
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-1.5">
          <Terminal className="h-3 w-3 text-muted-foreground/50" />
          <span className="text-[11px] text-muted-foreground font-mono">autai.local</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Pixel status indicators */}
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

        <button className="inline-flex items-center gap-1.5 bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:opacity-90 transition-all pixel-border-sm hover:pixel-glow">
          <Play className="h-3 w-3" />
          <span className="font-mono tracking-wider">RUN</span>
        </button>
        <button
          onClick={cycleTheme}
          className="inline-flex items-center justify-center p-1.5 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors border-2 border-transparent hover:border-border"
          title={`Theme: ${theme}`}
        >
          <ThemeIcon className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}
