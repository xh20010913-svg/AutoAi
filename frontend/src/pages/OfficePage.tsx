import { PixelOffice } from "@/components/pixel/office"

const AGENTS = [
  { name: "PM", palette: "blue" as const, state: "working" as const },
  { name: "BE-1", palette: "green" as const, state: "working" as const },
  { name: "BE-2", palette: "purple" as const, state: "idle" as const },
  { name: "BE-3", palette: "amber" as const, state: "error" as const },
  { name: "FE", palette: "pink" as const, state: "working" as const },
  { name: "QA-1", palette: "cyan" as const, state: "idle" as const },
  { name: "QA-2", palette: "red" as const, state: "working" as const },
  { name: "QA-3", palette: "teal" as const, state: "idle" as const },
]

export function OfficePage() {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold">Pixel Office</h1>
        <div className="flex items-center gap-3 text-sm text-muted-foreground font-mono">
          <span>{AGENTS.length} agents</span>
          <span>|</span>
          <span>{AGENTS.filter(a => a.state === "working").length} working</span>
          <span>{AGENTS.filter(a => a.state === "idle").length} idle</span>
          <span>{AGENTS.filter(a => a.state === "error").length} error</span>
        </div>
      </div>
      <div className="flex-1 flex items-start justify-center">
        <PixelOffice agents={AGENTS} />
      </div>
    </div>
  )
}
