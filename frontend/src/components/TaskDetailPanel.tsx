import { useState, useEffect, type FormEvent } from "react"
import { X, Trash2 } from "lucide-react"
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

interface TaskDetailPanelProps {
  task: Task
  projectId: string
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

export function TaskDetailPanel({ task, projectId, onClose, onUpdated, onDeleted }: TaskDetailPanelProps) {
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description)
  const [status, setStatus] = useState<TaskStatus>(task.status)
  const [priority, setPriority] = useState<TaskPriority>(task.priority)
  const [assignee, setAssignee] = useState(task.assignee_id ?? "")
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  useEffect(() => {
    setTitle(task.title)
    setDescription(task.description)
    setStatus(task.status)
    setPriority(task.priority)
    setAssignee(task.assignee_id ?? "")
    setConfirmDelete(false)
  }, [task])

  async function handleSave(e: FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    setSaving(true)
    try {
      const updated = await api.tasks.update(projectId, task.id, {
        title: title.trim(),
        description: description.trim(),
        status,
        priority,
        assignee_id: assignee.trim() || undefined,
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
      await api.tasks.delete(projectId, task.id)
      onDeleted(task.id)
    } catch (err) {
      console.error("Failed to delete task:", err)
    }
  }

  return (
    <div
      className="fixed inset-y-0 right-0 z-40 flex w-96 flex-col bg-background shadow-xl border-l-2 border-border relative"
      style={{ animation: "slideInFromRight 0.2s ease-out" }}
    >
      <div className="flex items-center justify-between border-b-2 border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 bg-primary" />
          <h2 className="text-sm font-semibold">Task Details</h2>
        </div>
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
