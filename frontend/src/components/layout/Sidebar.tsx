import { NavLink } from "react-router-dom";
import { LayoutDashboard, Bot, Play, Cpu, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { to: "/", icon: LayoutDashboard, label: "Board" },
  { to: "/agents", icon: Bot, label: "Agents" },
  { to: "/runtime", icon: Play, label: "Runtime" },
  { to: "/models", icon: Cpu, label: "Models" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export default function Sidebar() {
  return (
    <aside className="flex w-14 flex-col items-center gap-1 border-r border-border bg-sidebar py-3">
      {links.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            cn(
              "flex size-10 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:text-foreground hover:bg-accent",
              isActive && "bg-primary/10 text-primary"
            )
          }
          title={label}
        >
          <Icon className="size-5" />
        </NavLink>
      ))}
    </aside>
  );
}
