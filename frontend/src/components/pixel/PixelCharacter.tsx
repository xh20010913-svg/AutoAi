import { useState, useEffect } from "react"

const PX = 5 // pixel size in px

// Color presets for different agent roles
const COLOR_PRESETS = {
  blue:   { hair: "#6366f1", shirt: "#3b82f6", pants: "#475569" },
  green:  { hair: "#10b981", shirt: "#22c55e", pants: "#475569" },
  purple: { hair: "#a855f7", shirt: "#8b5cf6", pants: "#475569" },
  amber:  { hair: "#f59e0b", shirt: "#eab308", pants: "#475569" },
  pink:   { hair: "#ec4899", shirt: "#f472b6", pants: "#475569" },
  cyan:   { hair: "#06b6d4", shirt: "#0ea5e9", pants: "#475569" },
  red:    { hair: "#ef4444", shirt: "#f87171", pants: "#475569" },
  teal:   { hair: "#14b8a6", shirt: "#2dd4bf", pants: "#475569" },
} as const

export type ColorPreset = keyof typeof COLOR_PRESETS

type Status = "running" | "idle" | "error"

interface PixelCharacterProps {
  colorPreset?: ColorPreset
  status: Status
}

// Pixel character frames - 8 columns x 10 rows
// 0 = transparent, 1 = hair, 2 = skin, 3 = shirt, 4 = pants

const SITTING_FRAME: number[][] = [
  [0, 0, 1, 1, 1, 1, 0, 0],
  [0, 1, 2, 2, 2, 2, 1, 0],
  [0, 1, 2, 2, 2, 2, 1, 0],
  [0, 0, 2, 2, 2, 2, 0, 0],
  [0, 3, 3, 3, 3, 3, 3, 0],
  [3, 3, 3, 3, 3, 3, 3, 3],
  [0, 3, 3, 3, 3, 3, 3, 0],
  [0, 0, 4, 4, 0, 4, 4, 0],
  [0, 0, 4, 4, 0, 4, 4, 0],
  [0, 0, 2, 2, 0, 2, 2, 0],
]

// Arms up (reaching toward keyboard)
const ARMS_UP: number[][] = [
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 2, 2, 2, 2, 0, 0],
  [0, 3, 3, 3, 3, 3, 3, 0],
  [3, 2, 3, 3, 3, 3, 2, 3],
  [0, 0, 3, 3, 3, 3, 0, 0],
  [0, 0, 4, 4, 0, 4, 4, 0],
  [0, 0, 4, 4, 0, 4, 4, 0],
  [0, 0, 2, 2, 0, 2, 2, 0],
]

// Arms down (resting)
const ARMS_DOWN: number[][] = [
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 2, 2, 2, 2, 0, 0],
  [0, 3, 3, 3, 3, 3, 3, 0],
  [3, 3, 3, 3, 3, 3, 3, 3],
  [0, 3, 3, 3, 3, 3, 3, 0],
  [2, 0, 4, 4, 0, 4, 4, 2],
  [0, 0, 4, 4, 0, 4, 4, 0],
  [0, 0, 2, 2, 0, 2, 2, 0],
]

function getPixelColor(
  value: number,
  colors: { hair: string; shirt: string; pants: string; skin: string },
): string | null {
  switch (value) {
    case 1: return colors.hair
    case 2: return colors.skin
    case 3: return colors.shirt
    case 4: return colors.pants
    default: return null
  }
}

function PixelGrid({
  frame,
  colors,
  style,
  className,
}: {
  frame: number[][]
  colors: { hair: string; shirt: string; pants: string; skin: string }
  style?: React.CSSProperties
  className?: string
}) {
  return (
    <div
      className={className}
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(${frame[0].length}, ${PX}px)`,
        gridTemplateRows: `repeat(${frame.length}, ${PX}px)`,
        ...style,
      }}
    >
      {frame.flat().map((v, i) => {
        const color = getPixelColor(v, colors)
        return color ? (
          <div key={i} style={{ backgroundColor: color }} />
        ) : (
          <div key={i} />
        )
      })}
    </div>
  )
}

// Desk scene: desk + monitor + keyboard + character
function DeskScene({
  colors,
  armFrame,
}: {
  colors: { hair: string; shirt: string; pants: string; skin: string }
  armFrame: number[][]
}) {
  return (
    <div className="relative mx-auto" style={{ width: 130, height: 100 }}>
      {/* Desk */}
      <div
        className="absolute"
        style={{
          bottom: 8,
          left: 10,
          width: 110,
          height: 4,
          backgroundColor: "#92400e",
        }}
      />
      {/* Desk legs */}
      <div
        className="absolute"
        style={{
          bottom: 8,
          left: 12,
          width: 4,
          height: 28,
          backgroundColor: "#78350f",
        }}
      />
      <div
        className="absolute"
        style={{
          bottom: 8,
          right: 12,
          width: 4,
          height: 28,
          backgroundColor: "#78350f",
        }}
      />

      {/* Monitor */}
      <div
        className="absolute"
        style={{
          bottom: 12,
          left: 28,
          width: 44,
          height: 32,
          backgroundColor: "#374151",
          borderRadius: 2,
        }}
      >
        {/* Screen */}
        <div
          style={{
            position: "absolute",
            top: 3,
            left: 3,
            right: 3,
            bottom: 8,
            backgroundColor: "#3b82f6",
            animation: "pixelMonitorGlow 2s ease-in-out infinite",
          }}
        />
        {/* Stand */}
        <div
          style={{
            position: "absolute",
            bottom: -6,
            left: "50%",
            transform: "translateX(-50%)",
            width: 12,
            height: 6,
            backgroundColor: "#374151",
          }}
        />
      </div>

      {/* Keyboard */}
      <div
        className="absolute"
        style={{
          bottom: 12,
          left: 34,
          width: 32,
          height: 6,
          backgroundColor: "#6b7280",
          borderRadius: 1,
        }}
      />

      {/* Character sitting at desk */}
      <div className="absolute" style={{ bottom: 16, left: 18 }}>
        <PixelGrid
          frame={armFrame}
          colors={colors}
          className="animate-[pixelArmType_0.4s_ease-in-out_infinite]"
        />
      </div>
    </div>
  )
}

// Sofa scene: sofa + side table + character
function SofaScene({
  colors,
}: {
  colors: { hair: string; shirt: string; pants: string; skin: string }
}) {
  return (
    <div className="relative mx-auto" style={{ width: 130, height: 100 }}>
      {/* Sofa back */}
      <div
        className="absolute"
        style={{
          bottom: 8,
          left: 10,
          width: 72,
          height: 44,
          backgroundColor: "#7c3aed",
          borderRadius: "6px 6px 0 0",
        }}
      />
      {/* Sofa seat */}
      <div
        className="absolute"
        style={{
          bottom: 8,
          left: 10,
          width: 72,
          height: 16,
          backgroundColor: "#8b5cf6",
          borderRadius: "0 0 4px 4px",
        }}
      />
      {/* Left armrest */}
      <div
        className="absolute"
        style={{
          bottom: 8,
          left: 6,
          width: 10,
          height: 36,
          backgroundColor: "#7c3aed",
          borderRadius: "6px 0 0 4px",
        }}
      />
      {/* Right armrest */}
      <div
        className="absolute"
        style={{
          bottom: 8,
          right: 42,
          width: 10,
          height: 36,
          backgroundColor: "#7c3aed",
          borderRadius: "0 6px 4px 0",
        }}
      />

      {/* Side table */}
      <div
        className="absolute"
        style={{
          bottom: 8,
          right: 10,
          width: 28,
          height: 3,
          backgroundColor: "#92400e",
        }}
      />
      <div
        className="absolute"
        style={{
          bottom: 8,
          right: 22,
          width: 3,
          height: 24,
          backgroundColor: "#78350f",
        }}
      />
      {/* Cup on table */}
      <div
        className="absolute"
        style={{
          bottom: 11,
          right: 20,
          width: 8,
          height: 10,
          backgroundColor: "#f3f4f6",
          borderRadius: "0 0 2px 2px",
        }}
      />
      {/* Steam */}
      <div
        className="absolute"
        style={{
          bottom: 22,
          right: 22,
          width: 4,
          height: 6,
          backgroundColor: "rgba(255,255,255,0.3)",
          borderRadius: "50%",
        }}
      />

      {/* Character sitting on sofa */}
      <div
        className="absolute animate-[pixelIdleSway_2s_ease-in-out_infinite]"
        style={{ bottom: 24, left: 22 }}
      >
        <PixelGrid frame={SITTING_FRAME} colors={colors} />
      </div>
    </div>
  )
}

export function PixelCharacter({ colorPreset = "blue", status }: PixelCharacterProps) {
  const palette = COLOR_PRESETS[colorPreset]
  const colors = { ...palette, skin: "#fbbf24" }

  const [armUp, setArmUp] = useState(true)

  // Alternate arm frames for typing animation
  useEffect(() => {
    if (status !== "running") return
    const interval = setInterval(() => setArmUp((v) => !v), 400)
    return () => clearInterval(interval)
  }, [status])

  const containerClass =
    status === "error"
      ? "animate-[pixelError_0.6s_ease-in-out_infinite]"
      : ""

  return (
    <div
      className={`mt-3 flex items-center justify-center rounded-md bg-muted/50 p-2 ${containerClass}`}
      style={{ minHeight: 100 }}
    >
      {status === "idle" ? (
        <SofaScene colors={colors} />
      ) : (
        <DeskScene colors={colors} armFrame={armUp ? ARMS_UP : ARMS_DOWN} />
      )}
    </div>
  )
}
