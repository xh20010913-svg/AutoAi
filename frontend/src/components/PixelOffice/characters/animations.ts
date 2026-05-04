// Animation constants and frame definitions for pixel characters

export const PX = 3 // base pixel size for scene-scale characters

export const CHAR_COLS = 10
export const CHAR_ROWS = 12

// Pixel grid values: 0=transparent, 1=hair, 2=skin, 3=shirt, 4=pants, 5=shoe, 6=chair/sofa
export const V = { EMPTY: 0, HAIR: 1, SKIN: 2, SHIRT: 3, PANTS: 4, SHOE: 5 }

// Standing facing front
export const STANDING_FRAME: number[][] = [
  [0,0,0,1,1,1,1,0,0,0],
  [0,0,1,2,2,2,2,1,0,0],
  [0,0,2,2,2,2,2,2,0,0],
  [0,0,0,2,2,2,2,0,0,0],
  [0,0,3,3,3,3,3,3,0,0],
  [0,3,3,3,3,3,3,3,3,0],
  [0,2,3,3,3,3,3,3,2,0],
  [0,0,3,3,3,3,3,3,0,0],
  [0,0,0,4,4,4,4,0,0,0],
  [0,0,0,4,4,4,4,0,0,0],
  [0,0,0,4,4,4,4,0,0,0],
  [0,0,5,5,0,0,5,5,0,0],
]

// Sitting at desk (arms on keyboard)
export const SITTING_KEYBOARD_FRAME: number[][] = [
  [0,0,0,1,1,1,1,0,0,0],
  [0,0,1,2,2,2,2,1,0,0],
  [0,0,2,2,2,2,2,2,0,0],
  [0,0,0,2,2,2,2,0,0,0],
  [0,0,3,3,3,3,3,3,0,0],
  [0,2,3,3,3,3,3,3,2,0],
  [0,0,3,3,3,3,3,3,0,0],
  [0,0,0,4,4,4,4,0,0,0],
  [0,0,0,4,0,0,4,0,0,0],
  [0,0,0,4,0,0,4,0,0,0],
  [0,0,2,2,0,0,2,2,0,0],
  [0,0,0,0,0,0,0,0,0,0],
]

// Arms raised (typing animation frame)
export const SITTING_ARMS_UP_FRAME: number[][] = [
  [0,0,0,1,1,1,1,0,0,0],
  [0,0,1,2,2,2,2,1,0,0],
  [0,0,2,2,2,2,2,2,0,0],
  [0,0,0,2,2,2,2,0,0,0],
  [0,2,3,3,3,3,3,3,2,0],
  [0,0,3,3,3,3,3,3,0,0],
  [0,0,3,3,3,3,3,3,0,0],
  [0,0,0,4,4,4,4,0,0,0],
  [0,0,0,4,0,0,4,0,0,0],
  [0,0,0,4,0,0,4,0,0,0],
  [0,0,2,2,0,0,2,2,0,0],
  [0,0,0,0,0,0,0,0,0,0],
]

// Walking frames (legs alternate)
export const WALK_LEFT_FRAME: number[][] = [
  [0,0,0,1,1,1,1,0,0,0],
  [0,0,1,2,2,2,2,1,0,0],
  [0,0,2,2,2,2,2,2,0,0],
  [0,0,0,2,2,2,2,0,0,0],
  [0,0,3,3,3,3,3,3,0,0],
  [0,3,3,3,3,3,3,3,3,0],
  [0,2,3,3,3,3,3,3,2,0],
  [0,0,3,3,3,3,3,3,0,0],
  [0,0,0,4,4,4,4,0,0,0],
  [0,0,4,4,0,4,4,0,0,0],
  [0,0,4,0,0,0,4,4,0,0],
  [0,0,5,0,0,0,0,5,0,0],
]

export const WALK_RIGHT_FRAME: number[][] = [
  [0,0,0,1,1,1,1,0,0,0],
  [0,0,1,2,2,2,2,1,0,0],
  [0,0,2,2,2,2,2,2,0,0],
  [0,0,0,2,2,2,2,0,0,0],
  [0,0,3,3,3,3,3,3,0,0],
  [0,3,3,3,3,3,3,3,3,0],
  [0,2,3,3,3,3,3,3,2,0],
  [0,0,3,3,3,3,3,3,0,0],
  [0,0,0,4,4,4,4,0,0,0],
  [0,0,0,4,4,0,4,4,0,0],
  [0,0,4,4,0,0,0,4,0,0],
  [0,0,5,0,0,0,0,5,0,0],
]

// Sitting on sofa (relaxed)
export const SITTING_SOFA_FRAME: number[][] = [
  [0,0,0,1,1,1,1,0,0,0],
  [0,0,1,2,2,2,2,1,0,0],
  [0,0,2,2,2,2,2,2,0,0],
  [0,0,0,2,2,2,2,0,0,0],
  [0,0,3,3,3,3,3,3,0,0],
  [0,0,3,3,3,3,3,3,0,0],
  [0,2,3,3,3,3,3,3,2,0],
  [0,0,0,4,4,4,4,0,0,0],
  [0,0,0,4,0,0,4,0,0,0],
  [0,0,0,4,0,0,4,0,0,0],
  [0,0,2,2,0,0,2,2,0,0],
  [0,0,0,0,0,0,0,0,0,0],
]

// Alert frame (exclamation mark over head — we draw this separately)
export const ALERT_FRAME = SITTING_KEYBOARD_FRAME

// Color presets matching role
export const COLOR_PRESETS = {
  blue:   { hair: "#6366f1", shirt: "#3b82f6", pants: "#475569", skin: "#fbbf24", shoe: "#1e293b" },
  green:  { hair: "#10b981", shirt: "#22c55e", pants: "#475569", skin: "#fbbf24", shoe: "#1e293b" },
  purple: { hair: "#a855f7", shirt: "#8b5cf6", pants: "#475569", skin: "#fbbf24", shoe: "#1e293b" },
  amber:  { hair: "#f59e0b", shirt: "#eab308", pants: "#475569", skin: "#fbbf24", shoe: "#1e293b" },
  pink:   { hair: "#ec4899", shirt: "#f472b6", pants: "#475569", skin: "#fbbf24", shoe: "#1e293b" },
  cyan:   { hair: "#06b6d4", shirt: "#0ea5e9", pants: "#475569", skin: "#fbbf24", shoe: "#1e293b" },
  red:    { hair: "#ef4444", shirt: "#f87171", pants: "#475569", skin: "#fbbf24", shoe: "#1e293b" },
  teal:   { hair: "#14b8a6", shirt: "#2dd4bf", pants: "#475569", skin: "#fbbf24", shoe: "#1e293b" },
} as const

export type ColorPreset = keyof typeof COLOR_PRESETS

export function pixelColor(val: number, colors: Record<string, string>): string | null {
  switch (val) {
    case V.HAIR: return colors.hair
    case V.SKIN: return colors.skin
    case V.SHIRT: return colors.shirt
    case V.PANTS: return colors.pants
    case V.SHOE: return colors.shoe
    default: return null
  }
}

/** Draw a pixel grid at (x, y) on a CanvasRenderingContext2D */
export function drawPixelGrid(
  ctx: CanvasRenderingContext2D,
  frame: number[][],
  x: number,
  y: number,
  colors: Record<string, string>,
  scale: number = PX,
) {
  for (let row = 0; row < frame.length; row++) {
    for (let col = 0; col < frame[row].length; col++) {
      const c = pixelColor(frame[row][col], colors)
      if (c) {
        ctx.fillStyle = c
        ctx.fillRect(x + col * scale, y + row * scale, scale, scale)
      }
    }
  }
}
