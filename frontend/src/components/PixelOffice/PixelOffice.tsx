import { useRef, useEffect, useCallback, useState } from "react"
import type { ColorPreset } from "./characters/animations"
import {
  createCharacter,
  updateCharacter,
  drawCharacter,
  type CharacterInstance,
  type PixelCharAgent,
} from "./characters/PixelCharacter"
import { drawWorkArea, type DeskSlot } from "./scenes/WorkArea"
import { drawRestArea, type SofaSlot } from "./scenes/RestArea"
import { drawWhiteboard, type WhiteboardStats } from "./scenes/Whiteboard"

export type { ColorPreset }

export interface PixelOfficeAgent {
  id: string
  name: string
  role: string
  status: "idle" | "running" | "error"
  colorPreset: ColorPreset
}

interface PixelOfficeProps {
  agents: PixelOfficeAgent[]
}

const CANVAS_HEIGHT = 380
const WORK_AREA_RATIO = 0.65

export function PixelOffice({ agents }: PixelOfficeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const charactersRef = useRef<CharacterInstance[]>([])
  const prevAgentsRef = useRef<PixelOfficeAgent[]>([])
  const deskSlotsRef = useRef<DeskSlot[]>([])
  const sofaSlotsRef = useRef<SofaSlot[]>([])
  const prevStatsRef = useRef<WhiteboardStats>({ completed: 0, running: 0, pending: 0 })
  const frameRef = useRef(0)
  const [canvasWidth, setCanvasWidth] = useState(800)

  // Responsive resize
  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setCanvasWidth(Math.max(600, entry.contentRect.width))
      }
    })
    observer.observe(container)
    return () => observer.disconnect()
  }, [])

  const getDeskSlot = useCallback((index: number): { x: number; y: number } => {
    const slots = deskSlotsRef.current
    if (index < slots.length) {
      return { x: slots[index].x, y: slots[index].y }
    }
    return { x: 50 + index * 80, y: 150 }
  }, [])

  const getSofaSlot = useCallback((index: number): { x: number; y: number } => {
    const slots = sofaSlotsRef.current
    if (index < slots.length) {
      return { x: slots[index].x, y: slots[index].y }
    }
    const workW = canvasWidth * WORK_AREA_RATIO
    return { x: workW + 50 + index * 60, y: 200 }
  }, [canvasWidth])

  // Initialize characters on agents change
  useEffect(() => {
    prevAgentsRef.current
    const workingAgents = agents.filter((a) => a.status === "running" || a.status === "error")
    const idleAgents = agents.filter((a) => a.status === "idle")

    // Map existing characters
    const existingMap = new Map(charactersRef.current.map((c) => [c.agent.id, c]))
    const newChars: CharacterInstance[] = []

    agents.forEach((agent, i) => {
      if (existingMap.has(agent.id)) {
        const existing = existingMap.get(agent.id)!
        // Update status
        const oldStatus = existing.agent.status
        existing.agent = agent as PixelCharAgent

        // If status changed, trigger transition
        if (oldStatus !== agent.status) {
          if (agent.status === "running" || agent.status === "error") {
            const workingIndex = workingAgents.findIndex((a) => a.id === agent.id)
            const desk = getDeskSlot(workingIndex >= 0 ? workingIndex : i)
            if (existing.state === "idle") {
              existing.state = "walking_to_desk"
              existing.targetX = desk.x
              existing.targetY = desk.y
            } else {
              existing.x = desk.x
              existing.y = desk.y
              existing.state = "working"
            }
          } else {
            const idleIndex = idleAgents.findIndex((a) => a.id === agent.id)
            const sofa = getSofaSlot(idleIndex >= 0 ? idleIndex : 0)
            if (existing.state === "working") {
              existing.state = "walking_to_sofa"
              existing.targetX = sofa.x
              existing.targetY = sofa.y
            } else {
              existing.x = sofa.x
              existing.y = sofa.y
              existing.state = "idle"
            }
          }
        }
        newChars.push(existing)
      } else {
        // New character
        const workingIndex = workingAgents.findIndex((a) => a.id === agent.id)
        const idleIndex = idleAgents.findIndex((a) => a.id === agent.id)
        const desk = getDeskSlot(workingIndex >= 0 ? workingIndex : i)
        const sofa = getSofaSlot(idleIndex >= 0 ? idleIndex : 0)
        newChars.push(createCharacter(agent as PixelCharAgent, desk.x, desk.y, sofa.x, sofa.y))
      }
    })

    charactersRef.current = newChars
    prevAgentsRef.current = [...agents]
  }, [agents, getDeskSlot, getSofaSlot])

  // Main render loop
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    let running = true

    function render() {
      if (!running) return
      const frame = frameRef.current++

      const w = canvasWidth
      const h = CANVAS_HEIGHT
      const dpr = window.devicePixelRatio || 1

      canvas!.width = w * dpr
      canvas!.height = h * dpr
      canvas!.style.width = `${w}px`
      canvas!.style.height = `${h}px`
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0)

      // Clear
      ctx!.fillStyle = "#f5f0e6"
      ctx!.fillRect(0, 0, w, h)

      const workW = w * WORK_AREA_RATIO
      const restW = w - workW
      const sceneH = h - 20

      // Draw floor line
      ctx!.fillStyle = "#b8a88a"
      ctx!.fillRect(0, sceneH * 0.7 + 10, w, 2)

      // Draw scenes
      deskSlotsRef.current = drawWorkArea(ctx!, 0, 10, workW, sceneH, Math.min(agents.length, 6), frame)
      sofaSlotsRef.current = drawRestArea(ctx!, workW, 10, restW, sceneH, frame)

      // Whiteboard (top-right of work area)
      const stats: WhiteboardStats = {
        completed: agents.filter((a) => a.status === "idle").length * 5 + 12,
        running: agents.filter((a) => a.status === "running").length,
        pending: agents.filter((a) => a.status === "error").length + 3,
      }
      drawWhiteboard(ctx!, workW - 115, 20, stats, prevStatsRef.current, frame)
      prevStatsRef.current = { ...stats }

      // Update and draw characters
      const dt = 1
      const workingAgents = agents.filter((a) => a.status === "running" || a.status === "error")
      const idleAgents = agents.filter((a) => a.status === "idle")

      charactersRef.current.forEach((char) => {
        const workingIndex = workingAgents.findIndex((a) => a.id === char.agent.id)
        const idleIndex = idleAgents.findIndex((a) => a.id === char.agent.id)
        const desk = getDeskSlot(workingIndex >= 0 ? workingIndex : 0)
        const sofa = getSofaSlot(idleIndex >= 0 ? idleIndex : 0)

        updateCharacter(char, dt, desk.x, desk.y, sofa.x, sofa.y)
        drawCharacter(ctx!, char)
      })

      // Error character red tint
      charactersRef.current.forEach((char) => {
        if (char.agent.status === "error" && char.state === "working") {
          const pulseAlpha = 0.15 + Math.sin(frame * 0.1) * 0.1
          ctx!.fillStyle = `rgba(239, 68, 68, ${pulseAlpha})`
          const charW = 10 * 3
          const charH = 12 * 3
          ctx!.fillRect(char.x - 4, char.y - 4, charW + 8, charH + 8)
        }
      })

      requestAnimationFrame(render)
    }

    render()
    return () => {
      running = false
    }
  }, [canvasWidth, agents, getDeskSlot, getSofaSlot])

  return (
    <div ref={containerRef} className="w-full pixel-border bg-card overflow-hidden">
      <canvas
        ref={canvasRef}
        style={{
          width: canvasWidth,
          height: CANVAS_HEIGHT,
          imageRendering: "pixelated",
          display: "block",
        }}
      />
    </div>
  )
}
