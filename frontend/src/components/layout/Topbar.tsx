import { Play } from "lucide-react";

export default function Topbar() {
  return (
    <header className="flex h-12 items-center justify-between border-b border-border bg-card px-6">
      <h1 className="text-sm font-semibold tracking-tight">AutoAI</h1>
      <button className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90">
        <Play className="size-3.5" fill="currentColor" />
        Run
      </button>
    </header>
  );
}
