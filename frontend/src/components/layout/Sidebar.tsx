import { NavLink } from "react-router-dom"
import { LayoutGrid, Bot, Play, Box, Settings } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/", icon: LayoutGrid, label: "Board" },
  { to: "/agents", icon: Bot, label: "Agents" },
  { to: "/runtime", icon: Play, label: "Runtime" },
  { to: "/models", icon: Box, label: "Models" },
  { to: "/settings", icon: Settings, label: "Settings" },
]

export function Sidebar() {
  return (
    <aside className="flex h-full w-56 flex-col border-r border-sidebar-border bg-sidebar-background">
      <div className="flex h-12 items-center px-4 border-b border-sidebar-border">
        <span className="text-sm font-semibold text-sidebar-foreground">
          AutoAI
        </span>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-2">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
