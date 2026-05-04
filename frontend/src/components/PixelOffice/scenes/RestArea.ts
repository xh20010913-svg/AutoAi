/**
 * Rest Area scene — draws sofa, coffee table, plants, and floor
 */

export interface SofaSlot {
  x: number
  y: number
}

export function drawRestArea(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  frame: number,
): SofaSlot[] {
  const slots: SofaSlot[] = []

  // Floor — different color from work area
  ctx.fillStyle = "#c4b590"
  ctx.fillRect(x, y + h * 0.7, w, h * 0.3)

  // Rug
  ctx.fillStyle = "#a78b71"
  const rugX = x + w * 0.1
  const rugY = y + h * 0.72
  const rugW = w * 0.8
  const rugH = h * 0.22
  ctx.fillRect(rugX, rugY, rugW, rugH)
  // Rug pattern
  ctx.fillStyle = "#8b7355"
  ctx.fillRect(rugX + 4, rugY + 4, rugW - 8, 2)
  ctx.fillRect(rugX + 4, rugY + rugH - 6, rugW - 8, 2)
  ctx.fillRect(rugX + 4, rugY + 4, 2, rugH - 8)
  ctx.fillRect(rugX + rugW - 6, rugY + 4, 2, rugH - 8)

  // Back wall
  ctx.fillStyle = "#e0d5c0"
  ctx.fillRect(x, y, w, h * 0.7)

  // Wall trim
  ctx.fillStyle = "#b8a88a"
  ctx.fillRect(x, y + h * 0.7 - 4, w, 4)

  // Big Sofa
  const sofaX = x + w * 0.15
  const sofaY = y + h * 0.5
  const sofaW = w * 0.6
  const sofaH = 35

  // Sofa back
  ctx.fillStyle = "#7c3aed"
  ctx.fillRect(sofaX, sofaY - sofaH + 12, sofaW, sofaH)

  // Sofa back cushion highlight
  ctx.fillStyle = "#8b5cf6"
  ctx.fillRect(sofaX + 3, sofaY - sofaH + 14, sofaW * 0.45 - 3, sofaH - 16)
  ctx.fillRect(sofaX + sofaW * 0.45 + 3, sofaY - sofaH + 14, sofaW * 0.55 - 6, sofaH - 16)

  // Sofa seat
  ctx.fillStyle = "#8b5cf6"
  ctx.fillRect(sofaX, sofaY, sofaW, 14)

  // Sofa cushions (dividers)
  ctx.fillStyle = "#6d28d9"
  ctx.fillRect(sofaX + sofaW * 0.33, sofaY - sofaH + 14, 2, sofaH - 2)
  ctx.fillRect(sofaX + sofaW * 0.66, sofaY - sofaH + 14, 2, sofaH - 2)

  // Left armrest
  ctx.fillStyle = "#7c3aed"
  ctx.fillRect(sofaX - 8, sofaY - sofaH + 16, 10, sofaH - 4)
  // Right armrest
  ctx.fillRect(sofaX + sofaW - 2, sofaY - sofaH + 16, 10, sofaH - 4)

  // Sofa legs
  ctx.fillStyle = "#5b21b6"
  ctx.fillRect(sofaX + 4, sofaY + 14, 4, 6)
  ctx.fillRect(sofaX + sofaW - 8, sofaY + 14, 4, 6)

  // Sofa slots (2 positions)
  slots.push({ x: sofaX + 15, y: sofaY - 30 })
  slots.push({ x: sofaX + sofaW * 0.45, y: sofaY - 30 })

  // Coffee table
  const tableX = x + w * 0.3
  const tableY = sofaY + sofaH + 8
  ctx.fillStyle = "#92400e"
  ctx.fillRect(tableX, tableY, 40, 4)
  ctx.fillStyle = "#78350f"
  ctx.fillRect(tableX + 4, tableY + 4, 3, 14)
  ctx.fillRect(tableX + 33, tableY + 4, 3, 14)

  // Coffee cups on table
  drawCoffeeCup(ctx, tableX + 10, tableY - 7, frame)
  drawCoffeeCup(ctx, tableX + 24, tableY - 7, frame)

  // Magazine on table
  ctx.fillStyle = "#f472b6"
  ctx.fillRect(tableX + 15, tableY - 2, 8, 3)
  ctx.fillStyle = "#ec4899"
  ctx.fillRect(tableX + 15, tableY - 2, 8, 1)

  // Potted plant (left side)
  drawPlant(ctx, x + w * 0.08, y + h * 0.55, frame)

  // Potted plant (right side)
  drawPlant(ctx, x + w * 0.85, y + h * 0.6, frame)

  // Bookshelf on wall
  drawBookshelf(ctx, x + w * 0.7, y + 10, 25, 40)

  return slots
}

function drawCoffeeCup(ctx: CanvasRenderingContext2D, x: number, y: number, frame: number) {
  // Cup body
  ctx.fillStyle = "#f3f4f6"
  ctx.fillRect(x, y, 7, 8)
  // Cup rim
  ctx.fillStyle = "#d1d5db"
  ctx.fillRect(x, y, 7, 1)
  // Coffee inside
  ctx.fillStyle = "#78350f"
  ctx.fillRect(x + 1, y + 1, 5, 3)
  // Handle
  ctx.fillStyle = "#e5e7eb"
  ctx.fillRect(x + 7, y + 2, 3, 1)
  ctx.fillRect(x + 7, y + 5, 3, 1)
  ctx.fillRect(x + 9, y + 2, 1, 4)

  // Steam
  const steamAlpha = 0.2 + Math.sin(frame * 0.08 + x) * 0.15
  ctx.fillStyle = `rgba(255,255,255,${steamAlpha})`
  ctx.fillRect(x + 2, y - 4 - Math.sin(frame * 0.05) * 2, 2, 3)
  ctx.fillRect(x + 4, y - 5 - Math.cos(frame * 0.06) * 2, 2, 3)
}

function drawPlant(ctx: CanvasRenderingContext2D, x: number, y: number, frame: number) {
  // Pot
  ctx.fillStyle = "#c2410c"
  ctx.fillRect(x, y + 10, 14, 14)
  ctx.fillStyle = "#ea580c"
  ctx.fillRect(x - 1, y + 9, 16, 3)

  // Soil
  ctx.fillStyle = "#451a03"
  ctx.fillRect(x + 2, y + 9, 10, 3)

  // Leaves
  const sway = Math.sin(frame * 0.03) * 1.5
  ctx.fillStyle = "#16a34a"
  ctx.fillRect(x + 5 + sway, y, 4, 10)
  ctx.fillRect(x + 2 + sway, y + 2, 4, 6)
  ctx.fillRect(x + 8 + sway, y + 1, 4, 7)

  // Leaf highlights
  ctx.fillStyle = "#22c55e"
  ctx.fillRect(x + 6 + sway, y + 1, 2, 4)
  ctx.fillRect(x + 3 + sway, y + 3, 2, 3)
}

function drawBookshelf(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number) {
  // Shelf frame
  ctx.fillStyle = "#78350f"
  ctx.fillRect(x, y, w, h)
  ctx.fillStyle = "#92400e"
  ctx.fillRect(x + 1, y + 1, w - 2, h - 2)

  // Shelves
  ctx.fillStyle = "#78350f"
  ctx.fillRect(x + 1, y + h * 0.33, w - 2, 2)
  ctx.fillRect(x + 1, y + h * 0.66, w - 2, 2)

  // Books
  const bookColors = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#8b5cf6", "#ec4899"]
  const shelfY = [y + 3, y + h * 0.33 + 3, y + h * 0.66 + 3]
  for (const sy of shelfY) {
    let bx = x + 3
    for (let i = 0; i < 4; i++) {
      const bw = 3 + Math.random() * 2
      const bh = h * 0.28
      ctx.fillStyle = bookColors[(i + shelfY.indexOf(sy)) % bookColors.length]
      ctx.fillRect(bx, sy, bw, bh)
      bx += bw + 1
    }
  }
}
