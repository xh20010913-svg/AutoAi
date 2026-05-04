import { Plus, MoreHorizontal } from "lucide-react"
import { cn } from "@/lib/utils"

interface Task {
  id: string
  title: string
  description: string
  priority: "low" | "medium" | "high"
  assignee: string
}

interface Column {
  title: string
  color: string
  tasks: Task[]
}

const mockColumns: Column[] = [
  {
    title: "Todo",
    color: "bg-zinc-400",
    tasks: [
      { id: "1", title: "Setup project structure", description: "Initialize the project with proper directory layout and tooling", priority: "high", assignee: "Alice" },
      { id: "2", title: "Design database schema", description: "Create ERD and define table relationships", priority: "medium", assignee: "Bob" },
      { id: "3", title: "Write unit tests", description: "Cover core business logic with unit tests", priority: "low", assignee: "Carol" },
    ],
  },
  {
    title: "In Progress",
    color: "bg-blue-500",
    tasks: [
      { id: "4", title: "Implement auth API", description: "JWT-based authentication with refresh tokens", priority: "high", assignee: "Dave" },
      { id: "5", title: "Build dashboard UI", description: "Create responsive dashboard with charts", priority: "medium", assignee: "Alice" },
    ],
  },
  {
    title: "In Review",
    color: "bg-amber-500",
    tasks: [
      { id: "6", title: "Code review: payments", description: "Review the Stripe payment integration PR", priority: "high", assignee: "Eve" },
      { id: "7", title: "API documentation", description: "Document REST endpoints with OpenAPI spec", priority: "medium", assignee: "Bob" },
    ],
  },
  {
    title: "Done",
    color: "bg-emerald-500",
    tasks: [
      { id: "8", title: "Setup CI/CD pipeline", description: "GitHub Actions for lint, test, deploy", priority: "medium", assignee: "Carol" },
      { id: "9", title: "Configure linting", description: "ESLint + Prettier configuration", priority: "low", assignee: "Dave" },
      { id: "10", title: "Initial wireframes", description: "Low-fidelity wireframes for all pages", priority: "low", assignee: "Eve" },
    ],
  },
  {
    title: "Blocked",
    color: "bg-red-500",
    tasks: [
      { id: "11", title: "External API integration", description: "Waiting on third-party API credentials", priority: "high", assignee: "Alice" },
    ],
  },
]

const priorityColors: Record<string, string> = {
  high: "bg-red-500/15 text-red-400 border-red-500/20",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/20",
  low: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
}

function TaskCard({ task }: { task: Task }) {
  return (
    <div className="group rounded-lg border border-border bg-card p-3 transition-colors hover:border-primary/40">
      <div className="flex items-start justify-between">
        <h4 className="text-sm font-medium text-card-foreground">{task.title}</h4>
        <button className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground">
          <MoreHorizontal className="h-4 w-4" />
        </button>
      </div>
      <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{task.description}</p>
      <div className="mt-3 flex items-center justify-between">
        <span className={cn("rounded-md border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider", priorityColors[task.priority])}>
          {task.priority}
        </span>
        <span className="text-xs text-muted-foreground">{task.assignee}</span>
      </div>
    </div>
  )
}

export function BoardPage() {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold">Board</h1>
        <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:opacity-90 transition-opacity">
          <Plus className="h-3.5 w-3.5" />
          New Task
        </button>
      </div>
      <div className="flex-1 overflow-x-auto">
        <div className="flex gap-4 pb-4" style={{ minWidth: "max-content" }}>
          {mockColumns.map((col) => (
            <div key={col.title} className="flex w-72 flex-col rounded-lg border border-border bg-muted/30">
              <div className="flex items-center gap-2 p-3 border-b border-border">
                <div className={cn("h-2.5 w-2.5 rounded-full", col.color)} />
                <h3 className="text-sm font-medium">{col.title}</h3>
                <span className="ml-auto rounded-md bg-muted px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground">
                  {col.tasks.length}
                </span>
              </div>
              <div className="flex flex-col gap-2 p-2 flex-1 min-h-0">
                {col.tasks.map((task) => (
                  <TaskCard key={task.id} task={task} />
                ))}
              </div>
              <div className="p-2 border-t border-border">
                <button className="flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors">
                  <Plus className="h-3 w-3" />
                  New Task
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
