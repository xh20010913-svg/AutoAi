import { Play } from "lucide-react";

export default function Runtime() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center h-full text-center">
      <Play className="size-12 text-muted-foreground mb-4" />
      <h2 className="text-xl font-semibold tracking-tight">Runtime</h2>
      <p className="mt-2 text-sm text-muted-foreground max-w-md">
        Monitor active agent sessions, view real-time execution logs, track
        progress, and manage the harness lifecycle for long-running tasks.
      </p>
    </div>
  );
}
