import {
  COLOR_PRESETS,
  type ColorPreset,
  drawPixelGrid,
  SITTING_KEYBOARD_FRAME,
  SITTING_ARMS_UP_FRAME,
  SITTING_SOFA_FRAME,
  WALK_LEFT_FRAME,
  WALK_RIGHT_FRAME,
  PX,
  CHAR_COLS,
  CHAR_ROWS,
} from "./animations"

export type CharacterState = "idle" | "walking_to_desk" | "working" | "walking_to_sofa" | "alert"

export interface PixelCharAgent {
  id: string
  name: string
  role: string
  status: "idle" | "running" | "error"
  colorPreset: ColorPreset
}

export interface CharacterInstance {
  agent: PixelCharAgent
  state: CharacterState
  x: number
  y: number
  targetX: number
  targetY: number
  walkFrame: number
  armFrame: number
  swayPhase: number
  alertTimer: number
  colors: Record<string, string>
}

export function createCharacter(agent: PixelCharAgent, deskX: number, deskY: number, sofaX: number, sofaY: number): CharacterInstance {
  const palette = COLOR_PRESETS[agent.colorPreset]
  const isIdle = agent.status === "idle"
  return {
    agent,
    state: isIdle ? "idle" : "working",
    x: isIdle ? sofaX : deskX,
    y: isIdle ? sofaY : deskY,
    targetX: isIdle ? sofaX : deskX,
    targetY: isIdle ? sofaY : deskY,
    walkFrame: 0,
    armFrame: 0,
    swayPhase: Math.random() * Math.PI * 2,
    alertTimer: 0,
    colors: { ...palette },
  }
}

export function updateCharacter(char: CharacterInstance, _dt: number, deskX: number, deskY: number, sofaX: number, sofaY: number) {
  const walkSpeed = 1.8 // pixels per frame at 60fps

  // Check if status changed
  const wantsWorking = char.agent.status === "running" || char.agent.status === "error"
  const wantsIdle = char.agent.status === "idle"

  // State transitions
  if (char.state === "idle" && wantsWorking) {
    char.state = "walking_to_desk"
    char.targetX = deskX
    char.targetY = deskY
  } else if (char.state === "working" && wantsIdle) {
    char.state = "walking_to_sofa"
    char.targetX = sofaX
    char.targetY = sofaY
  } else if (char.state === "working" && char.agent.status === "error" && char.alertTimer <= 0) {
    char.alertTimer = 120 // frames of alert
  }

  // Walking
  if (char.state === "walking_to_desk" || char.state === "walking_to_sofa") {
    const dx = char.targetX - char.x
    const dy = char.targetY - char.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist > walkSpeed) {
      char.x += (dx / dist) * walkSpeed
      char.y += (dy / dist) * walkSpeed
      char.walkFrame += 1
    } else {
      char.x = char.targetX
      char.y = char.targetY
      char.state = char.state === "walking_to_desk" ? "working" : "idle"
      char.walkFrame = 0
    }
  }

  // Typing arm animation
  if (char.state === "working") {
    char.armFrame += 1
  }

  // Sway phase for idle
  char.swayPhase += 0.03

  // Alert countdown
  if (char.alertTimer > 0) char.alertTimer -= 1
}

export function drawCharacter(ctx: CanvasRenderingContext2D, char: CharacterInstance) {
  const scale = PX
  const w = CHAR_COLS * scale
  const h = CHAR_ROWS * scale

  ctx.save()

  if (char.state === "idle") {
    // Sway on sofa
    const sway = Math.sin(char.swayPhase) * 2
    ctx.translate(char.x + sway, char.y)
    drawPixelGrid(ctx, SITTING_SOFA_FRAME, 0, 0, char.colors, scale)
  } else if (char.state === "working") {
    // Typing animation
    const typing = char.armFrame % 20 < 10
    const frame = typing ? SITTING_ARMS_UP_FRAME : SITTING_KEYBOARD_FRAME
    ctx.translate(char.x, char.y)
    drawPixelGrid(ctx, frame, 0, 0, char.colors, scale)

    // Monitor glow effect
    ctx.fillStyle = char.agent.status === "error" ? "#ef4444" : "#3b82f6"
    const glowAlpha = 0.3 + Math.sin(char.armFrame * 0.1) * 0.2
    ctx.globalAlpha = glowAlpha
    ctx.fillRect(CHAR_COLS * scale + 4, -h * 0.3, scale * 6, scale * 4)
    ctx.globalAlpha = 1
  } else if (char.state === "walking_to_desk" || char.state === "walking_to_sofa") {
    const walkFrame = char.walkFrame % 20 < 10 ? WALK_LEFT_FRAME : WALK_RIGHT_FRAME
    ctx.translate(char.x, char.y)
    // Face the right direction
    const goingRight = char.targetX > char.x
    if (!goingRight) {
      ctx.translate(w, 0)
      ctx.scale(-1, 1)
    }
    drawPixelGrid(ctx, walkFrame, 0, 0, char.colors, scale)
  }

  ctx.restore()

  // Alert bubble
  if (char.alertTimer > 0) {
    const bubbleAlpha = char.alertTimer > 20 ? 1 : char.alertTimer / 20
    ctx.save()
    ctx.globalAlpha = bubbleAlpha
    // Background circle
    ctx.fillStyle = "#ef4444"
    ctx.beginPath()
    ctx.arc(char.x + w / 2, char.y - 10, 8, 0, Math.PI * 2)
    ctx.fill()
    // Exclamation mark
    ctx.fillStyle = "#fff"
    ctx.fillRect(char.x + w / 2 - 1, char.y - 15, 2, 6)
    ctx.fillRect(char.x + w / 2 - 1, char.y - 7, 2, 2)
    ctx.restore()
  }

  // Name tag
  ctx.save()
  ctx.fillStyle = "rgba(0,0,0,0.6)"
  const nameWidth = ctx.measureText(char.agent.name).width
  const tagX = char.x + w / 2 - nameWidth / 2 - 4
  const tagY = char.y + h + 2
  ctx.fillRect(tagX, tagY, nameWidth + 8, 14)
  ctx.fillStyle = "#fff"
  ctx.font = "9px monospace"
  ctx.textAlign = "center"
  ctx.fillText(char.agent.name, char.x + w / 2, tagY + 11)
  ctx.restore()
}
