import { Play, Square, Search } from "lucide-react"
import { useState, useEffect, useRef, useCallback } from "react"
import { cn } from "@/lib/utils"
import { connectWebSocket } from "@/lib/ws"

interface LogEntry {
  id: number
  time: string
  level: "info" | "warn" | "error"
  message: string
}

let nextLogId = 100

function timeNow() {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}:${now.getSeconds().toString().padStart(2, "0")}`
}

const levelColors: Record<string, string> = {
  info: "text-amber-300",
  warn: "text-yellow-400",
  error: "text-red-400",
}

export function RuntimePage() {
  const [running, setRunning] = useState(true)
  const [logs, setLogs] = useState<LogEntry[]>([
    { id: 1, time: timeNow(), level: "info", message: "Runtime initialized successfully" },
  ])
  const [searchQuery, setSearchQuery] = useState("")
  const logEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [logs])

  // WebSocket: real-time runtime updates
  useEffect(() => {
    const unsubscribe = connectWebSocket((data) => {
      if (data.event === "runtime_update") {
        const payload = data.data ?? {}
        const level: LogEntry["level"] = ["info", "warn", "error"].includes(payload.level)
          ? payload.level
          : "info"
        setLogs((prev) => [
          ...prev,
          { id: ++nextLogId, time: timeNow(), level, message: payload.message ?? "Unknown event" },
        ])
      }
    })
    return unsubscribe
  }, [])

  // Simulated heartbeat logs (keep as demo when no real backend activity)
  useEffect(() => {
    if (!running) return
    const interval = setInterval(() => {
      const messages = [
        "Heartbeat received from all active agents",
        "Task queue depth: 12 pending, 4 processing",
        "Memory usage: 342MB / 1024MB",
        "API latency: 245ms avg",
        "Checkpoint saved for Agent 'Backend Dev #1'",
        "New issue comment detected on AUT-143",
        "Agent 'Project Manager' dispatched subtask",
      ]
      const levels: Array<"info" | "warn" | "error"> = ["info", "info", "info", "info", "warn", "error"]
      setLogs((prev) => [
        ...prev,
        {
          id: ++nextLogId,
          time: timeNow(),
          level: levels[Math.floor(Math.random() * levels.length)],
          message: messages[Math.floor(Math.random() * messages.length)],
        },
      ])
    }, 5000)
    return () => clearInterval(interval)
  }, [running])

  const filteredLogs = searchQuery
    ? logs.filter((l) => l.message.toLowerCase().includes(searchQuery.toLowerCase()))
    : logs

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold">Runtime</h1>
          <span className="text-[10px] font-mono text-muted-foreground/40 tracking-wider uppercase">// live console</span>
        </div>
        <div className="flex items-center gap-2">
          <div className={cn(
            "flex items-center gap-1.5 px-2 py-1 text-xs font-medium border",
            running ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" : "bg-zinc-500/15 text-zinc-400 border-zinc-500/30"
          )}>
            <span className={cn("h-2 w-2", running ? "bg-emerald-500 animate-pulse" : "bg-zinc-500")} />
            {running ? "Running" : "Stopped"}
          </div>
          <button
            onClick={() => setRunning(!running)}
            className={cn(
              "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-opacity hover:opacity-90 pixel-border-sm",
              running
                ? "bg-destructive text-destructive-foreground border-destructive"
                : "bg-primary text-primary-foreground border-primary"
            )}
          >
            {running ? <Square className="h-3 w-3" /> : <Play className="h-3 w-3" />}
            {running ? "Stop" : "Run"}
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-hidden flex flex-col pixel-border">
        <div className="flex-1 overflow-auto p-3 font-mono text-xs leading-relaxed relative" style={{ backgroundColor: "oklch(0.12 0.015 40)" }}>
          <div className="absolute inset-0 pointer-events-none opacity-[0.03]" style={{
            background: "repeating-linear-gradient(0deg, transparent, transparent 1px, rgba(255,255,255,0.08) 1px, rgba(255,255,255,0.08) 2px)"
          }} />
          {filteredLogs.map((log) => (
            <div key={log.id} className="flex gap-3 relative z-10">
              <span className="shrink-0" style={{ color: "oklch(0.55 0.08 55 / 0.6)" }}>{log.time}</span>
              <span className={cn("shrink-0 uppercase w-12", levelColors[log.level])}>
                [{log.level}]
              </span>
              <span style={{ color: "oklch(0.90 0.03 75 / 0.8)" }}>{log.message}</span>
            </div>
          ))}
          <div ref={logEndRef} />
        </div>
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
  )
}
