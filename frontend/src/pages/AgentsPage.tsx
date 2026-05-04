import { Bot, Settings, User, Code, TestTube, Briefcase } from "lucide-react"
import { cn } from "@/lib/utils"
import { useState, useEffect, useCallback } from "react"
import { PixelCharacter } from "@/components/pixel/PixelCharacter"
import type { ColorPreset } from "@/components/pixel/PixelCharacter"
import { CreateAgentDialog } from "@/components/CreateAgentDialog"
import { AgentDetailPanel } from "@/components/AgentDetailPanel"
import { api, type Agent, type AgentStatus, type Role } from "@/lib/api"
import { useI18n } from "@/context/i18n-context"

const COLOR_PRESETS: ColorPreset[] = ["blue", "green", "purple", "amber", "pink", "cyan", "red", "teal"]

const ROLE_ICONS: Record<string, typeof Bot> = {
  "Project Manager": Briefcase,
  "Backend Developer": Code,
  "Frontend Developer": User,
  "QA Tester": TestTube,
}

function getPixelStatus(agentStatus: AgentStatus): "idle" | "running" | "error" {
  if (agentStatus === "error") return "error"
  if (agentStatus === "working") return "running"
  return "idle"
}

function AgentCard({ agent, index, onClick }: { agent: Agent; index: number; onClick: () => void }) {
  const { t } = useI18n()
  const [hovered, setHovered] = useState(false)
  const Icon = ROLE_ICONS[agent.role] || Bot
  const colorPreset = COLOR_PRESETS[index % COLOR_PRESETS.length]

  const statusColors: Record<AgentStatus, string> = {
    idle: "bg-emerald-500",
    working: "bg-blue-500",
    blocked: "bg-orange-500",
    error: "bg-red-500 animate-pulse",
  }

  const statusLabels: Record<AgentStatus, string> = {
    idle: t("status.idle"),
    working: t("status.working"),
    blocked: t("status.blocked"),
    error: t("status.error"),
  }

  return (
    <div
      className="group relative bg-card p-4 transition-colors hover:border-primary pixel-border cursor-pointer"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center bg-primary/15 text-primary border-2 border-primary/30">
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium text-card-foreground" style={{ fontFamily: "var(--font-heading, monospace)" }}>{agent.name}</h3>
            <div className={cn("h-2 w-2 rounded-full", statusColors[agent.status])} />
          </div>
          <p className="text-xs text-muted-foreground">{agent.role}</p>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
        <span className="font-mono text-[11px]">{agent.model}</span>
        <span className="flex items-center gap-2">
          <span>{agent.current_tasks} {t("agents.currentTasks")}</span>
          <span>{agent.completed_tasks} {t("agents.tasksDone")}</span>
        </span>
      </div>
      <PixelCharacter status={getPixelStatus(agent.status)} colorPreset={colorPreset} />
      {hovered && (
        <div className="absolute inset-x-0 bottom-0 flex justify-end gap-1 bg-gradient-to-t from-card p-2">
          <button
            className="p-1.5 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors border border-transparent hover:border-border"
            title={t("agents.settings")}
            onClick={(e) => { e.stopPropagation(); onClick() }}
          >
            <Settings className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  )
}

export function AgentsPage() {
  const { t } = useI18n()
  const [agents, setAgents] = useState<Agent[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const [agentsRes, rolesRes] = await Promise.all([
        api.agents.list(),
        api.roles.list(),
      ])
      setAgents(agentsRes.agents)
      setRoles(rolesRes.roles)
      setError(null)
    } catch (err) {
      console.error("Failed to fetch agents:", err)
      setError("Failed to load agents")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  function handleAgentCreated(agent: Agent) {
    setAgents((prev) => [...prev, agent])
  }

  function handleAgentUpdated(agent: Agent) {
    setAgents((prev) => prev.map((a) => (a.id === agent.id ? agent : a)))
    setSelectedAgent(agent)
  }

  function handleAgentDeleted(agentId: string) {
    setAgents((prev) => prev.filter((a) => a.id !== agentId))
    setSelectedAgent(null)
  }

  const running = agents.filter((a) => a.status === "working").length
  const errored = agents.filter((a) => a.status === "error").length
  const blocked = agents.filter((a) => a.status === "blocked").length

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-sm text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-lg font-semibold mb-1">{t("agents.title")}</h1>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{t("common.total")}: {agents.length}</span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-blue-500" />
              {t("agents.running")}: {running}
            </span>
            {blocked > 0 && (
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-orange-500" />
                {t("agents.blocked")}: {blocked}
              </span>
            )}
            {errored > 0 && (
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                {t("agents.error")}: {errored}
              </span>
            )}
          </div>
        </div>
        <CreateAgentDialog roles={roles} onCreated={handleAgentCreated} />
      </div>

      {error && (
        <div className="mb-4 p-3 border-2 border-destructive/50 bg-destructive/10 text-sm text-destructive pixel-border-sm">
          {error}
        </div>
      )}

      {agents.length === 0 && !error ? (
        <div className="flex items-center justify-center h-64 border-2 border-dashed border-border pixel-border">
          <p className="text-sm text-muted-foreground">{t("agents.noAgents")}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent, index) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              index={index}
              onClick={() => setSelectedAgent(agent)}
            />
          ))}
        </div>
      )}

      {selectedAgent && (
        <AgentDetailPanel
          agent={selectedAgent}
          roles={roles}
          onClose={() => setSelectedAgent(null)}
          onUpdated={handleAgentUpdated}
          onDeleted={handleAgentDeleted}
        />
      )}
    </div>
  )
}
