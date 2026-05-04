import { useRef, useEffect, useCallback } from "react"
import { CANVAS_W, CANVAS_H } from "./constants"
import { renderOffice } from "./renderer"
import { createAgents, updateAgents, renderAgents, type AgentState, type PaletteKey } from "./agents"

interface AgentData {
  name: string
  palette: PaletteKey
  state: AgentState
}

interface PixelOfficeProps {
  agents?: AgentData[]
}

const DEFAULT_AGENTS: AgentData[] = [
  { name: "PM", palette: "blue", state: "working" },
  { name: "BE-1", palette: "green", state: "working" },
  { name: "BE-2", palette: "purple", state: "idle" },
  { name: "BE-3", palette: "amber", state: "error" },
  { name: "FE", palette: "pink", state: "working" },
  { name: "QA-1", palette: "cyan", state: "idle" },
  { name: "QA-2", palette: "red", state: "working" },
  { name: "QA-3", palette: "teal", state: "idle" },
]

export function PixelOffice({ agents: agentData }: PixelOfficeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const agentsRef = useRef(createAgents(agentData ?? DEFAULT_AGENTS))
  const frameRef = useRef(0)
  const rafRef = useRef<number>(0)

  const tick = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    frameRef.current++
    updateAgents(agentsRef.current)

    renderOffice(ctx, frameRef.current)
    renderAgents(ctx, agentsRef.current)

    rafRef.current = requestAnimationFrame(tick)
  }, [])

  useEffect(() => {
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [tick])

  // Update agents if prop changes
  useEffect(() => {
    if (agentData) {
      agentsRef.current = createAgents(agentData)
    }
  }, [agentData])

  return (
    <div className="relative pixel-border overflow-hidden bg-background">
      <canvas
        ref={canvasRef}
        width={CANVAS_W}
        height={CANVAS_H}
        style={{
          width: "100%",
          height: "auto",
          imageRendering: "pixelated",
          maxWidth: CANVAS_W,
        }}
      />
      {/* Legend */}
      <div className="absolute bottom-2 right-2 bg-background/80 border border-border px-2 py-1 text-[10px] font-mono text-muted-foreground">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 bg-emerald-500" /> Working
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 bg-zinc-500" /> Idle
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 bg-red-500 animate-pulse" /> Error
          </span>
        </div>
      </div>
    </div>
  )
}
