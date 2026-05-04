import { NavLink } from "react-router-dom"
import { LayoutGrid, Bot, Play, Box, Settings } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/", icon: LayoutGrid, label: "Board", pixel: "▣" },
  { to: "/agents", icon: Bot, label: "Agents", pixel: "◈" },
  { to: "/runtime", icon: Play, label: "Runtime", pixel: "▶" },
  { to: "/models", icon: Box, label: "Models", pixel: "◫" },
  { to: "/settings", icon: Settings, label: "Settings", pixel: "⚙" },
]

function PixelLogo() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="relative h-8 w-8">
        {/* Pixel grid logo — 5x5 blocks with warm amber gradient */}
        <div className="grid grid-cols-5 gap-[1px] h-full w-full">
          <div className="bg-sidebar-primary" />
          <div className="bg-sidebar-primary" />
          <div className="bg-sidebar-primary" />
          <div className="bg-sidebar-primary/70" />
          <div className="bg-transparent" />
          <div className="bg-sidebar-primary" />
          <div className="bg-sidebar-primary/90" />
          <div className="bg-sidebar-primary/70" />
          <div className="bg-sidebar-primary/50" />
          <div className="bg-sidebar-primary/60" />
          <div className="bg-sidebar-primary/80" />
          <div className="bg-sidebar-primary/60" />
          <div className="bg-sidebar-primary/80" />
          <div className="bg-sidebar-primary/60" />
          <div className="bg-sidebar-primary/70" />
          <div className="bg-sidebar-primary/50" />
          <div className="bg-sidebar-primary/70" />
          <div className="bg-sidebar-primary/60" />
          <div className="bg-sidebar-primary/90" />
          <div className="bg-sidebar-primary" />
          <div className="bg-transparent" />
          <div className="bg-sidebar-primary/60" />
          <div className="bg-sidebar-primary/70" />
          <div className="bg-sidebar-primary" />
          <div className="bg-sidebar-primary" />
        </div>
      </div>
      <div>
        <span className="text-sm font-bold text-sidebar-primary tracking-[0.15em] uppercase">
          AutoAI
        </span>
        <div className="text-[9px] text-sidebar-foreground/40 tracking-[0.25em] uppercase -mt-0.5 font-mono">
          v0.2 // agent runtime
        </div>
      </div>
    </div>
  )
}

export function Sidebar() {
  return (
    <aside className="flex h-full w-56 flex-col border-r-2 border-sidebar-border bg-sidebar-background relative">
      {/* Subtle scanline overlay on sidebar */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.02]"
        style={{
          background: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.1) 2px, rgba(255,255,255,0.1) 4px)"
        }}
      />

      <div className="flex h-14 items-center px-4 border-b-2 border-sidebar-border relative">
        <PixelLogo />
        {/* Pixel dot accent */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex gap-[3px]">
          <div className="h-[5px] w-[5px] bg-sidebar-primary/60" />
          <div className="h-[5px] w-[5px] bg-sidebar-primary/40" />
          <div className="h-[5px] w-[5px] bg-sidebar-primary/20" />
        </div>
      </div>

      <div className="px-3 pt-4 pb-2">
        <span className="text-[10px] font-medium text-sidebar-foreground/35 tracking-[0.2em] uppercase font-mono">
          // Navigation
        </span>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 px-2">
        {navItems.map(({ to, icon: Icon, label, pixel }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 px-3 py-2 text-sm transition-all relative group",
                isActive
                  ? "bg-sidebar-accent text-sidebar-primary font-medium border-l-[3px] border-sidebar-primary"
                  : "text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-foreground border-l-[3px] border-transparent"
              )
            }
          >
            {({ isActive }) => (
              <>
                <span className={cn(
                  "text-[13px] font-mono w-4 text-center transition-colors",
                  isActive ? "text-sidebar-primary" : "text-sidebar-foreground/30 group-hover:text-sidebar-foreground/50"
                )}>
                  {pixel}
                </span>
                <Icon className="h-4 w-4" />
                <span>{label}</span>
                {isActive && (
                  <div className="absolute right-2 h-1.5 w-1.5 bg-sidebar-primary" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Pixel decorative divider */}
      <div className="mx-3 my-2 h-px bg-gradient-to-r from-sidebar-border via-sidebar-primary/30 to-sidebar-border" />

      <div className="border-t-2 border-sidebar-border p-3">
        <div className="flex items-center gap-2 text-[10px] text-sidebar-foreground/30 tracking-wider uppercase font-mono">
          <div className="h-1.5 w-1.5 bg-emerald-500" style={{ animation: "pixelBlink 2s step-end infinite" }} />
          System Online
        </div>
        <div className="mt-1.5 flex gap-[2px]">
          {Array.from({ length: 20 }).map((_, i) => (
            <div
              key={i}
              className="h-[3px] flex-1"
              style={{
                backgroundColor: i < 14
                  ? `oklch(0.74 0.18 55 / ${0.3 + (i / 20) * 0.7})`
                  : "oklch(0.57 0.22 27 / 0.5)"
              }}
            />
          ))}
        </div>
        <div className="text-[8px] text-sidebar-foreground/20 font-mono mt-1 tracking-wider">
          CAPACITY 70%
        </div>
      </div>
    </aside>
  )
}
