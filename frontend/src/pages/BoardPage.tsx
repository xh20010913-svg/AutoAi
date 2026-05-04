import { useState, useEffect, useCallback } from "react"
import {
  DndContext,
  DragOverlay,
  useSensor,
  useSensors,
  PointerSensor,
  useDroppable,
  closestCorners,
  type DragStartEvent,
  type DragEndEvent,
  type DragOverEvent,
} from "@dnd-kit/core"
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable"
import { cn } from "@/lib/utils"
import { taskApi, type Task, type TaskStatus } from "@/lib/api"
import { showToast } from "@/lib/toast"
import { connectWebSocket } from "@/lib/ws"
import { CreateTaskDialog } from "@/components/CreateTaskDialog"
import { TaskDetailPanel } from "@/components/TaskDetailPanel"
import { SortableTaskCard, TaskCardOverlay } from "@/components/TaskCard"

interface ColumnDef {
  id: TaskStatus
  title: string
  color: string
}

const COLUMNS: ColumnDef[] = [
  { id: "todo", title: "Todo", color: "bg-zinc-400" },
  { id: "in_progress", title: "In Progress", color: "bg-amber-500" },
  { id: "in_review", title: "In Review", color: "bg-orange-500" },
  { id: "done", title: "Done", color: "bg-emerald-500" },
  { id: "blocked", title: "Blocked", color: "bg-red-500" },
]

const priorityColors: Record<string, string> = {
  high: "bg-red-500/15 text-red-400 border-red-500/30",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  low: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  none: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
}

function SortableTaskCard({
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
      className="group bg-card p-3 transition-all hover:border-primary pixel-border-sm hover:pixel-glow relative"
    >
      {/* Pixel corner accents */}
      <div className="absolute top-0 left-0 w-[6px] h-[6px] border-t-2 border-l-2 border-primary/40 opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="absolute bottom-0 right-0 w-[6px] h-[6px] border-b-2 border-r-2 border-primary/40 opacity-0 group-hover:opacity-100 transition-opacity" />

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
          <span className="text-[10px] text-muted-foreground truncate max-w-[100px] font-mono">
            @{task.assignee_id.slice(0, 8)}
          </span>
        )}
      </div>
    </div>
  )
}

function DroppableColumn({
  column,
  tasks,
  onTaskClick,
}: {
  column: ColumnDef
  tasks: Task[]
  onTaskClick: (task: Task) => void
}) {
  const { setNodeRef } = useDroppable({ id: column.id })

  return (
    <div className="flex w-72 flex-col bg-muted/20 pixel-border relative group/col">
      <div className="flex items-center gap-2 p-3 border-b-2 border-border">
        <div className={cn("h-2.5 w-2.5", column.color)} />
        <h3 className="text-sm font-medium">{column.title}</h3>
        <span className="ml-auto bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground font-mono border border-border">
          {tasks.length}
        </span>
      </div>
      {/* Pixel divider under header */}
      <div className="h-[2px]" style={{
        background: "repeating-linear-gradient(90deg, var(--pixel-border) 0px, var(--pixel-border) 3px, transparent 3px, transparent 6px)",
        opacity: 0.3
      }} />
      <SortableContext
        items={tasks.map((t) => t.id)}
        strategy={verticalListSortingStrategy}
      >
        <div
          ref={setNodeRef}
          className="flex flex-col gap-2 p-2 flex-1 min-h-[80px]"
        >
          {tasks.map((task) => (
            <SortableTaskCard
              key={task.id}
              task={task}
              onClick={() => onTaskClick(task)}
            />
          ))}
        </div>
      </SortableContext>
    </div>
  )
}

export function BoardPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [activeId, setActiveId] = useState<string | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  )

  const loadTasks = useCallback(async () => {
    try {
      const data = await taskApi.list()
      setTasks(data)
      setError(null)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error"
      setError(`Failed to load tasks: ${msg}`)
      showToast(`Failed to load tasks: ${msg}`, "error")
    }
  }, [])

  // Initial load
  useEffect(() => {
    setLoading(true)
    loadTasks().finally(() => setLoading(false))
  }, [loadTasks])

  // WebSocket: refresh board on task change notifications
  useEffect(() => {
    const unsubscribe = connectWebSocket((data) => {
      if (data.type === "task_updated" || data.type === "task_created" || data.type === "task_deleted") {
        loadTasks()
      }
    })
    return unsubscribe
  }, [loadTasks])

  const getColumnTasks = (status: TaskStatus) =>
    tasks
      .filter((t) => t.status === status)
      .sort((a, b) => a.position - b.position)

  function handleDragStart(event: DragStartEvent) {
    setActiveId(event.active.id as string)
  }

  function handleDragOver(event: DragOverEvent) {
    const { active, over } = event
    if (!over) return

    const activeId = active.id as string
    const overId = over.id as string

    const overIsColumn = COLUMNS.some((c) => c.id === overId)
    const activeTask = tasks.find((t) => t.id === activeId)
    if (!activeTask) return

    let targetStatus: TaskStatus | null = null
    if (overIsColumn) {
      targetStatus = overId as TaskStatus
    } else {
      const overTask = tasks.find((t) => t.id === overId)
      if (overTask && overTask.status !== activeTask.status) {
        targetStatus = overTask.status
      }
    }

    if (targetStatus && targetStatus !== activeTask.status) {
      setTasks((prev) =>
        prev.map((t) =>
          t.id === activeId ? { ...t, status: targetStatus! } : t,
        ),
      )
    }
  }

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    setActiveId(null)

    if (!over) return

    const activeId = active.id as string
    const overId = over.id as string

    const activeTask = tasks.find((t) => t.id === activeId)
    if (!activeTask) return

    const overIsColumn = COLUMNS.some((c) => c.id === overId)
    let targetStatus: TaskStatus
    let targetPosition: number | undefined

    if (overIsColumn) {
      targetStatus = overId as TaskStatus
    } else {
      const overTask = tasks.find((t) => t.id === overId)
      if (!overTask) return
      targetStatus = overTask.status
      targetPosition = overTask.position
    }

    const statusChanged = activeTask.status !== targetStatus
    const positionChanged =
      targetPosition !== undefined && activeTask.position !== targetPosition

    if (!statusChanged && !positionChanged) return

    try {
      const updated = await taskApi.update(activeId, {
        status: statusChanged ? targetStatus : undefined,
        position: targetPosition,
      })
      setTasks((prev) =>
        prev.map((t) => (t.id === activeId ? updated : t)),
      )
      if (selectedTask?.id === activeId) {
        setSelectedTask(updated)
      }
    } catch (err) {
      console.error("Failed to update task position:", err)
      showToast("Failed to update task", "error")
      await loadTasks(projectId)
    }
  }

  function handleTaskCreated(task: Task) {
    setTasks((prev) => [...prev, task])
    showToast("Task created", "success")
  }

  function handleTaskUpdated(task: Task) {
    setTasks((prev) => prev.map((t) => (t.id === task.id ? task : t)))
    setSelectedTask(task)
  }

  function handleTaskDeleted(taskId: string) {
    setTasks((prev) => prev.filter((t) => t.id !== taskId))
    setSelectedTask(null)
    showToast("Task deleted", "success")
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground font-mono">Loading board...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-destructive">{error}</p>
      </div>
    )
  }

  const activeTask = activeId ? tasks.find((t) => t.id === activeId) : null

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold">Board</h1>
          <span className="text-[10px] font-mono text-muted-foreground/40 tracking-wider uppercase">// task board</span>
        </div>
        {projectId && (
          <CreateTaskDialog projectId={projectId} onCreated={handleTaskCreated} />
        )}
      </div>
      <div className="flex-1 overflow-x-auto">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          <div className="flex gap-4 pb-4" style={{ minWidth: "max-content" }}>
            {COLUMNS.map((col) => (
              <DroppableColumn
                key={col.id}
                column={col}
                tasks={getColumnTasks(col.id)}
                onTaskClick={setSelectedTask}
              />
            ))}
          </div>
          <DragOverlay>
            {activeTask ? <TaskCardOverlay task={activeTask} /> : null}
          </DragOverlay>
        </DndContext>
      </div>

      {selectedTask && (
        <TaskDetailPanel
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
          onUpdated={handleTaskUpdated}
          onDeleted={handleTaskDeleted}
        />
      )}
    </div>
  )
}
