import { LayoutDashboard } from "lucide-react";

export default function Board() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center h-full text-center">
      <LayoutDashboard className="size-12 text-muted-foreground mb-4" />
      <h2 className="text-xl font-semibold tracking-tight">Board</h2>
      <p className="mt-2 text-sm text-muted-foreground max-w-md">
        Kanban board for managing tasks across Backlog, Todo, In Progress, In
        Review, Done, and Blocked columns. Drag and drop to update task status.
      </p>
    </div>
  );
}
