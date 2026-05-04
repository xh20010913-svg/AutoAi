import { useState, useEffect, useCallback, type CSSProperties } from "react"
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
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { GripVertical } from "lucide-react"
import { cn } from "@/lib/utils"
import { api, type Task, type TaskStatus } from "@/lib/api"
import { CreateTaskDialog } from "@/components/CreateTaskDialog"
import { TaskDetailPanel } from "@/components/TaskDetailPanel"

interface ColumnDef {
  id: TaskStatus
  title: string
  color: string
}

const COLUMNS: ColumnDef[] = [
  { id: "todo", title: "Todo", color: "bg-zinc-400" },
  { id: "in_progress", title: "In Progress", color: "bg-blue-500" },
  { id: "in_review", title: "In Review", color: "bg-amber-500" },
  { id: "done", title: "Done", color: "bg-emerald-500" },
  { id: "blocked", title: "Blocked", color: "bg-red-500" },
]

const priorityColors: Record<string, string> = {
  high: "bg-red-500/15 text-red-400 border-red-500/20",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/20",
  low: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  none: "bg-zinc-500/15 text-zinc-400 border-zinc-500/20",
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
      className="group rounded-lg border border-border bg-card p-3 transition-colors hover:border-primary/40"
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
            "rounded-md border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider",
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
    <div className="flex w-72 flex-col rounded-lg border border-border bg-muted/30">
      <div className="flex items-center gap-2 p-3 border-b border-border">
        <div className={cn("h-2.5 w-2.5 rounded-full", column.color)} />
        <h3 className="text-sm font-medium">{column.title}</h3>
        <span className="ml-auto rounded-md bg-muted px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground">
          {tasks.length}
        </span>
      </div>
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

function TaskCardOverlay({ task }: { task: Task }) {
  return (
    <div className="rounded-lg border border-primary bg-card p-3 shadow-lg w-64">
      <h4 className="text-sm font-medium text-card-foreground">{task.title}</h4>
      {task.description && (
        <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
          {task.description}
        </p>
      )}
      <div className="mt-3">
        <span
          className={cn(
            "rounded-md border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider",
            priorityColors[task.priority] ?? priorityColors.none,
          )}
        >
          {task.priority}
        </span>
      </div>
    </div>
  )
}

export function BoardPage() {
  const [projectId, setProjectId] = useState<string | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [activeId, setActiveId] = useState<string | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  )

  const loadProject = useCallback(async () => {
    try {
      const { projects } = await api.projects.list()
      if (projects.length === 0) {
        setError("No projects found. Create a project first.")
        return null
      }
      return projects[0].id
    } catch (err) {
      setError(`Failed to load projects: ${err instanceof Error ? err.message : "Unknown error"}`)
      return null
    }
  }, [])

  const loadTasks = useCallback(async (pid: string) => {
    try {
      const { tasks: data } = await api.tasks.list(pid)
      setTasks(data)
    } catch (err) {
      setError(`Failed to load tasks: ${err instanceof Error ? err.message : "Unknown error"}`)
    }
  }, [])

  useEffect(() => {
    async function init() {
      setLoading(true)
      const pid = await loadProject()
      if (pid) {
        setProjectId(pid)
        await loadTasks(pid)
      }
      setLoading(false)
    }
    init()
  }, [loadProject, loadTasks])

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

    // Check if we're hovering over a column directly
    const overIsColumn = COLUMNS.some((c) => c.id === overId)
    const activeTask = tasks.find((t) => t.id === activeId)
    if (!activeTask) return

    let targetStatus: TaskStatus | null = null
    if (overIsColumn) {
      targetStatus = overId as TaskStatus
    } else {
      // Hovering over another task — check its column
      const overTask = tasks.find((t) => t.id === overId)
      if (overTask && overTask.status !== activeTask.status) {
        targetStatus = overTask.status
      }
    }

    if (targetStatus && targetStatus !== activeTask.status) {
      // Optimistic update: move task to new column
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

    if (!over || !projectId) return

    const activeId = active.id as string
    const overId = over.id as string

    const activeTask = tasks.find((t) => t.id === activeId)
    if (!activeTask) return

    // Determine target column
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

    // Check if anything changed
    const statusChanged = activeTask.status !== targetStatus
    const positionChanged =
      targetPosition !== undefined && activeTask.position !== targetPosition

    if (!statusChanged && !positionChanged) return

    try {
      const updated = await api.tasks.update(projectId, activeId, {
        status: statusChanged ? targetStatus : undefined,
        position: targetPosition,
      })
      setTasks((prev) =>
        prev.map((t) => (t.id === activeId ? updated : t)),
      )
      // Update selected task if it's the one we moved
      if (selectedTask?.id === activeId) {
        setSelectedTask(updated)
      }
    } catch (err) {
      console.error("Failed to update task position:", err)
      // Reload to revert optimistic update
      await loadTasks(projectId)
    }
  }

  function handleTaskCreated(task: Task) {
    setTasks((prev) => [...prev, task])
  }

  function handleTaskUpdated(task: Task) {
    setTasks((prev) => prev.map((t) => (t.id === task.id ? task : t)))
    setSelectedTask(task)
  }

  function handleTaskDeleted(taskId: string) {
    setTasks((prev) => prev.filter((t) => t.id !== taskId))
    setSelectedTask(null)
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading board...</p>
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
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold">Board</h1>
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

      {selectedTask && projectId && (
        <TaskDetailPanel
          task={selectedTask}
          projectId={projectId}
          onClose={() => setSelectedTask(null)}
          onUpdated={handleTaskUpdated}
          onDeleted={handleTaskDeleted}
        />
      )}
    </div>
  )
}
