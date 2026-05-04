import { Bot, User, Code, TestTube, Briefcase } from "lucide-react"
import { AgentCard, type Agent } from "@/components/AgentCard"

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

export function AgentsPage() {
  const running = mockAgents.filter((a) => a.status === "running").length
  const errored = mockAgents.filter((a) => a.status === "error").length

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-lg font-semibold">Agents</h1>
          <span className="text-[10px] font-mono text-muted-foreground/40 tracking-wider uppercase">// agent roster</span>
        </div>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span className="font-mono text-xs">Total: {mockAgents.length}</span>
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockAgents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  )
}
