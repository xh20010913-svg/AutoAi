import { useState, useEffect, useCallback, useRef, type CSSProperties } from "react"
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
import { api, type Task, type TaskStatus, type GraphEdge } from "@/lib/api"
import { CreateTaskDialog } from "@/components/CreateTaskDialog"
import { TaskDetailPanel } from "@/components/TaskDetailPanel"

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
      data-task-id={task.id}
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
        {task.assignee && (
          <span className="text-xs text-muted-foreground truncate max-w-[100px]">
            {task.assignee}
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
    <div className="flex w-72 flex-col bg-muted/20 pixel-border">
      <div className="flex items-center gap-2 p-3 border-b-2 border-border">
        <div className={cn("h-2.5 w-2.5", column.color)} />
        <h3 className="text-sm font-medium">{column.title}</h3>
        <span className="ml-auto bg-muted px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground font-mono border border-border">
          {tasks.length}
        </span>
      </div>
      <SortableContext
        items={tasks.map((t) => t.id)}
        strategy={verticalListSortingStrategy}
      >
        <div
          ref={setNodeRef}
          data-column-id={column.id}
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

function DependencyArrows({
  edges,
  tasks,
}: {
  edges: GraphEdge[]
  tasks: Task[]
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [, forceUpdate] = useState(0)

  useEffect(() => {
    const handle = setInterval(() => forceUpdate((n) => n + 1), 500)
    return () => clearInterval(handle)
  }, [])

  const arrows: { x1: number; y1: number; x2: number; y2: number; source: string; target: string }[] = []

  if (!containerRef.current) {
    return (
      <div ref={containerRef} className="absolute inset-0 pointer-events-none overflow-hidden">
        <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 5 }} />
      </div>
    )
  }

  const containerRect = containerRef.current.getBoundingClientRect()

  for (const edge of edges) {
    const sourceEl = document.querySelector(`[data-task-id="${edge.source}"]`) as HTMLElement | null
    const targetEl = document.querySelector(`[data-task-id="${edge.target}"]`) as HTMLElement | null
    if (!sourceEl || !targetEl) continue

    const sourceRect = sourceEl.getBoundingClientRect()
    const targetRect = targetEl.getBoundingClientRect()

    arrows.push({
      x1: sourceRect.right - containerRect.left,
      y1: sourceRect.top + sourceRect.height / 2 - containerRect.top,
      x2: targetRect.left - containerRect.left,
      y2: targetRect.top + targetRect.height / 2 - containerRect.top,
      source: edge.source,
      target: edge.target,
    })
  }

  return (
    <div ref={containerRef} className="absolute inset-0 pointer-events-none overflow-hidden">
      <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 5 }}>
        <defs>
          <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#a1a1aa" />
          </marker>
        </defs>
        {arrows.map((a) => (
          <line
            key={`${a.source}-${a.target}`}
            x1={a.x1}
            y1={a.y1}
            x2={a.x2 - 4}
            y2={a.y2}
            stroke="#a1a1aa"
            strokeWidth={1.5}
            strokeDasharray="5,3"
            markerEnd="url(#arrowhead)"
          />
        ))}
      </svg>
    </div>
  )
}

export function BoardPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [edges, setEdges] = useState<GraphEdge[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [activeId, setActiveId] = useState<string | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  )

  const loadData = useCallback(async () => {
    try {
      const [taskList, graph] = await Promise.all([
        api.tasks.list(),
        api.tasks.dependencyGraph(),
      ])
      setTasks(taskList)
      setEdges(graph.edges)
    } catch (err) {
      setError(`Failed to load: ${err instanceof Error ? err.message : "Unknown error"}`)
    }
  }, [])

  useEffect(() => {
    async function init() {
      setLoading(true)
      await loadData()
      setLoading(false)
    }
    init()
  }, [loadData])

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
      const updated = await api.tasks.updateStatus(activeId, targetStatus, targetPosition)
      setTasks((prev) =>
        prev.map((t) => (t.id === activeId ? updated : t)),
      )
      if (selectedTask?.id === activeId) {
        setSelectedTask(updated)
      }
    } catch (err) {
      console.error("Failed to update task:", err)
      await loadData()
    }
  }

  function handleTaskCreated(task: Task) {
    setTasks((prev) => [...prev, task])
  }

  function handleTaskUpdated(task: Task) {
    setTasks((prev) => prev.map((t) => (t.id === task.id ? task : t)))
    setSelectedTask(task)
    // Refresh graph edges too
    api.tasks.dependencyGraph().then((g) => setEdges(g.edges))
  }

  function handleTaskDeleted(taskId: string) {
    setTasks((prev) => prev.filter((t) => t.id !== taskId))
    setSelectedTask(null)
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
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold">Board</h1>
        <CreateTaskDialog onCreated={handleTaskCreated} />
      </div>
      <div className="flex-1 overflow-x-auto relative">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          <div className="flex gap-4 pb-4 relative" style={{ minWidth: "max-content" }}>
            {COLUMNS.map((col) => (
              <DroppableColumn
                key={col.id}
                column={col}
                tasks={getColumnTasks(col.id)}
                onTaskClick={setSelectedTask}
              />
            ))}
            <DependencyArrows edges={edges} tasks={tasks} />
          </div>
          <DragOverlay>
            {activeTask ? <TaskCardOverlay task={activeTask} /> : null}
          </DragOverlay>
        </DndContext>
      </div>

      {selectedTask && (
        <TaskDetailPanel
          task={selectedTask}
          allTasks={tasks}
          onClose={() => setSelectedTask(null)}
          onUpdated={handleTaskUpdated}
          onDeleted={handleTaskDeleted}
        />
      )}
    </div>
  )
}
