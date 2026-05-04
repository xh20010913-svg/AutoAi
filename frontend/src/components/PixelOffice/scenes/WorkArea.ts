/**
 * Work Area scene — draws desks, monitors, dividers, and wall decorations
 */

export interface DeskSlot {
  x: number
  y: number // character sit position
  deskX: number
  deskY: number
}

export function drawWorkArea(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  deskCount: number,
  frame: number,
): DeskSlot[] {
  const slots: DeskSlot[] = []

  // Floor
  ctx.fillStyle = "#d4c5a0"
  ctx.fillRect(x, y + h * 0.7, w, h * 0.3)

  // Floor tile pattern
  ctx.fillStyle = "#c9b896"
  for (let tx = x; tx < x + w; tx += 20) {
    for (let ty = y + h * 0.7; ty < y + h; ty += 20) {
      if ((Math.floor((tx - x) / 20) + Math.floor((ty - y - h * 0.7) / 20)) % 2 === 0) {
        ctx.fillRect(tx, ty, 20, 20)
      }
    }
  }

  // Back wall
  ctx.fillStyle = "#e8dcc8"
  ctx.fillRect(x, y, w, h * 0.7)

  // Wall trim
  ctx.fillStyle = "#b8a88a"
  ctx.fillRect(x, y + h * 0.7 - 4, w, 4)

  // Wall decorations — calendar
  drawCalendar(ctx, x + w * 0.15, y + 15, 30, 35)

  // Sticky notes on wall
  drawStickyNote(ctx, x + w * 0.55, y + 12, "#fef08a", 16)
  drawStickyNote(ctx, x + w * 0.62, y + 18, "#bbf7d0", 14)
  drawStickyNote(ctx, x + w * 0.68, y + 10, "#fecaca", 15)

  // Desks
  const deskW = 50
  const deskH = 30
  const spacing = w / deskCount

  for (let i = 0; i < deskCount; i++) {
    const deskX = x + spacing * i + (spacing - deskW) / 2
    const deskY = y + h * 0.45

    drawDesk(ctx, deskX, deskY, deskW, deskH, frame)

    // Divider panels between desks
    if (i > 0) {
      ctx.fillStyle = "#94a3b8"
      const divX = x + spacing * i - 2
      ctx.fillRect(divX, deskY - 15, 3, 35)
      // Fabric texture
      ctx.fillStyle = "#cbd5e1"
      for (let dy = deskY - 13; dy < deskY + 18; dy += 3) {
        ctx.fillRect(divX, dy, 3, 1)
      }
    }

    slots.push({
      x: deskX - 8,
      y: deskY - 28,
      deskX,
      deskY,
    })
  }

  return slots
}

function drawDesk(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, frame: number) {
  // Desk legs
  ctx.fillStyle = "#78350f"
  ctx.fillRect(x + 3, y + h - 4, 4, 20)
  ctx.fillRect(x + w - 7, y + h - 4, 4, 20)

  // Desk surface
  ctx.fillStyle = "#92400e"
  ctx.fillRect(x, y + h - 8, w, 8)
  ctx.fillStyle = "#a3613a"
  ctx.fillRect(x, y + h - 8, w, 2) // highlight

  // Monitor
  ctx.fillStyle = "#374151"
  ctx.fillRect(x + w / 2 - 12, y - 8, 24, 18)

  // Screen
  const glowPhase = Math.sin(frame * 0.05) * 0.15
  ctx.fillStyle = `rgba(59, 130, 246, ${0.6 + glowPhase})`
  ctx.fillRect(x + w / 2 - 10, y - 6, 20, 12)

  // Screen scanline
  const scanY = (frame * 2) % 12
  ctx.fillStyle = "rgba(96, 165, 250, 0.3)"
  ctx.fillRect(x + w / 2 - 10, y - 6 + scanY, 20, 1)

  // Monitor stand
  ctx.fillStyle = "#374151"
  ctx.fillRect(x + w / 2 - 3, y + 10, 6, 5)
  ctx.fillRect(x + w / 2 - 6, y + 14, 12, 3)

  // Keyboard
  ctx.fillStyle = "#6b7280"
  ctx.fillRect(x + w / 2 - 8, y + h - 16, 16, 5)
  // Keys
  ctx.fillStyle = "#9ca3af"
  for (let kx = 0; kx < 4; kx++) {
    for (let ky = 0; ky < 2; ky++) {
      ctx.fillRect(x + w / 2 - 7 + kx * 4, y + h - 15 + ky * 2, 3, 1)
    }
  }

  // Coffee mug
  ctx.fillStyle = "#f3f4f6"
  ctx.fillRect(x + w - 8, y + h - 14, 5, 6)
  // Mug handle
  ctx.fillStyle = "#e5e7eb"
  ctx.fillRect(x + w - 3, y + h - 12, 3, 1)
  ctx.fillRect(x + w - 3, y + h - 10, 3, 1)
  ctx.fillRect(x + w - 3, y + h - 12, 1, 3)
}

function drawCalendar(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number) {
  // Calendar background
  ctx.fillStyle = "#fff"
  ctx.fillRect(x, y, w, h)
  ctx.strokeStyle = "#94a3b8"
  ctx.strokeRect(x, y, w, h)

  // Header
  ctx.fillStyle = "#ef4444"
  ctx.fillRect(x + 1, y + 1, w - 2, 8)

  // Grid lines
  ctx.strokeStyle = "#e5e7eb"
  const cellW = (w - 2) / 4
  const cellH = 6
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 4; c++) {
      ctx.strokeRect(x + 1 + c * cellW, y + 10 + r * cellH, cellW, cellH)
    }
  }

  // Date number
  ctx.fillStyle = "#3b82f6"
  ctx.fillRect(x + cellW * 2 + 3, y + 10 + cellH + 2, 4, 3)
}

function drawStickyNote(ctx: CanvasRenderingContext2D, x: number, y: number, color: string, size: number) {
  ctx.fillStyle = color
  ctx.fillRect(x, y, size, size)
  // Slight curl
  ctx.fillStyle = "rgba(0,0,0,0.05)"
  ctx.fillRect(x + size - 3, y + size - 3, 3, 3)
  // Text lines
  ctx.fillStyle = "rgba(0,0,0,0.2)"
  ctx.fillRect(x + 2, y + 4, size - 6, 1)
  ctx.fillRect(x + 2, y + 7, size - 8, 1)
  ctx.fillRect(x + 2, y + 10, size - 5, 1)
}
