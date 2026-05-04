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
import { api, type Task, type TaskStatus } from "@/lib/api"
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

    if (!over || !projectId) return

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
      const updated = await api.tasks.update(projectId, activeId, {
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
