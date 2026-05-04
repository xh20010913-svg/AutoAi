/**
 * Whiteboard scene — real-time stats display board
 */

export interface WhiteboardStats {
  completed: number
  running: number
  pending: number
}

export function drawWhiteboard(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  stats: WhiteboardStats,
  prevStats: WhiteboardStats,
  frame: number,
) {
  const w = 100
  const h = 80

  // Board background
  ctx.fillStyle = "#1e293b"
  ctx.fillRect(x, y, w, h)

  // Border
  ctx.strokeStyle = "#475569"
  ctx.lineWidth = 2
  ctx.strokeRect(x, y, w, h)

  // Wood frame
  ctx.fillStyle = "#92400e"
  ctx.fillRect(x - 3, y - 3, w + 6, 3) // top
  ctx.fillRect(x - 3, y + h, w + 6, 3) // bottom
  ctx.fillRect(x - 3, y, 3, h) // left
  ctx.fillRect(x + w, y, 3, h) // right

  // Title
  ctx.fillStyle = "#f8fafc"
  ctx.font = "bold 9px monospace"
  ctx.textAlign = "center"
  ctx.fillText("TASK BOARD", x + w / 2, y + 14)

  // Divider
  ctx.fillStyle = "#475569"
  ctx.fillRect(x + 8, y + 18, w - 16, 1)

  // Stats
  const rows: { label: string; value: number; prevValue: number; color: string }[] = [
    { label: "Done", value: stats.completed, prevValue: prevStats.completed, color: "#22c55e" },
    { label: "Work", value: stats.running, prevValue: prevStats.running, color: "#3b82f6" },
    { label: "Todo", value: stats.pending, prevValue: prevStats.pending, color: "#f59e0b" },
  ]

  ctx.textAlign = "left"
  ctx.font = "8px monospace"

  rows.forEach((row, i) => {
    const ry = y + 30 + i * 16

    // Label
    ctx.fillStyle = "#94a3b8"
    ctx.fillText(row.label + ":", x + 8, ry)

    // Value — blink on change
    const changed = row.value !== row.prevValue
    const blink = changed && frame % 10 < 5
    ctx.fillStyle = blink ? "#fff" : row.color
    ctx.font = "bold 11px monospace"
    ctx.fillText(String(row.value).padStart(2, " "), x + 42, ry + 1)
    ctx.font = "8px monospace"

    // Dot
    ctx.fillStyle = row.color
    ctx.beginPath()
    ctx.arc(x + w - 12, ry - 2, 3, 0, Math.PI * 2)
    ctx.fill()
  })

  // Nail/hook at top
  ctx.fillStyle = "#64748b"
  ctx.fillRect(x + w / 2 - 1, y - 8, 2, 6)
  ctx.beginPath()
  ctx.arc(x + w / 2, y - 8, 3, 0, Math.PI * 2)
  ctx.fill()
}
