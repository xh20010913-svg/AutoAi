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
import { Plus } from "lucide-react"
import { useTranslation } from "@/hooks/useLanguage"

interface CreateTaskDialogProps {
  projectId: string
  onCreated: (task: Task) => void
}

export function CreateTaskDialog({ projectId, onCreated }: CreateTaskDialogProps) {
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [priority, setPriority] = useState<TaskPriority>("medium")
  const [assignee, setAssignee] = useState("")
  const [creating, setCreating] = useState(false)
  const { t } = useTranslation()

  const PRIORITIES: { value: TaskPriority; label: string }[] = [
    { value: "high", label: t("createTask.priorityHigh") },
    { value: "medium", label: t("createTask.priorityMedium") },
    { value: "low", label: t("createTask.priorityLow") },
    { value: "none", label: t("createTask.priorityNone") },
  ]

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!title.trim()) return
    setCreating(true)
    try {
      const task = await api.tasks.create(projectId, {
        title: title.trim(),
        description: description.trim() || undefined,
        priority,
        assignee_id: assignee.trim() || undefined,
      })
      onCreated(task)
      setTitle("")
      setDescription("")
      setPriority("medium")
      setAssignee("")
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
          {t("board.newTask")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("createTask.title")}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="create-title">{t("createTask.labelTitle")}</Label>
            <Input id="create-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder={t("createTask.placeholderTitle")} required autoFocus />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="create-description">{t("createTask.labelDescription")}</Label>
            <Textarea id="create-description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder={t("createTask.placeholderDescription")} rows={3} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>{t("createTask.labelPriority")}</Label>
            <Select value={priority} onValueChange={(v) => setPriority(v as TaskPriority)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {PRIORITIES.map((p) => (<SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="create-assignee">{t("createTask.labelAssignee")}</Label>
            <Input id="create-assignee" value={assignee} onChange={(e) => setAssignee(e.target.value)} placeholder={t("createTask.placeholderAssignee")} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={() => setOpen(false)}>{t("createTask.cancel")}</Button>
            <Button type="submit" disabled={creating || !title.trim()}>
              {creating ? t("createTask.creating") : t("createTask.create")}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
