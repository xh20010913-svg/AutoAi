import { useState, useEffect, useCallback } from "react"
import { Bot, User, Code, TestTube, Briefcase, type LucideIcon } from "lucide-react"
import { AgentCard } from "@/components/AgentCard"
import { agentApi, type Agent as ApiAgent } from "@/lib/api"
import { connectWebSocket } from "@/lib/ws"
import { showToast } from "@/lib/toast"
import type { ColorPreset } from "@/components/pixel/PixelCharacter"

const roleIcons: Record<string, LucideIcon> = {
  backend: Code,
  frontend: User,
  tester: TestTube,
  project_manager: Briefcase,
  default: Bot,
}

const roleColorPresets: Record<string, ColorPreset> = {
  backend: "green",
  frontend: "pink",
  tester: "cyan",
  project_manager: "blue",
  default: "purple",
}

function toAgentCard(agent: ApiAgent) {
  return {
    id: agent.id,
    name: agent.name,
    role: agent.role,
    status: (agent.status === "running" || agent.status === "idle" || agent.status === "error"
      ? agent.status
      : "idle") as "idle" | "running" | "error",
    model: agent.model || "N/A",
    completedTasks: 0,
    icon: roleIcons[agent.role] ?? roleIcons.default,
    colorPreset: (roleColorPresets[agent.role] ?? roleColorPresets.default) as ColorPreset,
  }
}

export function AgentsPage() {
  const [agents, setAgents] = useState<ReturnType<typeof toAgentCard>[]>([])
  const [loading, setLoading] = useState(true)

  const loadAgents = useCallback(async () => {
    try {
      const data = await agentApi.list()
      setAgents(data.map(toAgentCard))
    } catch {
      showToast("Failed to load agents", "error")
    }
  }, [])

  useEffect(() => {
    loadAgents().finally(() => setLoading(false))
  }, [loadAgents])

  useEffect(() => {
    const unsubscribe = connectWebSocket((data) => {
      if (data.event === "agent_status_change") {
        loadAgents()
      }
    })
    return unsubscribe
  }, [loadAgents])

  const running = agents.filter((a) => a.status === "running").length
  const errored = agents.filter((a) => a.status === "error").length

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground font-mono">Loading agents...</p>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-lg font-semibold">Agents</h1>
          <span className="text-[10px] font-mono text-muted-foreground/40 tracking-wider uppercase">// agent roster</span>
        </div>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span className="font-mono text-xs">Total: {agents.length}</span>
          <span className="flex items-center gap-1.5 font-mono text-xs">
            <span className="h-2 w-2 bg-emerald-500 animate-pulse" />
            Running: {running}
          </span>
          {errored > 0 && (
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
              Error: {errored}
            </span>
          )}
        </div>
      </div>
      {agents.length === 0 ? (
        <p className="text-sm text-muted-foreground font-mono">No agents registered yet.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}
    </div>
  )
}
