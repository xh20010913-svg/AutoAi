import { Bot, Play, Square, Settings, User, Code, TestTube, Briefcase, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useState, useEffect } from "react"
import { PixelCharacter } from "@/components/pixel/PixelCharacter"
import type { ColorPreset } from "@/components/pixel/PixelCharacter"
import { api } from "@/lib/api"
import type { Agent } from "@/lib/api"

const roleIcons: Record<string, typeof Bot> = {
  "Project Manager": Briefcase,
  "Backend Developer": Code,
  "Frontend Developer": User,
  "QA Tester": TestTube,
}

const roleColors: Record<string, ColorPreset> = {
  "Project Manager": "blue",
  "Backend Developer": "green",
  "Frontend Developer": "pink",
  "QA Tester": "cyan",
}

function getIcon(role: string) {
  return roleIcons[role] ?? Bot
}

function getColorPreset(role: string, index: number): ColorPreset {
  const presets: ColorPreset[] = ["blue", "green", "purple", "amber", "pink", "cyan", "red", "teal"]
  return roleColors[role] ?? presets[index % presets.length]
}

function AgentCard({ agent, index }: { agent: Agent; index: number }) {
  const [hovered, setHovered] = useState(false)
  const Icon = getIcon(agent.role)
  const colorPreset = getColorPreset(agent.role, index)

  const pixelStatus = agent.status === "working" ? "running" : agent.status === "blocked" ? "error" : "idle"

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
              agent.status === "working" ? "bg-emerald-500 animate-pulse" :
              agent.status === "blocked" ? "bg-red-500 animate-pulse" :
              "bg-zinc-500"
            )} />
          </div>
          <p className="text-xs text-muted-foreground">{agent.role}</p>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
        <span className="font-mono text-[11px]">{agent.model}</span>
        <span>{agent.completed_tasks} tasks done</span>
      </div>
      <PixelCharacter status={pixelStatus} colorPreset={colorPreset} />
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

export function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function fetchAgents() {
      try {
        const data = await api.agents.listAll()
        if (!cancelled) {
          setAgents(data)
          setError(null)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load agents")
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchAgents()
    const interval = setInterval(fetchAgents, 5000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-20 text-sm text-red-500">
        {error}
      </div>
    )
  }

  const working = agents.filter((a) => a.status === "working").length
  const blocked = agents.filter((a) => a.status === "blocked").length

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-lg font-semibold mb-1">Agents</h1>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>Total: {agents.length}</span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 bg-emerald-500 animate-pulse" />
            Working: {working}
          </span>
          {blocked > 0 && (
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
              Blocked: {blocked}
            </span>
          )}
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent, i) => (
          <AgentCard key={agent.id} agent={agent} index={i} />
        ))}
      </div>
    </div>
  )
}
