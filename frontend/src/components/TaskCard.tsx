import { type CSSProperties } from "react"
import { useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { GripVertical } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Task } from "@/lib/api"

const priorityColors: Record<string, string> = {
  high: "bg-red-500/15 text-red-400 border-red-500/30",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  low: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  none: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
}

export function SortableTaskCard({
  task,
  onClick,
}: {
  task: Task
  onClick: () => void
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id })

  const style: CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="group bg-card p-3 transition-colors hover:border-primary pixel-border-sm"
    >
      <div className="flex items-start justify-between">
        <h4
          className="cursor-pointer text-sm font-medium text-card-foreground hover:text-primary"
          onClick={onClick}
        >
          {task.title}
        </h4>
        <button
          className="cursor-grab touch-none opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground"
          {...attributes}
          {...listeners}
        >
          <GripVertical className="h-4 w-4" />
        </button>
      </div>
      {task.description && (
        <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
          {task.description}
        </p>
      )}
      <div className="mt-3 flex items-center justify-between">
        <span
          className={cn(
            "border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider font-mono",
            priorityColors[task.priority] ?? priorityColors.none,
          )}
        >
          {task.priority}
        </span>
        {task.assignee_id && (
          <span className="text-xs text-muted-foreground truncate max-w-[100px]">
            {task.assignee_id}
          </span>
        )}
      </div>
    </div>
  )
}

export function TaskCardOverlay({ task }: { task: Task }) {
  return (
    <div className="bg-card p-3 shadow-lg w-64 pixel-border-accent">
      <h4 className="text-sm font-medium text-card-foreground">{task.title}</h4>
      {task.description && (
        <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
          {task.description}
        </p>
      )}
      <div className="mt-3">
        <span
          className={cn(
            "border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider font-mono",
            priorityColors[task.priority] ?? priorityColors.none,
          )}
        >
          {task.priority}
        </span>
      </div>
    </div>
  )
}
