import { Play, Square, Search } from "lucide-react"
import { useState, useEffect, useRef } from "react"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/hooks/useLanguage"

interface LogEntry { id: number; time: string; level: "info" | "warn" | "error"; message: string }

const mockLogs: LogEntry[] = [
  { id: 1, time: "10:23:01", level: "info", message: "Runtime initialized successfully" },
  { id: 2, time: "10:23:02", level: "info", message: "Loading agent configuration from workspace" },
  { id: 3, time: "10:23:03", level: "info", message: "Connected to model provider: Anthropic" },
  { id: 4, time: "10:23:04", level: "info", message: "Agent 'Backend Dev #1' started with model claude-sonnet-4-6" },
  { id: 5, time: "10:23:05", level: "info", message: "Agent 'Frontend Dev' started with model claude-sonnet-4-6" },
  { id: 6, time: "10:23:06", level: "warn", message: "Agent 'Tester #2' response time exceeding threshold (>5s)" },
  { id: 7, time: "10:23:07", level: "info", message: "Task 'Implement auth API' assigned to Backend Dev #1" },
  { id: 8, time: "10:23:08", level: "info", message: "Task 'Build dashboard UI' assigned to Frontend Dev" },
  { id: 9, time: "10:23:09", level: "error", message: "Agent 'Backend Dev #3' connection timeout after 30s" },
  { id: 10, time: "10:23:10", level: "info", message: "Retrying connection for Agent 'Backend Dev #3'..." },
  { id: 11, time: "10:23:11", level: "info", message: "Agent 'Backend Dev #3' reconnected successfully" },
  { id: 12, time: "10:23:12", level: "info", message: "Task 'Setup CI/CD pipeline' completed by Project Manager" },
  { id: 13, time: "10:23:13", level: "warn", message: "Rate limit approaching for API key (85% of quota)" },
  { id: 14, time: "10:23:14", level: "info", message: "Agent 'Tester #1' started with model claude-haiku-4-5" },
  { id: 15, time: "10:23:15", level: "info", message: "All agents operational. 4 running, 4 idle" },
]

const levelColors: Record<string, string> = { info: "text-amber-300", warn: "text-yellow-400", error: "text-red-400" }

export function RuntimePage() {
  const [running, setRunning] = useState(true)
  const [logs, setLogs] = useState(mockLogs)
  const [searchQuery, setSearchQuery] = useState("")
  const logEndRef = useRef<HTMLDivElement>(null)
  const { t } = useTranslation()

  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: "smooth" }) }, [logs])

  useEffect(() => {
    if (!running) return
    const interval = setInterval(() => {
      const messages = ["Heartbeat received from all active agents", "Task queue depth: 12 pending, 4 processing", "Memory usage: 342MB / 1024MB", "API latency: 245ms avg", "Checkpoint saved for Agent 'Backend Dev #1'", "New issue comment detected on AUT-143", "Agent 'Project Manager' dispatched subtask"]
      const levels: Array<"info" | "warn" | "error"> = ["info", "info", "info", "info", "warn", "error"]
      const now = new Date()
      const time = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}:${now.getSeconds().toString().padStart(2, "0")}`
      setLogs((prev) => [...prev, { id: prev.length + 1, time, level: levels[Math.floor(Math.random() * levels.length)], message: messages[Math.floor(Math.random() * messages.length)] }])
    }, 2000)
    return () => clearInterval(interval)
  }, [running])

  const filteredLogs = searchQuery ? logs.filter((l) => l.message.toLowerCase().includes(searchQuery.toLowerCase())) : logs

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold">{t("runtime.title")}</h1>
        <div className="flex items-center gap-2">
          <div className={cn("flex items-center gap-1.5 px-2 py-1 text-xs font-medium border", running ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" : "bg-zinc-500/15 text-zinc-400 border-zinc-500/30")}>
            <span className={cn("h-2 w-2", running ? "bg-emerald-500 animate-pulse" : "bg-zinc-500")} />
            {running ? t("runtime.running") : t("runtime.stopped")}
          </div>
          <button onClick={() => setRunning(!running)} className={cn("inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-opacity hover:opacity-90 pixel-border-sm", running ? "bg-destructive text-destructive-foreground border-destructive" : "bg-primary text-primary-foreground border-primary")}>
            {running ? <Square className="h-3 w-3" /> : <Play className="h-3 w-3" />}
            {running ? t("runtime.stop") : t("runtime.run")}
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-hidden flex flex-col pixel-border">
        <div className="flex-1 overflow-auto bg-zinc-950 p-3 font-mono text-xs leading-relaxed">
          {filteredLogs.map((log) => (
            <div key={log.id} className="flex gap-3">
              <span className="text-amber-700/60 shrink-0">{log.time}</span>
              <span className={cn("shrink-0 uppercase w-12", levelColors[log.level])}>[{log.level}]</span>
              <span className="text-amber-100/80">{log.message}</span>
            </div>
          ))}
          <div ref={logEndRef} />
        </div>
        <div className="border-t-2 border-border bg-card p-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input type="text" placeholder={t("runtime.searchPlaceholder")} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full border-2 border-input bg-background pl-8 pr-3 py-1.5 text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono" />
          </div>
        </div>
      </div>
    </div>
  )
}
