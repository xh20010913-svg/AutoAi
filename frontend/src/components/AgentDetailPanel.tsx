import { useState, useEffect, type FormEvent } from "react"
import { X, Trash2 } from "lucide-react"
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
import { api, type Agent, type AgentStatus, type Role } from "@/lib/api"
import { useI18n } from "@/context/i18n-context"

interface AgentDetailPanelProps {
  agent: Agent
  roles: Role[]
  onClose: () => void
  onUpdated: (agent: Agent) => void
  onDeleted: (agentId: string) => void
}

const STATUSES: { value: AgentStatus; labelKey: "status.idle" | "status.working" | "status.blocked" | "status.error" }[] = [
  { value: "idle", labelKey: "status.idle" },
  { value: "working", labelKey: "status.working" },
  { value: "blocked", labelKey: "status.blocked" },
  { value: "error", labelKey: "status.error" },
]

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

export function AgentDetailPanel({ agent, roles, onClose, onUpdated, onDeleted }: AgentDetailPanelProps) {
  const { t } = useI18n()
  const [name, setName] = useState(agent.name)
  const [role, setRole] = useState(agent.role)
  const [status, setStatus] = useState<AgentStatus>(agent.status)
  const [model, setModel] = useState(agent.model)
  const [provider, setProvider] = useState(agent.provider)
  const [apiKeyEnv, setApiKeyEnv] = useState(agent.api_key_env)
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  useEffect(() => {
    setName(agent.name)
    setRole(agent.role)
    setStatus(agent.status)
    setModel(agent.model)
    setProvider(agent.provider)
    setApiKeyEnv(agent.api_key_env)
    setConfirmDelete(false)
  }, [agent])

  async function handleSave(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setSaving(true)
    try {
      const updated = await api.agents.update(agent.id, {
        name: name.trim(),
        role,
        status,
        model,
        provider,
        api_key_env: apiKeyEnv.trim() || undefined,
      })
      onUpdated(updated)
    } catch (err) {
      console.error("Failed to save agent:", err)
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
      await api.agents.delete(agent.id)
      onDeleted(agent.id)
    } catch (err) {
      console.error("Failed to delete agent:", err)
    }
  }

  return (
    <div
      className="fixed inset-y-0 right-0 z-40 flex w-96 flex-col bg-background shadow-xl border-l-2 border-border"
      style={{ animation: "slideInFromRight 0.2s ease-out" }}
    >
      <div className="flex items-center justify-between border-b-2 border-border px-4 py-3">
        <h2 className="text-sm font-semibold">{t("agents.editAgent")}</h2>
        <button
          onClick={onClose}
          className="p-1 text-muted-foreground hover:bg-accent hover:text-foreground border border-transparent hover:border-border"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <form onSubmit={handleSave} className="flex flex-1 flex-col gap-4 overflow-y-auto p-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="agent-name">{t("agentForm.name")}</Label>
          <Input
            id="agent-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>{t("agentForm.role")}</Label>
          <Select value={role} onValueChange={setRole}>
            <SelectTrigger>
              <SelectValue />
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
          <Label>{t("agentForm.status")}</Label>
          <Select value={status} onValueChange={(v) => setStatus(v as AgentStatus)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {STATUSES.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {t(s.labelKey)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>{t("agentForm.model")}</Label>
          <Select value={model} onValueChange={setModel}>
            <SelectTrigger>
              <SelectValue />
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
              <SelectValue />
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

        <div className="mt-auto flex items-center gap-2 border-t-2 border-border pt-4">
          <Button type="submit" disabled={saving || !name.trim()}>
            {saving ? t("common.saving") : t("common.save")}
          </Button>
          <Button type="button" variant="ghost" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button
            type="button"
            variant="destructive"
            className="ml-auto"
            onClick={handleDelete}
          >
            <Trash2 className="h-3.5 w-3.5" />
            {confirmDelete ? t("common.confirm") : t("common.delete")}
          </Button>
        </div>
      </form>
    </div>
  )
}
