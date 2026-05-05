import { useState, useEffect, type FormEvent } from "react"
import { X, Trash2, Link, Unlink } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { api, type Task, type TaskStatus, type TaskPriority } from "@/lib/api"
import { cn } from "@/lib/utils"

interface TaskDetailPanelProps {
  task: Task
  allTasks: Task[]
  onClose: () => void
  onUpdated: (task: Task) => void
  onDeleted: (taskId: string) => void
}

const STATUSES: { value: TaskStatus; label: string }[] = [
  { value: "todo", label: "Todo" },
  { value: "in_progress", label: "In Progress" },
  { value: "in_review", label: "In Review" },
  { value: "done", label: "Done" },
  { value: "blocked", label: "Blocked" },
]

const PRIORITIES: { value: TaskPriority; label: string }[] = [
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
  { value: "none", label: "None" },
]

export function TaskDetailPanel({ task, allTasks, onClose, onUpdated, onDeleted }: TaskDetailPanelProps) {
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description)
  const [status, setStatus] = useState<TaskStatus>(task.status)
  const [priority, setPriority] = useState<TaskPriority>(task.priority)
  const [assignee, setAssignee] = useState(task.assignee ?? "")
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [depId, setDepId] = useState("")
  const [depError, setDepError] = useState<string | null>(null)

  useEffect(() => {
    setTitle(task.title)
    setDescription(task.description)
    setStatus(task.status)
    setPriority(task.priority)
    setAssignee(task.assignee ?? "")
    setConfirmDelete(false)
    setDepId("")
    setDepError(null)
  }, [task])

  async function handleSave(e: FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    setSaving(true)
    try {
      const updated = await api.tasks.update(task.id, {
        title: title.trim(),
        description: description.trim(),
        status,
        priority,
        assignee: assignee.trim() || undefined,
      })
      onUpdated(updated)
    } catch (err) {
      console.error("Failed to save task:", err)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!confirmDelete) {
      setConfirmDelete(true)
      return
    }
    try {
      await api.tasks.delete(task.id)
      onDeleted(task.id)
    } catch (err) {
      console.error("Failed to delete task:", err)
    }
  }

  async function handleAddDependency() {
    if (!depId.trim()) return
    setDepError(null)
    try {
      const updated = await api.tasks.addDependency(task.id, depId.trim())
      onUpdated(updated)
      setDepId("")
    } catch (err) {
      setDepError(err instanceof Error ? err.message : "Failed to add dependency")
    }
  }

  async function handleRemoveDependency(dependsOnId: string) {
    try {
      const updated = await api.tasks.removeDependency(task.id, dependsOnId)
      onUpdated(updated)
    } catch (err) {
      console.error("Failed to remove dependency:", err)
    }
  }

  const dependsOnTasks = allTasks.filter((t) => task.depends_on_ids.includes(t.id))
  const dependedByTasks = allTasks.filter((t) => task.depended_by_ids.includes(t.id))
  // Tasks that can be added as dependencies (not self, not already a dependency)
  const availableTasks = allTasks.filter(
    (t) => t.id !== task.id && !task.depends_on_ids.includes(t.id)
  )

  return (
    <div
      className="fixed inset-y-0 right-0 z-40 flex w-96 flex-col bg-background shadow-xl border-l-2 border-border"
      style={{ animation: "slideInFromRight 0.2s ease-out" }}
    >
      <div className="flex items-center justify-between border-b-2 border-border px-4 py-3">
        <h2 className="text-sm font-semibold">Task Details</h2>
        <button
          onClick={onClose}
          className="p-1 text-muted-foreground hover:bg-accent hover:text-foreground border border-transparent hover:border-border"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <form onSubmit={handleSave} className="flex flex-1 flex-col gap-4 overflow-y-auto p-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Status</Label>
          <Select value={status} onValueChange={(v) => setStatus(v as TaskStatus)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {STATUSES.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {task.blocked_reason && (
            <p className="text-xs text-destructive/80 mt-0.5">{task.blocked_reason}</p>
          )}
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Priority</Label>
          <Select value={priority} onValueChange={(v) => setPriority(v as TaskPriority)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PRIORITIES.map((p) => (
                <SelectItem key={p.value} value={p.value}>
                  {p.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="assignee">Assignee</Label>
          <Input
            id="assignee"
            value={assignee}
            onChange={(e) => setAssignee(e.target.value)}
            placeholder="Agent ID"
          />
        </div>

        {/* Dependencies section */}
        <div className="border-t-2 border-border pt-3">
          <Label className="text-xs text-muted-foreground uppercase tracking-wider">Dependencies</Label>

          {/* Depends on */}
          <div className="mt-2">
            <span className="text-[11px] text-muted-foreground">Depends on:</span>
            {dependsOnTasks.length === 0 ? (
              <p className="text-xs text-muted-foreground italic mt-0.5">None</p>
            ) : (
              <ul className="mt-1 space-y-1">
                {dependsOnTasks.map((dep) => (
                  <li key={dep.id} className="flex items-center justify-between text-xs bg-muted/30 px-2 py-1 border border-border">
                    <span className="truncate">
                      <span className={cn(
                        "inline-block w-2 h-2 mr-1.5",
                        dep.status === "done" ? "bg-emerald-500" :
                        dep.status === "in_progress" ? "bg-amber-500" :
                        "bg-zinc-400"
                      )} />
                      {dep.title}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveDependency(dep.id)}
                      className="text-muted-foreground hover:text-destructive ml-2"
                    >
                      <Unlink className="h-3 w-3" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Depended by */}
          {dependedByTasks.length > 0 && (
            <div className="mt-2">
              <span className="text-[11px] text-muted-foreground">Depended by:</span>
              <ul className="mt-1 space-y-1">
                {dependedByTasks.map((dep) => (
                  <li key={dep.id} className="text-xs bg-muted/30 px-2 py-1 border border-border flex items-center">
                    <span className={cn(
                      "inline-block w-2 h-2 mr-1.5",
                      dep.status === "done" ? "bg-emerald-500" :
                      dep.status === "blocked" ? "bg-red-500" :
                      "bg-zinc-400"
                    )} />
                    {dep.title}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Add dependency */}
          {availableTasks.length > 0 && (
            <div className="mt-3 flex gap-1.5">
              <select
                value={depId}
                onChange={(e) => setDepId(e.target.value)}
                className="flex-1 text-xs bg-background border border-border px-2 py-1.5 text-foreground"
              >
                <option value="">Add dependency...</option>
                {availableTasks.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.title}
                  </option>
                ))}
              </select>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={handleAddDependency}
                disabled={!depId.trim()}
              >
                <Link className="h-3 w-3" />
              </Button>
            </div>
          )}
          {depError && (
            <p className="text-xs text-destructive mt-1">{depError}</p>
          )}
        </div>

        <div className="mt-auto flex items-center gap-2 border-t-2 border-border pt-4">
          <Button type="submit" disabled={saving || !title.trim()}>
            {saving ? "Saving..." : "Save"}
          </Button>
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            className="ml-auto"
            onClick={handleDelete}
          >
            <Trash2 className="h-3.5 w-3.5" />
            {confirmDelete ? "Confirm" : "Delete"}
          </Button>
        </div>
      </form>
    </div>
  )
}

