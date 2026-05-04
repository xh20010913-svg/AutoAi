import { useState, useEffect, useCallback } from "react"
import { ListTodo, Timer, CheckCircle2, Bot, Clock, AlertTriangle, Wrench, Coffee } from "lucide-react"
import { Link } from "react-router-dom"
import { cn } from "@/lib/utils"
import { api, type Task, type AgentStatusSummary, type Activity } from "@/lib/api"

interface TaskStats {
  total: number
  todo: number
  inProgress: number
  inReview: number
  done: number
  blocked: number
}

interface StatCard {
  label: string
  value: number
  icon: React.ComponentType<{ className?: string }>
  color: string
  accent: string
  href: string
}

function buildTaskStats(tasks: Task[]): TaskStats {
  return {
    total: tasks.length,
    todo: tasks.filter((t) => t.status === "todo").length,
    inProgress: tasks.filter((t) => t.status === "in_progress").length,
    inReview: tasks.filter((t) => t.status === "in_review").length,
    done: tasks.filter((t) => t.status === "done").length,
    blocked: tasks.filter((t) => t.status === "blocked").length,
  }
}

function TaskBarChart({ stats }: { stats: TaskStats }) {
  const bars = [
    { label: "Todo", value: stats.todo, color: "bg-zinc-400" },
    { label: "In Progress", value: stats.inProgress, color: "bg-amber-500" },
    { label: "In Review", value: stats.inReview, color: "bg-orange-500" },
    { label: "Done", value: stats.done, color: "bg-emerald-500" },
    { label: "Blocked", value: stats.blocked, color: "bg-red-500" },
  ]

  const max = Math.max(...bars.map((b) => b.value), 1)

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-foreground font-mono">Task Status Distribution</h3>
      <div className="space-y-2.5">
        {bars.map((bar) => (
          <div key={bar.label} className="flex items-center gap-3">
            <span className="w-20 text-xs text-muted-foreground font-mono tracking-tight flex-shrink-0">
              {bar.label}
            </span>
            <div className="flex-1 h-5 bg-muted relative">
              <div
                className={cn("h-full transition-all duration-500", bar.color)}
                style={{ width: `${Math.max((bar.value / max) * 100, bar.value > 0 ? 4 : 0)}%` }}
              />
            </div>
            <span className="w-8 text-right text-xs text-foreground font-mono font-medium tabular-nums">
              {bar.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function AgentStatusPanel({ summary }: { summary: AgentStatusSummary }) {
  const items = [
    { label: "Working", value: summary.working, icon: Wrench, color: "text-amber-400", bg: "bg-amber-500/15", border: "border-amber-500/30" },
    { label: "Idle", value: summary.idle, icon: Coffee, color: "text-emerald-400", bg: "bg-emerald-500/15", border: "border-emerald-500/30" },
    { label: "Blocked", value: summary.blocked, icon: AlertTriangle, color: "text-red-400", bg: "bg-red-500/15", border: "border-red-500/30" },
  ]

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-foreground font-mono">Agent Status</h3>
        <Link
          to="/agents"
          className="text-[10px] text-muted-foreground hover:text-primary font-mono uppercase tracking-wider"
        >
          View all →
        </Link>
      </div>
      <div className="space-y-2">
        {items.map(({ label, value, icon: Icon, color, bg, border }) => (
          <div
            key={label}
            className={cn("flex items-center gap-3 p-2.5 border", bg, border)}
          >
            <Icon className={cn("h-4 w-4", color)} />
            <span className="text-xs text-foreground flex-1">{label}</span>
            <span className="text-sm font-mono font-medium text-foreground tabular-nums">{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ActivityList({ activities }: { activities: Activity[] }) {
  const typeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    task_created: ListTodo,
    task_completed: CheckCircle2,
    agent_started: Bot,
    agent_idle: Coffee,
    agent_blocked: AlertTriangle,
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-foreground font-mono">Recent Activity</h3>
      {activities.length === 0 ? (
        <p className="text-xs text-muted-foreground font-mono">No recent activity.</p>
      ) : (
        <div className="space-y-0">
          {activities.map((a, i) => {
            const Icon = typeIcons[a.type] ?? Clock
            return (
              <div
                key={a.id}
                className={cn(
                  "flex items-start gap-3 py-2.5 px-3 border-l-2 border-transparent hover:bg-muted/50 transition-colors",
                  i === 0 && "border-l-primary",
                )}
              >
                <Icon className="h-3.5 w-3.5 text-muted-foreground mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-foreground">{a.message}</p>
                  <p className="text-[10px] text-muted-foreground font-mono mt-0.5">
                    {new Date(a.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export function DashboardPage() {
  const [taskStats, setTaskStats] = useState<TaskStats>({
    total: 0, todo: 0, inProgress: 0, inReview: 0, done: 0, blocked: 0,
  })
  const [agentSummary, setAgentSummary] = useState<AgentStatusSummary>({
    idle: 0, working: 0, blocked: 0, offline: 0, total: 0,
  })
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)

    let tasks: Task[] = []
    let agents: AgentStatusSummary | null = null

    // Load tasks
    try {
      const { projects } = await api.projects.list()
      if (projects.length > 0) {
        const { tasks: taskData } = await api.tasks.list(projects[0].id)
        tasks = taskData
      }
    } catch {
      // API unavailable — use mock data
      const mockTasks = Array.from({ length: 42 }, (_, i) => ({
        id: `mock-task-${i}`,
        title: `Task ${i + 1}`,
        description: "",
        status: ["todo", "todo", "todo", "todo", "todo", "todo", "todo", "todo", "in_progress", "in_progress", "in_progress", "in_progress", "in_progress", "in_progress", "in_progress", "in_progress", "in_progress", "in_progress", "in_progress", "in_progress", "in_review", "in_review", "in_review", "in_review", "in_review", "in_review", "in_review", "in_review", "done", "done", "done", "done", "done", "done", "done", "done", "done", "done", "done", "done", "blocked", "blocked"][i] as Task["status"],
        priority: "medium" as const,
        assignee_id: null,
        parent_id: null,
        position: i,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }))
      tasks = mockTasks
    }

    // Load agent status
    try {
      const { summary } = await api.agents.statusAll()
      agents = summary
    } catch {
      agents = { idle: 3, working: 2, blocked: 1, offline: 0, total: 6 }
    }

    // Load activity (use mock — API under development per AUT-228)
    const mockActivities: Activity[] = [
      { id: "act-1", type: "task_completed", message: "Task \"Implement login page\" moved to Done", task_id: "t1", created_at: new Date(Date.now() - 2 * 60 * 1000).toISOString() },
      { id: "act-2", type: "agent_started", message: "Agent \"backend-builder\" started working", agent_id: "a1", created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString() },
      { id: "act-3", type: "task_created", message: "Task \"Fix memory leak in runtime\" created", task_id: "t2", created_at: new Date(Date.now() - 12 * 60 * 1000).toISOString() },
      { id: "act-4", type: "agent_idle", message: "Agent \"code-reviewer\" finished work, now idle", agent_id: "a2", created_at: new Date(Date.now() - 25 * 60 * 1000).toISOString() },
      { id: "act-5", type: "agent_blocked", message: "Agent \"data-migrator\" blocked: missing DB credentials", agent_id: "a3", created_at: new Date(Date.now() - 40 * 60 * 1000).toISOString() },
      { id: "act-6", type: "task_completed", message: "Task \"Set up CI/CD pipeline\" moved to Done", task_id: "t3", created_at: new Date(Date.now() - 60 * 60 * 1000).toISOString() },
      { id: "act-7", type: "agent_started", message: "Agent \"frontend-dev\" started working", agent_id: "a4", created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() },
      { id: "act-8", type: "task_created", message: "Task \"Add rate limiting to API\" created", task_id: "t4", created_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString() },
    ]

    setTaskStats(buildTaskStats(tasks))
    setAgentSummary(agents)
    setActivities(mockActivities)
    setLoading(false)
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground font-mono">Loading dashboard...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-destructive">{error}</p>
      </div>
    )
  }

  const statCards: StatCard[] = [
    { label: "Total Tasks", value: taskStats.total, icon: ListTodo, color: "text-blue-400", accent: "border-l-primary", href: "/board" },
    { label: "In Progress", value: taskStats.inProgress, icon: Timer, color: "text-amber-400", accent: "border-l-amber-500", href: "/board" },
    { label: "Done", value: taskStats.done, icon: CheckCircle2, color: "text-emerald-400", accent: "border-l-emerald-500", href: "/board" },
    { label: "Active Agents", value: agentSummary.working, icon: Bot, color: "text-purple-400", accent: "border-l-purple-500", href: "/agents" },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold font-mono">Dashboard</h1>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(({ label, value, icon: Icon, color, accent, href }) => (
          <Link
            key={label}
            to={href}
            className={cn("bg-card p-4 pixel-border-sm transition-colors hover:border-primary", accent, "border-l-[3px]")}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-mono tracking-tight">{label}</p>
                <p className="text-2xl font-bold font-mono mt-1 tabular-nums">{value}</p>
              </div>
              <Icon className={cn("h-6 w-6 opacity-40", color)} />
            </div>
          </Link>
        ))}
      </div>

      {/* Charts and agent status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card p-5 pixel-border-sm">
          <TaskBarChart stats={taskStats} />
        </div>
        <div className="bg-card p-5 pixel-border-sm">
          <AgentStatusPanel summary={agentSummary} />
        </div>
      </div>

      {/* Recent activity */}
      <div className="bg-card p-5 pixel-border-sm">
        <ActivityList activities={activities} />
      </div>
    </div>
  )
}
