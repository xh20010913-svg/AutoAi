import { TILE, isWalkable, CHAIR_POSITIONS, SOFA_POSITIONS } from "./constants"

// ── Agent color palettes ─────────────────────────────────────
export const AGENT_PALETTES = {
  blue:   { hair: "#6366f1", shirt: "#3b82f6", pants: "#475569" },
  green:  { hair: "#10b981", shirt: "#22c55e", pants: "#475569" },
  purple: { hair: "#a855f7", shirt: "#8b5cf6", pants: "#475569" },
  amber:  { hair: "#f59e0b", shirt: "#eab308", pants: "#475569" },
  pink:   { hair: "#ec4899", shirt: "#f472b6", pants: "#475569" },
  cyan:   { hair: "#06b6d4", shirt: "#0ea5e9", pants: "#475569" },
  red:    { hair: "#ef4444", shirt: "#f87171", pants: "#475569" },
  teal:   { hair: "#14b8a6", shirt: "#2dd4bf", pants: "#475569" },
} as const

export type PaletteKey = keyof typeof AGENT_PALETTES

// ── Sprite data ──────────────────────────────────────────────
// 6x8 pixel sprite, values: 0=transparent 1=hair 2=skin 3=shirt 4=pants
const SPRITES: Record<string, number[][]> = {
  walkDown1: [
    [0,0,1,1,0,0],
    [0,1,2,2,1,0],
    [0,0,2,2,0,0],
    [0,0,3,3,0,0],
    [0,3,3,3,3,0],
    [0,0,3,3,0,0],
    [0,0,4,4,0,0],
    [0,2,0,0,2,0],
  ],
  walkDown2: [
    [0,0,1,1,0,0],
    [0,1,2,2,1,0],
    [0,0,2,2,0,0],
    [0,0,3,3,0,0],
    [0,3,3,3,3,0],
    [0,0,3,3,0,0],
    [0,0,4,4,0,0],
    [0,0,2,2,0,0],
  ],
  walkUp1: [
    [0,0,1,1,0,0],
    [0,1,1,1,1,0],
    [0,0,1,1,0,0],
    [0,0,3,3,0,0],
    [0,3,3,3,3,0],
    [0,0,3,3,0,0],
    [0,0,4,4,0,0],
    [0,2,0,0,2,0],
  ],
  walkUp2: [
    [0,0,1,1,0,0],
    [0,1,1,1,1,0],
    [0,0,1,1,0,0],
    [0,0,3,3,0,0],
    [0,3,3,3,3,0],
    [0,0,3,3,0,0],
    [0,0,4,4,0,0],
    [0,0,2,2,0,0],
  ],
  walkLeft1: [
    [0,0,1,1,0,0],
    [0,1,2,2,1,0],
    [0,0,2,2,0,0],
    [0,0,3,3,0,0],
    [0,3,3,3,3,0],
    [0,0,3,3,0,0],
    [0,0,4,4,0,0],
    [0,2,0,0,0,0],
  ],
  walkLeft2: [
    [0,0,1,1,0,0],
    [0,1,2,2,1,0],
    [0,0,2,2,0,0],
    [0,0,3,3,0,0],
    [0,3,3,3,3,0],
    [0,0,3,3,0,0],
    [0,0,4,4,0,0],
    [0,0,0,0,2,0],
  ],
  walkRight1: [
    [0,0,1,1,0,0],
    [0,1,2,2,1,0],
    [0,0,2,2,0,0],
    [0,0,3,3,0,0],
    [0,3,3,3,3,0],
    [0,0,3,3,0,0],
    [0,0,4,4,0,0],
    [0,0,0,0,2,0],
  ],
  walkRight2: [
    [0,0,1,1,0,0],
    [0,1,2,2,1,0],
    [0,0,2,2,0,0],
    [0,0,3,3,0,0],
    [0,3,3,3,3,0],
    [0,0,3,3,0,0],
    [0,0,4,4,0,0],
    [0,2,0,0,0,0],
  ],
  sit: [
    [0,0,1,1,0,0],
    [0,1,2,2,1,0],
    [0,0,2,2,0,0],
    [0,0,3,3,0,0],
    [0,3,3,3,3,0],
    [0,0,3,3,0,0],
    [0,0,4,4,0,0],
    [0,0,2,2,0,0],
  ],
  sitType: [
    [0,0,0,0,0,0],
    [0,0,1,1,0,0],
    [0,1,2,2,1,0],
    [0,0,2,2,0,0],
    [0,0,3,3,0,0],
    [0,3,3,3,3,0],
    [0,2,3,3,2,0],
    [0,0,4,4,0,0],
  ],
}

// ── Agent class ──────────────────────────────────────────────
export type AgentState = "idle" | "walking" | "working" | "error"

interface AgentConfig {
  name: string
  palette: PaletteKey
  state: AgentState
  targetDesk?: { row: number; col: number }
  targetSofa?: { row: number; col: number }
}

export interface AgentInstance {
  name: string
  palette: PaletteKey
  state: AgentState
  // Current pixel position (smooth)
  px: number
  py: number
  // Path
  path: Array<{ x: number; y: number }>
  pathIndex: number
  // Animation
  walkFrame: number
  walkTimer: number
  lastDir: "down" | "up" | "left" | "right"
  // Sit positions
  deskPos: { row: number; col: number } | null
  sofaPos: { row: number; col: number } | null
  // Typing animation
  typingTimer: number
  typingUp: boolean
  // Idle timer for returning to work
  idleTimer: number
  // Error flash
  errorFlash: number
}

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

export function createAgents(configs: AgentConfig[]): AgentInstance[] {
  const usedDesks = new Set<string>()
  const usedSofas = new Set<string>()
  const shuffledDesks = shuffle(CHAIR_POSITIONS)
  const shuffledSofas = shuffle(SOFA_POSITIONS)

  return configs.map((cfg) => {
    let deskPos: { row: number; col: number } | null = null
    let sofaPos: { row: number; col: number } | null = null

    // Assign a desk
    for (const d of shuffledDesks) {
      const key = `${d.row},${d.col}`
      if (!usedDesks.has(key)) {
        usedDesks.add(key)
        deskPos = d
        break
      }
    }

    // Assign a sofa
    for (const s of shuffledSofas) {
      const key = `${s.row},${s.col}`
      if (!usedSofas.has(key)) {
        usedSofas.add(key)
        sofaPos = s
        break
      }
    }

    // Start at desk if working, sofa if idle
    const startPos = (cfg.state === "idle" || cfg.state === "error") && sofaPos
      ? sofaPos
      : deskPos ?? { row: 3, col: 5 }

    return {
      name: cfg.name,
      palette: cfg.palette,
      state: cfg.state,
      px: startPos.col * TILE + TILE / 2,
      py: startPos.row * TILE + TILE / 2,
      path: [],
      pathIndex: 0,
      walkFrame: 0,
      walkTimer: 0,
      lastDir: "down",
      deskPos,
      sofaPos,
      typingTimer: 0,
      typingUp: false,
      idleTimer: 0,
      errorFlash: 0,
    }
  })
}

// ── Simple pathfinding (BFS) ─────────────────────────────────
function bfs(
  startR: number, startC: number,
  endR: number, endC: number,
): Array<{ x: number; y: number }> {
  const visited = new Set<string>()
  const queue: Array<{ r: number; c: number; path: Array<{ x: number; y: number }> }> = []
  const startKey = `${startR},${startC}`

  queue.push({ r: startR, c: startC, path: [{ x: startC * TILE + TILE / 2, y: startR * TILE + TILE / 2 }] })
  visited.add(startKey)

  const dirs = [[0,1],[0,-1],[1,0],[-1,0]]

  while (queue.length > 0) {
    const { r, c, path } = queue.shift()!

    if (r === endR && c === endC) return path

    for (const [dr, dc] of dirs) {
      const nr = r + dr
      const nc = c + dc
      const key = `${nr},${nc}`
      if (!visited.has(key) && isWalkable(nr, nc)) {
        visited.add(key)
        queue.push({
          r: nr,
          c: nc,
          path: [...path, { x: nc * TILE + TILE / 2, y: nr * TILE + TILE / 2 }],
        })
      }
    }
  }

  // No path found, return empty
  return []
}

// Walkable spot adjacent to a target tile
function findAdjacentWalkable(row: number, col: number): { r: number; c: number } | null {
  const dirs = [[0,1],[0,-1],[1,0],[-1,0]]
  for (const [dr, dc] of dirs) {
    const nr = row + dr
    const nc = col + dc
    if (isWalkable(nr, nc)) return { r: nr, c: nc }
  }
  return null
}

// ── Update agents ────────────────────────────────────────────
const SPEED = 1.2 // pixels per frame

export function updateAgents(agents: AgentInstance[]) {
  for (const agent of agents) {
    // Error flash
    if (agent.state === "error") {
      agent.errorFlash = (agent.errorFlash + 1) % 60
      continue // Don't move
    }

    // Walking
    if (agent.path.length > 0 && agent.pathIndex < agent.path.length) {
      const target = agent.path[agent.pathIndex]
      const dx = target.x - agent.px
      const dy = target.y - agent.py
      const dist = Math.sqrt(dx * dx + dy * dy)

      if (dist < SPEED) {
        agent.px = target.x
        agent.py = target.y
        agent.pathIndex++
      } else {
        agent.px += (dx / dist) * SPEED
        agent.py += (dy / dist) * SPEED

        // Update direction
        if (Math.abs(dx) > Math.abs(dy)) {
          agent.lastDir = dx > 0 ? "right" : "left"
        } else {
          agent.lastDir = dy > 0 ? "down" : "up"
        }
      }

      // Walk animation
      agent.walkTimer++
      if (agent.walkTimer > 8) {
        agent.walkTimer = 0
        agent.walkFrame = 1 - agent.walkFrame
      }

      // Arrived at destination
      if (agent.pathIndex >= agent.path.length) {
        agent.path = []
        agent.pathIndex = 0
        agent.walkFrame = 0
      }
      continue
    }

    // Typing animation for working agents
    if (agent.state === "working") {
      agent.typingTimer++
      if (agent.typingTimer > 6) {
        agent.typingTimer = 0
        agent.typingUp = !agent.typingUp
      }
    }

    // Idle agents occasionally walk to desk or another sofa
    if (agent.state === "idle" && agent.path.length === 0) {
      agent.idleTimer++
      if (agent.idleTimer > 300 && Math.random() < 0.01) {
        agent.idleTimer = 0
        // Walk to desk briefly then back
        const desk = agent.deskPos
        if (desk) {
          const adj = findAdjacentWalkable(desk.row, desk.col)
          if (adj) {
            const curR = Math.floor(agent.py / TILE)
            const curC = Math.floor(agent.px / TILE)
            const newPath = bfs(curR, curC, adj.r, adj.c)
            if (newPath.length > 1) {
              agent.path = newPath
              agent.pathIndex = 0
              agent.state = "walking"

              // After reaching desk, become working briefly
              setTimeout(() => {
                if (agent.state === "walking") {
                  agent.state = "working"
                  // After a bit, go back to sofa
                  setTimeout(() => {
                    if (agent.state === "working" && agent.sofaPos) {
                      const sofaAdj = findAdjacentWalkable(agent.sofaPos.row, agent.sofaPos.col)
                      if (sofaAdj) {
                        const cr = Math.floor(agent.py / TILE)
                        const cc = Math.floor(agent.px / TILE)
                        const returnPath = bfs(cr, cc, sofaAdj.r, sofaAdj.c)
                        if (returnPath.length > 1) {
                          agent.path = returnPath
                          agent.pathIndex = 0
                          agent.state = "walking"
                          setTimeout(() => {
                            if (agent.state === "walking") agent.state = "idle"
                          }, returnPath.length * 14)
                        }
                      }
                    }
                  }, 3000 + Math.random() * 2000)
                }
              }, newPath.length * 14)
            }
          }
        }
      }
    }
  }
}

// ── Render agents ─────────────────────────────────────────────
export function renderAgents(ctx: CanvasRenderingContext2D, agents: AgentInstance[]) {
  // Sort by Y for depth
  const sorted = [...agents].sort((a, b) => a.py - b.py)

  for (const agent of sorted) {
    const palette = AGENT_PALETTES[agent.palette]
    const skin = "#fbbf24"
    const colors = { 1: palette.hair, 2: skin, 3: palette.shirt, 4: palette.pants }

    // Pick sprite
    let sprite: number[][]
    if (agent.state === "working") {
      sprite = agent.typingUp ? SPRITES.sitType : SPRITES.sit
    } else if (agent.path.length > 0) {
      const dir = agent.lastDir
      const frame = agent.walkFrame
      const key = `walk${dir.charAt(0).toUpperCase() + dir.slice(1)}${frame + 1}`
      sprite = SPRITES[key] ?? SPRITES.walkDown1
    } else {
      sprite = SPRITES.walkDown2 // Standing
    }

    // Error effect: red tint
    const isError = agent.state === "error"
    const flash = isError && agent.errorFlash < 30

    const spriteW = sprite[0].length
    const spriteH = sprite.length
    const px = 2 // pixel size for sprite
    const offsetX = agent.px - (spriteW * px) / 2
    const offsetY = agent.py - (spriteH * px) / 2

    for (let r = 0; r < spriteH; r++) {
      for (let c = 0; c < spriteW; c++) {
        const v = sprite[r][c]
        if (v === 0) continue

        const color = flash && v === 3 ? "#ef4444" : colors[v as keyof typeof colors]
        ctx.fillStyle = color
        ctx.fillRect(
          Math.round(offsetX + c * px),
          Math.round(offsetY + r * px),
          px, px,
        )
      }
    }

    // Name label
    ctx.font = "bold 7px monospace"
    ctx.textAlign = "center"
    ctx.fillStyle = isError ? "#ef4444" : "#ffffff"
    ctx.strokeStyle = "#000000"
    ctx.lineWidth = 2
    ctx.strokeText(agent.name, Math.round(agent.px), Math.round(offsetY - 2))
    ctx.fillText(agent.name, Math.round(agent.px), Math.round(offsetY - 2))
  }
}
