import { useState, type FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
import { api, type Agent, type Role } from "@/lib/api"
import { useI18n } from "@/context/i18n-context"
import { Plus } from "lucide-react"

interface CreateAgentDialogProps {
  roles: Role[]
  onCreated: (agent: Agent) => void
}

const MODELS = [
  { value: "gpt-4", labelKey: "model.gpt4" as const },
  { value: "gpt-4o", labelKey: "model.gpt4o" as const },
  { value: "claude-3-opus", labelKey: "model.claude3Opus" as const },
  { value: "claude-3-sonnet", labelKey: "model.claude3Sonnet" as const },
  { value: "claude-sonnet-4-6", labelKey: "model.claudeSonnet46" as const },
  { value: "claude-haiku-4-5", labelKey: "model.claudeHaiku45" as const },
]

const PROVIDERS = [
  { value: "openai", labelKey: "provider.openai" as const },
  { value: "anthropic", labelKey: "provider.anthropic" as const },
  { value: "azure", labelKey: "provider.azure" as const },
  { value: "google", labelKey: "provider.google" as const },
]

export function CreateAgentDialog({ roles, onCreated }: CreateAgentDialogProps) {
  const { t } = useI18n()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [role, setRole] = useState("")
  const [model, setModel] = useState("")
  const [provider, setProvider] = useState("")
  const [apiKeyEnv, setApiKeyEnv] = useState("")
  const [creating, setCreating] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!name.trim() || !role) return
    setCreating(true)
    try {
      const agent = await api.agents.create({
        name: name.trim(),
        role,
        model: model || undefined,
        provider: provider || undefined,
        api_key_env: apiKeyEnv.trim() || undefined,
      })
      onCreated(agent)
      setName("")
      setRole("")
      setModel("")
      setProvider("")
      setApiKeyEnv("")
      setOpen(false)
    } catch (err) {
      console.error("Failed to create agent:", err)
    } finally {
      setCreating(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-3.5 w-3.5" />
          {t("agents.createAgent")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("agents.createAgent")}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="agent-name">{t("agentForm.name")}</Label>
            <Input
              id="agent-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("agentForm.namePlaceholder")}
              required
              autoFocus
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>{t("agentForm.role")}</Label>
            <Select value={role} onValueChange={setRole}>
              <SelectTrigger>
                <SelectValue placeholder={t("agentForm.rolePlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                {roles.map((r) => (
                  <SelectItem key={r.id} value={r.name}>
                    {r.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>{t("agentForm.model")}</Label>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger>
                <SelectValue placeholder={t("agentForm.modelPlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                {MODELS.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {t(m.labelKey)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>{t("agentForm.provider")}</Label>
            <Select value={provider} onValueChange={setProvider}>
              <SelectTrigger>
                <SelectValue placeholder={t("agentForm.providerPlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                {PROVIDERS.map((p) => (
                  <SelectItem key={p.value} value={p.value}>
                    {t(p.labelKey)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="agent-api-key">{t("agentForm.apiKeyEnv")}</Label>
            <Input
              id="agent-api-key"
              value={apiKeyEnv}
              onChange={(e) => setApiKeyEnv(e.target.value)}
              placeholder={t("agentForm.apiKeyEnvPlaceholder")}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={creating || !name.trim() || !role}>
              {creating ? t("common.creating") : t("common.create")}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
