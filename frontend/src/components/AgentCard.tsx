import { Play, Square, Settings, type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { useState } from "react"
import { PixelCharacter } from "@/components/pixel/PixelCharacter"
import type { ColorPreset } from "@/components/pixel/PixelCharacter"

export interface Agent {
  id: string
  name: string
  role: string
  status: "idle" | "running" | "error"
  model: string
  completedTasks: number
  icon: LucideIcon
  colorPreset: ColorPreset
}

export function AgentCard({ agent }: { agent: Agent }) {
  const [hovered, setHovered] = useState(false)
  const Icon = agent.icon

  return (
    <div
      className="group relative bg-card p-4 transition-colors hover:border-primary pixel-border"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center bg-primary/15 text-primary border-2 border-primary/30">
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium text-card-foreground" style={{ fontFamily: "var(--font-heading, monospace)" }}>{agent.name}</h3>
            <div className={cn(
              "h-2 w-2 rounded-full",
              agent.status === "running" ? "bg-emerald-500 animate-pulse" :
              agent.status === "error" ? "bg-red-500 animate-pulse" :
              "bg-zinc-500"
            )} />
          </div>
          <p className="text-xs text-muted-foreground">{agent.role}</p>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
        <span className="font-mono text-[11px]">{agent.model}</span>
        <span>{agent.completedTasks} tasks done</span>
      </div>
      <PixelCharacter status={agent.status} colorPreset={agent.colorPreset} />
      {hovered && (
        <div className="absolute inset-x-0 bottom-0 flex justify-end gap-1 bg-gradient-to-t from-card p-2">
          <button className="p-1.5 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors border border-transparent hover:border-border" title="Start">
            <Play className="h-3.5 w-3.5" />
          </button>
          <button className="p-1.5 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors border border-transparent hover:border-border" title="Stop">
            <Square className="h-3.5 w-3.5" />
          </button>
          <button className="p-1.5 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors border border-transparent hover:border-border" title="Settings">
            <Settings className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  )
}
