import { Play, Square, Search, Filter, Terminal, ChevronDown, ChevronUp, Wifi, WifiOff, X } from "lucide-react"
import { useState, useEffect, useRef, useCallback } from "react"
import { cn } from "@/lib/utils"
import { api, type Run, type RunStatus, type Agent, type Task } from "@/lib/api"
import { useWebSocket, type WSMessage } from "@/hooks/useWebSocket"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

// ─── Mock Data (fallback when API unavailable) ────────────────────────────────

const MOCK_AGENTS: Agent[] = [
  { id: "a1", name: "Backend Dev #1", role: "backend", model: "claude-sonnet-4-6", status: "active" },
  { id: "a2", name: "Frontend Dev", role: "frontend", model: "claude-sonnet-4-6", status: "active" },
  { id: "a3", name: "Tester #1", role: "testing", model: "claude-haiku-4-5", status: "idle" },
  { id: "a4", name: "Project Manager", role: "management", model: "claude-sonnet-4-6", status: "active" },
]

const MOCK_TASKS: Task[] = [
  { id: "t1", title: "Implement auth API", description: "", status: "in_progress", priority: "high", assignee_id: null, parent_id: null, position: 0, created_at: "", updated_at: "" },
  { id: "t2", title: "Build dashboard UI", description: "", status: "todo", priority: "medium", assignee_id: null, parent_id: null, position: 0, created_at: "", updated_at: "" },
  { id: "t3", title: "Write unit tests", description: "", status: "todo", priority: "medium", assignee_id: null, parent_id: null, position: 0, created_at: "", updated_at: "" },
]

let mockRunId = 100
function makeMockRun(agentId: string, agentName: string): Run {
  const id = `run-${++mockRunId}`
  return {
    id,
    agent_id: agentId,
    agent_name: agentName,
    task_id: null,
    task_title: null,
    command: null,
    status: "running",
    started_at: new Date().toISOString(),
    finished_at: null,
    duration_ms: null,
  }
}

// ─── Mock log messages for simulation ──────────────────────────────────────────

const MOCK_LOG_MESSAGES = [
  "Processing task queue item #42",
  "Fetching repository metadata",
  "Analyzing code structure in src/",
  "Running linter checks...",
  "Compiling TypeScript definitions",
  "Executing test suite: auth.test.ts",
  "HTTP request completed in 234ms",
  "Cache hit for key: agent-config-a1",
  "Dispatching webhook notification",
  "Checkpoint saved at step 15/20",
  "Memory usage: 256MB / 1024MB",
  "Rate limit status: 45% of quota",
  "Syncing workspace state...",
  "Generated 3 file patches",
  "Review completed, no issues found",
]

const MOCK_LOG_LEVELS: Array<"info" | "warn" | "error"> = ["info", "info", "info", "info", "warn", "error"]

// ─── Status helpers ────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<RunStatus, { label: string; color: string; bgColor: string; dotColor: string }> = {
  running: { label: "Running", color: "text-blue-400", bgColor: "bg-blue-500/15 border-blue-500/30", dotColor: "bg-blue-500 animate-pulse" },
  succeeded: { label: "Succeeded", color: "text-emerald-400", bgColor: "bg-emerald-500/15 border-emerald-500/30", dotColor: "bg-emerald-500" },
  failed: { label: "Failed", color: "text-red-400", bgColor: "bg-red-500/15 border-red-500/30", dotColor: "bg-red-500" },
  stopped: { label: "Stopped", color: "text-zinc-400", bgColor: "bg-zinc-500/15 border-zinc-500/30", dotColor: "bg-zinc-500" },
}

const LOG_LEVEL_COLORS: Record<string, string> = {
  info: "text-emerald-400",
  warn: "text-yellow-400",
  error: "text-red-400",
}

function formatDuration(ms: number | null): string {
  if (ms === null) return "--"
  const s = Math.floor(ms / 1000)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  const rem = s % 60
  if (m < 60) return `${m}m ${rem}s`
  const h = Math.floor(m / 60)
  return `${h}h ${m % 60}m`
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}:${d.getSeconds().toString().padStart(2, "0")}`
}

// ─── Log Entry Type ────────────────────────────────────────────────────────────

interface LogEntry {
  id: number
  run_id: string
  timestamp: string
  level: "info" | "warn" | "error"
  message: string
}

// ─── Main Component ────────────────────────────────────────────────────────────

export function RuntimePage() {
  // State
  const [runs, setRuns] = useState<Run[]>([])
  const [agents, setAgents] = useState<Agent[]>(MOCK_AGENTS)
  const [tasks, setTasks] = useState<Task[]>(MOCK_TASKS)
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [logIdCounter, setLogIdCounter] = useState(1)
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [agentFilter, setAgentFilter] = useState<string>("all")
  const [useMockData, setUseMockData] = useState(true)

  // Start run form state
  const [startAgentId, setStartAgentId] = useState("")
  const [startTaskId, setStartTaskId] = useState("")
  const [startCommand, setStartCommand] = useState("")
  const [showStartForm, setShowStartForm] = useState(false)

  // Refs
  const logEndRef = useRef<HTMLDivElement>(null)
  const logContainerRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)

  // ── Load initial data ──────────────────────────────────────────────────────

  const loadRuns = useCallback(async () => {
    try {
      const res = await api.runs.list()
      setRuns(res.runs)
      setUseMockData(false)
    } catch {
      // API not available, use mock data
    }
  }, [])

  const loadAgents = useCallback(async () => {
    try {
      const res = await api.agents.list()
      setAgents(res.agents)
    } catch {
      // keep mock agents
    }
  }, [])

  const loadTasks = useCallback(async () => {
    try {
      const projects = await api.projects.list()
      if (projects.projects.length > 0) {
        const res = await api.tasks.list(projects.projects[0].id)
        setTasks(res.tasks)
      }
    } catch {
      // keep mock tasks
    }
  }, [])

  useEffect(() => {
    loadRuns()
    loadAgents()
    loadTasks()
  }, [loadRuns, loadAgents, loadTasks])

  // ── Mock data simulation ───────────────────────────────────────────────────

  useEffect(() => {
    if (!useMockData) return

    // Initialize with some mock runs
    const now = new Date()
    const initialRuns: Run[] = [
      {
        id: "run-1", agent_id: "a1", agent_name: "Backend Dev #1",
        task_id: "t1", task_title: "Implement auth API", command: null,
        status: "running", started_at: new Date(now.getTime() - 180000).toISOString(),
        finished_at: null, duration_ms: null,
      },
      {
        id: "run-2", agent_id: "a2", agent_name: "Frontend Dev",
        task_id: "t2", task_title: "Build dashboard UI", command: null,
        status: "succeeded", started_at: new Date(now.getTime() - 600000).toISOString(),
        finished_at: new Date(now.getTime() - 120000).toISOString(), duration_ms: 480000,
      },
      {
        id: "run-3", agent_id: "a3", agent_name: "Tester #1",
        task_id: null, task_title: null, command: "npm test",
        status: "failed", started_at: new Date(now.getTime() - 900000).toISOString(),
        finished_at: new Date(now.getTime() - 600000).toISOString(), duration_ms: 300000,
      },
      {
        id: "run-4", agent_id: "a4", agent_name: "Project Manager",
        task_id: null, task_title: null, command: null,
        status: "stopped", started_at: new Date(now.getTime() - 1200000).toISOString(),
        finished_at: new Date(now.getTime() - 900000).toISOString(), duration_ms: 300000,
      },
    ]
    setRuns(initialRuns)
    setSelectedRunId("run-1")

    // Initialize mock logs for the running run
    const initialLogs: LogEntry[] = [
      { id: 1, run_id: "run-1", timestamp: new Date(now.getTime() - 180000).toISOString(), level: "info", message: "Runtime initialized successfully" },
      { id: 2, run_id: "run-1", timestamp: new Date(now.getTime() - 170000).toISOString(), level: "info", message: "Loading agent configuration from workspace" },
      { id: 3, run_id: "run-1", timestamp: new Date(now.getTime() - 160000).toISOString(), level: "info", message: "Connected to model provider: Anthropic" },
      { id: 4, run_id: "run-1", timestamp: new Date(now.getTime() - 150000).toISOString(), level: "info", message: "Agent 'Backend Dev #1' started with model claude-sonnet-4-6" },
      { id: 5, run_id: "run-1", timestamp: new Date(now.getTime() - 140000).toISOString(), level: "info", message: "Task 'Implement auth API' assigned" },
      { id: 6, run_id: "run-1", timestamp: new Date(now.getTime() - 120000).toISOString(), level: "info", message: "Analyzing codebase structure..." },
      { id: 7, run_id: "run-1", timestamp: new Date(now.getTime() - 100000).toISOString(), level: "warn", message: "Response time exceeding threshold (>5s)" },
      { id: 8, run_id: "run-1", timestamp: new Date(now.getTime() - 80000).toISOString(), level: "info", message: "Generated auth middleware implementation" },
      { id: 9, run_id: "run-1", timestamp: new Date(now.getTime() - 60000).toISOString(), level: "info", message: "Running unit tests for auth module..." },
      { id: 10, run_id: "run-1", timestamp: new Date(now.getTime() - 40000).toISOString(), level: "info", message: "Tests passed: 12/12" },
    ]
    setLogs(initialLogs)
    setLogIdCounter(11)
  }, [useMockData])

  // ── Mock live log simulation ───────────────────────────────────────────────

  useEffect(() => {
    if (!useMockData) return
    const running = runs.find((r) => r.status === "running")
    if (!running) return

    const interval = setInterval(() => {
      const now = new Date()
      const level = MOCK_LOG_LEVELS[Math.floor(Math.random() * MOCK_LOG_LEVELS.length)]
      const message = MOCK_LOG_MESSAGES[Math.floor(Math.random() * MOCK_LOG_MESSAGES.length)]

      setLogs((prev) => [
        ...prev,
        {
          id: logIdCounter,
          run_id: running.id,
          timestamp: now.toISOString(),
          level,
          message,
        },
      ])
      setLogIdCounter((c) => c + 1)

      // Update duration on the running run
      setRuns((prev) =>
        prev.map((r) =>
          r.id === running.id
            ? { ...r, duration_ms: now.getTime() - new Date(r.started_at).getTime() }
            : r,
        ),
      )
    }, 2000)

    return () => clearInterval(interval)
  }, [useMockData, runs, logIdCounter])

  // ── WebSocket handler ──────────────────────────────────────────────────────

  const handleWSMessage = useCallback((msg: WSMessage) => {
    if ("type" in msg && (msg.type === "run_started" || msg.type === "run_finished")) {
      // Run state change event
      if (msg.type === "run_started") {
        setRuns((prev) => [
          {
            id: msg.run_id,
            agent_id: msg.agent_id,
            agent_name: msg.agent_name,
            task_id: msg.task_id ?? null,
            task_title: msg.task_title ?? null,
            command: null,
            status: "running",
            started_at: msg.timestamp,
            finished_at: null,
            duration_ms: null,
          },
          ...prev,
        ])
      } else {
        setRuns((prev) =>
          prev.map((r) =>
            r.id === msg.run_id
              ? {
                  ...r,
                  status: (msg.status as RunStatus) ?? "succeeded",
                  finished_at: msg.timestamp,
                  duration_ms: new Date(msg.timestamp).getTime() - new Date(r.started_at).getTime(),
                }
              : r,
          ),
        )
      }
    } else if ("run_id" in msg && "message" in msg) {
      // Log entry
      setUseMockData(false)
      setLogs((prev) => [
        ...prev,
        {
          id: prev.length + 1,
          run_id: msg.run_id,
          timestamp: msg.timestamp,
          level: msg.level,
          message: msg.message,
        },
      ])
    }
  }, [])

  const { connected: wsConnected } = useWebSocket(handleWSMessage)

  // ── Auto-scroll ────────────────────────────────────────────────────────────

  useEffect(() => {
    if (autoScroll) {
      logEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [logs, autoScroll])

  const handleLogScroll = () => {
    const el = logContainerRef.current
    if (!el) return
    const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50
    setAutoScroll(isAtBottom)
  }

  // ── Start / Stop handlers ──────────────────────────────────────────────────

  const handleStartRun = async () => {
    if (!startAgentId) return

    const agent = agents.find((a) => a.id === startAgentId)
    if (!agent) return

    if (!useMockData) {
      try {
        const run = await api.runs.create({
          agent_id: startAgentId,
          task_id: startTaskId || undefined,
          command: startCommand || undefined,
        })
        setRuns((prev) => [run, ...prev])
        setSelectedRunId(run.id)
      } catch {
        // fallback to mock
      }
    } else {
      const run = makeMockRun(startAgentId, agent.name)
      if (startTaskId) {
        const task = tasks.find((t) => t.id === startTaskId)
        run.task_id = startTaskId
        run.task_title = task?.title ?? null
      }
      if (startCommand) run.command = startCommand
      setRuns((prev) => [run, ...prev])
      setSelectedRunId(run.id)

      // Add initial log
      setLogs((prev) => [
        ...prev,
        {
          id: logIdCounter,
          run_id: run.id,
          timestamp: new Date().toISOString(),
          level: "info",
          message: `Run started for agent '${agent.name}'${run.task_title ? ` on task '${run.task_title}'` : ""}${run.command ? ` with command '${run.command}'` : ""}`,
        },
      ])
      setLogIdCounter((c) => c + 1)
    }

    setShowStartForm(false)
    setStartAgentId("")
    setStartTaskId("")
    setStartCommand("")
  }

  const handleStopRun = async (runId: string) => {
    if (!useMockData) {
      try {
        await api.runs.stop(runId)
      } catch {
        // fallback
      }
    }

    setRuns((prev) =>
      prev.map((r) =>
        r.id === runId
          ? {
              ...r,
              status: "stopped" as RunStatus,
              finished_at: new Date().toISOString(),
              duration_ms: r.started_at ? Date.now() - new Date(r.started_at).getTime() : null,
            }
          : r,
      ),
    )

    setLogs((prev) => [
      ...prev,
      {
        id: logIdCounter,
        run_id: runId,
        timestamp: new Date().toISOString(),
        level: "warn",
        message: "Run stopped by user",
      },
    ])
    setLogIdCounter((c) => c + 1)
  }

  // ── Filtered data ──────────────────────────────────────────────────────────

  const filteredRuns = runs.filter((r) => {
    if (statusFilter !== "all" && r.status !== statusFilter) return false
    if (agentFilter !== "all" && r.agent_id !== agentFilter) return false
    return true
  })

  const selectedRun = runs.find((r) => r.id === selectedRunId)

  const filteredLogs = logs
    .filter((l) => !selectedRunId || l.run_id === selectedRunId)
    .filter((l) => !searchQuery || l.message.toLowerCase().includes(searchQuery.toLowerCase()))

  // ── Running count ──────────────────────────────────────────────────────────

  const runningCount = runs.filter((r) => r.status === "running").length

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold">Runtime Console</h1>
          <div className={cn(
            "flex items-center gap-1.5 px-2 py-1 text-xs font-medium border",
            runningCount > 0
              ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
              : "bg-zinc-500/15 text-zinc-400 border-zinc-500/30"
          )}>
            <span className={cn("h-2 w-2", runningCount > 0 ? "bg-emerald-500 animate-pulse" : "bg-zinc-500")} />
            {runningCount > 0 ? `${runningCount} running` : "Idle"}
          </div>
          <div className={cn(
            "flex items-center gap-1 px-2 py-1 text-xs border",
            wsConnected ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" : "text-zinc-500 border-zinc-500/30 bg-zinc-500/10"
          )}>
            {wsConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            {wsConnected ? "WS Connected" : "WS Disconnected"}
          </div>
        </div>
        <Button onClick={() => setShowStartForm(!showStartForm)} size="sm">
          <Play className="h-3 w-3" />
          New Run
        </Button>
      </div>

      {/* Start Run Form */}
      {showStartForm && (
        <div className="pixel-border bg-card p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold font-mono">Start New Run</h3>
            <button onClick={() => setShowStartForm(false)} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block font-mono">Agent *</label>
              <Select value={startAgentId} onValueChange={setStartAgentId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select agent..." />
                </SelectTrigger>
                <SelectContent>
                  {agents.map((a) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block font-mono">Task</label>
              <Select value={startTaskId} onValueChange={setStartTaskId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select task (optional)..." />
                </SelectTrigger>
                <SelectContent>
                  {tasks.map((t) => (
                    <SelectItem key={t.id} value={t.id}>
                      {t.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block font-mono">Command</label>
              <Input
                placeholder="Custom command (optional)"
                value={startCommand}
                onChange={(e) => setStartCommand(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button onClick={handleStartRun} disabled={!startAgentId} className="w-full">
                <Play className="h-3 w-3" />
                Start
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Main content: Run list + Log viewer */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* Left: Run List */}
        <div className="w-80 flex flex-col pixel-border bg-card shrink-0">
          <div className="p-3 border-b-2 border-border">
            <div className="flex items-center gap-2 mb-2">
              <Filter className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs font-mono text-muted-foreground">Filters</span>
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="running">Running</SelectItem>
                  <SelectItem value="succeeded">Succeeded</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="stopped">Stopped</SelectItem>
                </SelectContent>
              </Select>
              <Select value={agentFilter} onValueChange={setAgentFilter}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Agent" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Agents</SelectItem>
                  {agents.map((a) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex-1 overflow-auto">
            {filteredRuns.length === 0 ? (
              <div className="p-4 text-center text-xs text-muted-foreground">
                No runs found
              </div>
            ) : (
              filteredRuns.map((run) => {
                const cfg = STATUS_CONFIG[run.status]
                const isSelected = run.id === selectedRunId
                return (
                  <button
                    key={run.id}
                    onClick={() => setSelectedRunId(run.id)}
                    className={cn(
                      "w-full text-left p-3 border-b-2 border-border transition-colors",
                      isSelected ? "bg-accent" : "hover:bg-accent/50"
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold truncate">{run.agent_name}</span>
                      <span className={cn(
                        "flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium border",
                        cfg.bgColor, cfg.color
                      )}>
                        <span className={cn("h-1.5 w-1.5 rounded-full", cfg.dotColor)} />
                        {cfg.label}
                      </span>
                    </div>
                    {run.task_title && (
                      <div className="text-[11px] text-muted-foreground truncate mb-1">
                        Task: {run.task_title}
                      </div>
                    )}
                    {run.command && (
                      <div className="text-[11px] text-muted-foreground truncate mb-1 font-mono">
                        $ {run.command}
                      </div>
                    )}
                    <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                      <span>{formatTime(run.started_at)}</span>
                      <span>{formatDuration(run.duration_ms)}</span>
                    </div>
                    {run.status === "running" && (
                      <div className="mt-2">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleStopRun(run.id)
                          }}
                          className="h-6 text-[10px] px-2"
                        >
                          <Square className="h-2.5 w-2.5" />
                          Stop
                        </Button>
                      </div>
                    )}
                  </button>
                )
              })
            )}
          </div>
        </div>

        {/* Right: Log Viewer */}
        <div className="flex-1 flex flex-col pixel-border overflow-hidden">
          {/* Log header */}
          <div className="flex items-center justify-between p-2 border-b-2 border-border bg-card">
            <div className="flex items-center gap-2">
              <Terminal className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs font-mono text-muted-foreground">
                {selectedRun
                  ? `Logs: ${selectedRun.agent_name}${selectedRun.task_title ? ` / ${selectedRun.task_title}` : ""}`
                  : "Select a run to view logs"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                className={cn(
                  "text-[10px] font-mono px-2 py-0.5 border",
                  autoScroll ? "text-emerald-400 border-emerald-500/30" : "text-muted-foreground border-border"
                )}
              >
                {autoScroll ? (
                  <span className="flex items-center gap-1"><ChevronDown className="h-3 w-3" /> Auto</span>
                ) : (
                  <span className="flex items-center gap-1"><ChevronUp className="h-3 w-3" /> Manual</span>
                )}
              </button>
            </div>
          </div>

          {/* Terminal log area */}
          <div
            ref={logContainerRef}
            onScroll={handleLogScroll}
            className="flex-1 overflow-auto bg-zinc-950 p-3 font-mono text-xs leading-relaxed"
          >
            {filteredLogs.length === 0 ? (
              <div className="text-zinc-600 text-center mt-8">
                {selectedRun ? "No log entries yet" : "Select a run from the list to view logs"}
              </div>
            ) : (
              filteredLogs.map((log) => (
                <div key={log.id} className="flex gap-3 py-0.5">
                  <span className="text-amber-700/60 shrink-0 select-none">{formatTime(log.timestamp)}</span>
                  <span className={cn("shrink-0 uppercase w-12 text-right", LOG_LEVEL_COLORS[log.level])}>
                    [{log.level}]
                  </span>
                  <span className="text-amber-100/80 break-all">{log.message}</span>
                </div>
              ))
            )}
            <div ref={logEndRef} />
          </div>

          {/* Log search bar */}
          <div className="border-t-2 border-border bg-card p-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full border-2 border-input bg-background pl-8 pr-3 py-1.5 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
