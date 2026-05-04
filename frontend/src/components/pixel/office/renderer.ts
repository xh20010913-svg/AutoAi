import {
  TILE, COLS, ROWS, CANVAS_W, CANVAS_H,
  TileType, SCREEN_COLORS, OFFICE_MAP,
} from "./constants"

// ── draw helpers ──────────────────────────────────────────────
function fillRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, color: string) {
  ctx.fillStyle = color
  ctx.fillRect(x, y, w, h)
}

// ── tile renderers ────────────────────────────────────────────
function drawWall(ctx: CanvasRenderingContext2D, x: number, y: number) {
  fillRect(ctx, x, y, TILE, TILE, "#4a4a5a")
  // Brick lines
  fillRect(ctx, x, y + TILE - 1, TILE, 1, "#3a3a4a")
  fillRect(ctx, x + TILE / 2, y, 1, TILE, "#3a3a4a")
  // Highlight
  fillRect(ctx, x, y, TILE, 1, "#5a5a6a")
}

function drawFloor(ctx: CanvasRenderingContext2D, x: number, y: number) {
  fillRect(ctx, x, y, TILE, TILE, "#c9b99a")
  // Subtle tile pattern
  fillRect(ctx, x + TILE - 1, y, 1, TILE, "#bfb18f")
  fillRect(ctx, x, y + TILE - 1, TILE, 1, "#bfb18f")
}

function drawDesk(ctx: CanvasRenderingContext2D, x: number, y: number) {
  drawFloor(ctx, x, y)
  fillRect(ctx, x + 1, y + 2, TILE - 2, TILE - 4, "#8B6914")
  fillRect(ctx, x + 1, y + 2, TILE - 2, 1, "#a07818") // highlight
  fillRect(ctx, x + 1, y + TILE - 3, TILE - 2, 1, "#6b4f10") // shadow
}

function drawMonitor(ctx: CanvasRenderingContext2D, x: number, y: number, frame: number) {
  drawFloor(ctx, x, y)
  // Monitor body
  fillRect(ctx, x + 2, y + 1, TILE - 4, TILE - 5, "#2d3748")
  // Screen
  const screenColor = SCREEN_COLORS[frame % SCREEN_COLORS.length]
  fillRect(ctx, x + 3, y + 2, TILE - 6, TILE - 7, screenColor)
  // Screen glow
  fillRect(ctx, x + 4, y + 3, 2, 2, "#ffffff30")
  // Stand
  fillRect(ctx, x + 5, y + TILE - 4, TILE - 10, 2, "#2d3748")
  // Stand base
  fillRect(ctx, x + 3, y + TILE - 2, TILE - 6, 1, "#2d3748")
}

function drawChair(ctx: CanvasRenderingContext2D, x: number, y: number) {
  drawFloor(ctx, x, y)
  // Seat
  fillRect(ctx, x + 3, y + 5, TILE - 6, TILE - 7, "#6b7280")
  // Back
  fillRect(ctx, x + 4, y + 2, TILE - 8, 4, "#4b5563")
  // Wheels
  fillRect(ctx, x + 4, y + TILE - 2, 2, 2, "#4b5563")
  fillRect(ctx, x + TILE - 6, y + TILE - 2, 2, 2, "#4b5563")
}

function drawSofa(ctx: CanvasRenderingContext2D, x: number, y: number) {
  drawFloor(ctx, x, y)
  // Sofa back
  fillRect(ctx, x + 1, y + 1, TILE - 2, TILE - 5, "#7c3aed")
  // Sofa seat
  fillRect(ctx, x + 1, y + 6, TILE - 2, TILE - 7, "#8b5cf6")
  // Armrests
  fillRect(ctx, x, y + 2, 2, TILE - 3, "#6d28d9")
  fillRect(ctx, x + TILE - 2, y + 2, 2, TILE - 3, "#6d28d9")
  // Cushion highlights
  fillRect(ctx, x + 3, y + 7, 3, 1, "#a78bfa")
  fillRect(ctx, x + TILE - 6, y + 7, 3, 1, "#a78bfa")
}

function drawTable(ctx: CanvasRenderingContext2D, x: number, y: number) {
  drawFloor(ctx, x, y)
  fillRect(ctx, x + 2, y + 4, TILE - 4, TILE - 6, "#92400e")
  fillRect(ctx, x + 2, y + 4, TILE - 4, 1, "#a07818")
  // Legs
  fillRect(ctx, x + 3, y + TILE - 3, 2, 3, "#78350f")
  fillRect(ctx, x + TILE - 5, y + TILE - 3, 2, 3, "#78350f")
}

function drawPlant(ctx: CanvasRenderingContext2D, x: number, y: number) {
  drawFloor(ctx, x, y)
  // Pot
  fillRect(ctx, x + 4, y + 10, TILE - 8, TILE - 10, "#8B4513")
  fillRect(ctx, x + 3, y + 9, TILE - 6, 2, "#A0522D")
  // Leaves
  fillRect(ctx, x + 5, y + 3, 6, 7, "#16a34a")
  fillRect(ctx, x + 3, y + 5, 4, 4, "#15803d")
  fillRect(ctx, x + 9, y + 5, 4, 4, "#15803d")
  fillRect(ctx, x + 6, y + 1, 4, 4, "#22c55e")
}

function drawCoffee(ctx: CanvasRenderingContext2D, x: number, y: number) {
  drawFloor(ctx, x, y)
  // Machine body
  fillRect(ctx, x + 3, y + 3, TILE - 6, TILE - 4, "#4a4a5a")
  fillRect(ctx, x + 4, y + 2, TILE - 8, 2, "#5a5a6a")
  // Screen
  fillRect(ctx, x + 5, y + 5, 6, 4, "#10b981")
  // Dispenser
  fillRect(ctx, x + 5, y + 10, 6, 3, "#374151")
  // Cup
  fillRect(ctx, x + 6, y + 11, 4, 2, "#f3f4f6")
}

function drawBoard(ctx: CanvasRenderingContext2D, x: number, y: number, frame: number) {
  // Wall behind
  fillRect(ctx, x, y, TILE, TILE, "#4a4a5a")
  // Board surface
  fillRect(ctx, x + 1, y + 1, TILE - 2, TILE - 2, "#f5f5dc")
  // Board frame
  fillRect(ctx, x + 1, y + 1, TILE - 2, 1, "#78350f") // top
  fillRect(ctx, x + 1, y + TILE - 2, TILE - 2, 1, "#78350f") // bottom
  fillRect(ctx, x + 1, y + 1, 1, TILE - 2, "#78350f") // left
  fillRect(ctx, x + TILE - 2, y + 1, 1, TILE - 2, "#78350f") // right
  // Chalk text (pixels that change with frame)
  const textColors = ["#1a1a2e", "#3b82f6", "#ef4444", "#16a34a"]
  const tc = textColors[frame % textColors.length]
  fillRect(ctx, x + 3, y + 4, 6, 1, tc)
  fillRect(ctx, x + 3, y + 6, 8, 1, tc)
  fillRect(ctx, x + 3, y + 8, 5, 1, tc)
  fillRect(ctx, x + 3, y + 10, 7, 1, tc)
}

function drawRug(ctx: CanvasRenderingContext2D, x: number, y: number) {
  fillRect(ctx, x, y, TILE, TILE, "#a16207")
  // Pattern
  fillRect(ctx, x + 2, y + 2, TILE - 4, TILE - 4, "#ca8a04")
  fillRect(ctx, x + 4, y + 4, TILE - 8, TILE - 8, "#eab308")
}

// ── main renderer ─────────────────────────────────────────────
export function renderOffice(ctx: CanvasRenderingContext2D, frame: number) {
  // Clear
  ctx.fillStyle = "#1a1a2e"
  ctx.fillRect(0, 0, CANVAS_W, CANVAS_H)

  // Draw tiles
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const x = c * TILE
      const y = r * TILE
      const tile = OFFICE_MAP[r][c] as TileType

      switch (tile) {
        case TileType.WALL: drawWall(ctx, x, y); break
        case TileType.FLOOR: drawFloor(ctx, x, y); break
        case TileType.DESK: drawDesk(ctx, x, y); break
        case TileType.MONITOR: drawMonitor(ctx, x, y, frame); break
        case TileType.CHAIR: drawChair(ctx, x, y); break
        case TileType.SOFA: drawSofa(ctx, x, y); break
        case TileType.TABLE: drawTable(ctx, x, y); break
        case TileType.PLANT: drawPlant(ctx, x, y); break
        case TileType.COFFEE: drawCoffee(ctx, x, y); break
        case TileType.BOARD: drawBoard(ctx, x, y, frame); break
        case TileType.RUG: drawRug(ctx, x, y); break
        default: break
      }
    }
  }

  // Labels
  ctx.font = "bold 10px monospace"
  ctx.textAlign = "center"

  // Office label
  ctx.fillStyle = "#fbbf24"
  ctx.fillText("OFFICE", 8 * TILE, 1.2 * TILE)

  // Rest area label
  ctx.fillStyle = "#a78bfa"
  ctx.fillText("REST AREA", 8 * TILE, 18.8 * TILE)

  // Blackboard label
  ctx.fillStyle = "#9ca3af"
  ctx.fillText("BLACKBOARD", 14 * TILE, 14.2 * TILE)
}
