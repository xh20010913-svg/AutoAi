import { NavLink } from "react-router-dom"
import { LayoutDashboard, LayoutGrid, Bot, Play, Box, Settings } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/board", icon: LayoutGrid, label: "Board" },
  { to: "/agents", icon: Bot, label: "Agents" },
  { to: "/runtime", icon: Play, label: "Runtime" },
  { to: "/models", icon: Box, label: "Models" },
  { to: "/settings", icon: Settings, label: "Settings" },
]

function PixelLogo() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="relative h-7 w-7">
        {/* Pixel grid logo — 4x4 blocks */}
        <div className="grid grid-cols-4 gap-[1px] h-full w-full">
          <div className="bg-sidebar-primary" />
          <div className="bg-sidebar-primary" />
          <div className="bg-sidebar-primary/60" />
          <div className="bg-transparent" />
          <div className="bg-sidebar-primary" />
          <div className="bg-sidebar-primary/80" />
          <div className="bg-sidebar-primary/40" />
          <div className="bg-sidebar-primary/60" />
          <div className="bg-sidebar-primary/60" />
          <div className="bg-sidebar-primary/40" />
          <div className="bg-sidebar-primary/80" />
          <div className="bg-sidebar-primary" />
          <div className="bg-transparent" />
          <div className="bg-sidebar-primary/60" />
          <div className="bg-sidebar-primary" />
          <div className="bg-sidebar-primary" />
        </div>
      </div>
      <div>
        <span className="text-sm font-bold text-sidebar-primary tracking-widest uppercase">
          AutoAI
        </span>
        <div className="text-[9px] text-sidebar-foreground/40 tracking-[0.2em] uppercase -mt-0.5">
          v0.2
        </div>
      </div>
    </div>
  )
}

export function Sidebar() {
  return (
    <aside className="flex h-full w-56 flex-col border-r-2 border-sidebar-border bg-sidebar-background">
      <div className="flex h-14 items-center px-4 border-b-2 border-sidebar-border">
        <PixelLogo />
      </div>
      <div className="px-3 pt-3 pb-1">
        <span className="text-[10px] font-medium text-sidebar-foreground/40 tracking-[0.15em] uppercase">
          Navigation
        </span>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5 px-2">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-3 py-2 text-sm transition-all",
                isActive
                  ? "bg-sidebar-accent text-sidebar-primary font-medium border-l-2 border-sidebar-primary"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground border-l-2 border-transparent"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t-2 border-sidebar-border p-3">
        <div className="flex items-center gap-2 text-[10px] text-sidebar-foreground/30 tracking-wider uppercase">
          <div className="h-1.5 w-1.5 bg-emerald-500" style={{ animation: "pixelBlink 2s step-end infinite" }} />
          System Online
        </div>
      </div>
    </aside>
  )
}
