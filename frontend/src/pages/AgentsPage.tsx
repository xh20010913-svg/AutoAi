import { Bot, Play, Square, Settings, Code, TestTube, Briefcase, User } from "lucide-react"
import { cn } from "@/lib/utils"
import { PixelOffice } from "@/components/PixelOffice"
import type { ColorPreset } from "@/components/PixelOffice"

interface Agent {
  id: string
  name: string
  role: string
  status: "idle" | "running" | "error"
  model: string
  completedTasks: number
  icon: typeof Bot
  colorPreset: ColorPreset
}

const mockAgents: Agent[] = [
  { id: "1", name: "Project Manager", role: "Project Manager", status: "running", model: "claude-sonnet-4-6", completedTasks: 23, icon: Briefcase, colorPreset: "blue" },
  { id: "2", name: "Backend Dev #1", role: "Backend Developer", status: "running", model: "claude-sonnet-4-6", completedTasks: 45, icon: Code, colorPreset: "green" },
  { id: "3", name: "Backend Dev #2", role: "Backend Developer", status: "idle", model: "claude-haiku-4-5", completedTasks: 31, icon: Code, colorPreset: "purple" },
  { id: "4", name: "Backend Dev #3", role: "Backend Developer", status: "error", model: "claude-sonnet-4-6", completedTasks: 28, icon: Code, colorPreset: "amber" },
  { id: "5", name: "Frontend Dev", role: "Frontend Developer", status: "running", model: "claude-sonnet-4-6", completedTasks: 19, icon: User, colorPreset: "pink" },
  { id: "6", name: "Tester #1", role: "QA Tester", status: "idle", model: "claude-haiku-4-5", completedTasks: 67, icon: TestTube, colorPreset: "cyan" },
  { id: "7", name: "Tester #2", role: "QA Tester", status: "running", model: "claude-haiku-4-5", completedTasks: 52, icon: TestTube, colorPreset: "red" },
  { id: "8", name: "Tester #3", role: "QA Tester", status: "idle", model: "claude-haiku-4-5", completedTasks: 38, icon: TestTube, colorPreset: "teal" },
]

function AgentDetailRow({ agent }: { agent: Agent }) {
  const Icon = agent.icon
  return (
    <div className="flex items-center gap-3 px-3 py-2 hover:bg-muted/50 transition-colors border-b border-border/50 last:border-b-0">
      <div className={cn(
        "h-2 w-2 rounded-full",
        agent.status === "running" ? "bg-emerald-500 animate-pulse" :
        agent.status === "error" ? "bg-red-500 animate-pulse" :
        "bg-zinc-500"
      )} />
      <div className="flex h-7 w-7 items-center justify-center bg-primary/15 text-primary border border-primary/30">
        <Icon className="h-3.5 w-3.5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate" style={{ fontFamily: "var(--font-heading, monospace)" }}>{agent.name}</div>
        <div className="text-xs text-muted-foreground">{agent.role}</div>
      </div>
      <span className="text-xs text-muted-foreground font-mono hidden sm:inline">{agent.model}</span>
      <span className="text-xs text-muted-foreground">{agent.completedTasks} done</span>
      <div className="flex gap-1">
        <button className="p-1 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors border border-transparent hover:border-border" title="Start">
          <Play className="h-3 w-3" />
        </button>
        <button className="p-1 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors border border-transparent hover:border-border" title="Stop">
          <Square className="h-3 w-3" />
        </button>
        <button className="p-1 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors border border-transparent hover:border-border" title="Settings">
          <Settings className="h-3 w-3" />
        </button>
      </div>
    </div>
  )
}

export function AgentsPage() {
  const running = mockAgents.filter((a) => a.status === "running").length
  const errored = mockAgents.filter((a) => a.status === "error").length
  const idle = mockAgents.filter((a) => a.status === "idle").length

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-semibold mb-1">Agents</h1>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>Total: {mockAgents.length}</span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 bg-emerald-500 animate-pulse" />
            Running: {running}
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 bg-zinc-500" />
            Idle: {idle}
          </span>
          {errored > 0 && (
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
              Error: {errored}
            </span>
          )}
        </div>
      </div>

      {/* Pixel Office Scene */}
      <PixelOffice agents={mockAgents} />

      {/* Agent Detail List */}
      <div className="mt-4 pixel-border bg-card">
        <div className="px-3 py-2 border-b border-border">
          <h2 className="text-sm font-semibold">Agent Details</h2>
        </div>
        {mockAgents.map((agent) => (
          <AgentDetailRow key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  )
}
