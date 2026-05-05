import { useState, type FormEvent } from "react"
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { api, type Task, type TaskPriority } from "@/lib/api"
import { Plus, X } from "lucide-react"

interface CreateTaskDialogProps {
  onCreated: (task: Task) => void
  allTasks: Task[]
}

const PRIORITIES: { value: TaskPriority; label: string }[] = [
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
  { value: "none", label: "None" },
]

export function CreateTaskDialog({ onCreated, allTasks }: CreateTaskDialogProps) {
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [priority, setPriority] = useState<TaskPriority>("medium")
  const [assignee, setAssignee] = useState("")
  const [depIds, setDepIds] = useState<string[]>([])
  const [depPicker, setDepPicker] = useState("")
  const [creating, setCreating] = useState(false)

  const availableForDep = allTasks.filter(
    (t) => !depIds.includes(t.id)
  )

  function addDep() {
    if (!depPicker.trim()) return
    setDepIds((prev) => [...prev, depPicker])
    setDepPicker("")
  }

  function removeDep(id: string) {
    setDepIds((prev) => prev.filter((d) => d !== id))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    setCreating(true)
    try {
      const task = await api.tasks.create({
        title: title.trim(),
        description: description.trim() || undefined,
        priority,
        assignee: assignee.trim() || undefined,
        depends_on_ids: depIds,
      })
      onCreated(task)
      setTitle("")
      setDescription("")
      setPriority("medium")
      setAssignee("")
      setDepIds([])
      setOpen(false)
    } catch (err) {
      console.error("Failed to create task:", err)
    } finally {
      setCreating(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-3.5 w-3.5" />
          New Task
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Task</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="create-title">Title</Label>
            <Input
              id="create-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Task title"
              required
              autoFocus
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="create-description">Description</Label>
            <Textarea
              id="create-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              rows={3}
            />
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
            <Label htmlFor="create-assignee">Assignee</Label>
            <Input
              id="create-assignee"
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
              placeholder="Agent ID (optional)"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>Dependencies</Label>
            {depIds.length > 0 && (
              <ul className="space-y-1 mb-1">
                {depIds.map((id) => {
                  const t = allTasks.find((a) => a.id === id)
                  return (
                    <li key={id} className="flex items-center justify-between text-xs bg-muted/30 px-2 py-1 border border-border">
                      <span className="truncate">{t?.title ?? id}</span>
                      <button
                        type="button"
                        onClick={() => removeDep(id)}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
            {availableForDep.length > 0 && (
              <div className="flex gap-1.5">
                <select
                  value={depPicker}
                  onChange={(e) => setDepPicker(e.target.value)}
                  className="flex-1 text-xs bg-background border border-border px-2 py-1.5 text-foreground"
                >
                  <option value="">Add dependency...</option>
                  {availableForDep.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.title}
                    </option>
                  ))}
                </select>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={addDep}
                  disabled={!depPicker.trim()}
                >
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={creating || !title.trim()}>
              {creating ? "Creating..." : "Create"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
