import { Bot, Play, Square, Settings, User, Code, TestTube, Briefcase } from "lucide-react"
import { cn } from "@/lib/utils"
import { useState } from "react"

interface Agent {
  id: string
  name: string
  role: string
  status: "idle" | "running"
  model: string
  completedTasks: number
  icon: typeof Bot
}

const mockAgents: Agent[] = [
  { id: "1", name: "Project Manager", role: "Project Manager", status: "running", model: "claude-sonnet-4-6", completedTasks: 23, icon: Briefcase },
  { id: "2", name: "Backend Dev #1", role: "Backend Developer", status: "running", model: "claude-sonnet-4-6", completedTasks: 45, icon: Code },
  { id: "3", name: "Backend Dev #2", role: "Backend Developer", status: "idle", model: "claude-haiku-4-5", completedTasks: 31, icon: Code },
  { id: "4", name: "Backend Dev #3", role: "Backend Developer", status: "idle", model: "claude-sonnet-4-6", completedTasks: 28, icon: Code },
  { id: "5", name: "Frontend Dev", role: "Frontend Developer", status: "running", model: "claude-sonnet-4-6", completedTasks: 19, icon: User },
  { id: "6", name: "Tester #1", role: "QA Tester", status: "idle", model: "claude-haiku-4-5", completedTasks: 67, icon: TestTube },
  { id: "7", name: "Tester #2", role: "QA Tester", status: "running", model: "claude-haiku-4-5", completedTasks: 52, icon: TestTube },
  { id: "8", name: "Tester #3", role: "QA Tester", status: "idle", model: "claude-haiku-4-5", completedTasks: 38, icon: TestTube },
]

function AgentCard({ agent }: { agent: Agent }) {
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
              "h-2 w-2",
              agent.status === "running" ? "bg-emerald-500 animate-pulse" : "bg-zinc-500"
            )} />
          </div>
          <p className="text-xs text-muted-foreground">{agent.role}</p>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
        <span className="font-mono text-[11px]">{agent.model}</span>
        <span>{agent.completedTasks} tasks done</span>
      </div>
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
  const running = mockAgents.filter((a) => a.status === "running").length

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-lg font-semibold mb-1">Agents</h1>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>Total: {mockAgents.length}</span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 bg-emerald-500 animate-pulse" />
            Running: {running}
          </span>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockAgents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  )
}
