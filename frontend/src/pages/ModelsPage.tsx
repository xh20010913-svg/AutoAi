import { useState, useEffect, useCallback } from "react"
import { Plus, Check, X, Trash2, Server, Cpu } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  providersApi,
  modelsApi,
  type Provider,
  type Model,
  type ProviderCreate,
  type ModelCreate,
} from "@/api/providers"

const PROVIDER_TYPES = ["Anthropic", "OpenAI", "DeepSeek", "Groq", "Google", "Custom"]

// --- Provider Card ---

function ProviderCard({
  provider,
  selected,
  onClick,
  onToggle,
  onDelete,
}: {
  provider: Provider
  selected: boolean
  onClick: () => void
  onToggle: () => void
  onDelete: () => void
}) {
  return (
    <div
      className={cn(
        "bg-card p-4 cursor-pointer transition-colors pixel-border",
        selected
          ? "border-primary shadow-[2px_2px_0_0_var(--primary),4px_4px_0_0_var(--pixel-shadow)]"
          : "hover:border-primary/50",
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center bg-primary/15 text-primary border-2 border-primary/30">
            <Server className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-card-foreground">{provider.name}</h3>
            <p className="text-[11px] text-muted-foreground font-mono">{provider.type}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          {provider.keyConfigured ? (
            <span className="flex items-center gap-1 bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-medium text-emerald-400 border border-emerald-500/20">
              <Check className="h-3 w-3" /> Key
            </span>
          ) : (
            <span className="flex items-center gap-1 bg-zinc-500/15 px-1.5 py-0.5 text-[10px] font-medium text-zinc-400 border border-zinc-500/20">
              <X className="h-3 w-3" /> Key
            </span>
          )}
        </div>
      </div>

      <div className="mt-3">
        <p className="text-[11px] text-muted-foreground mb-1 uppercase tracking-wider">Base URL</p>
        <code className="block bg-muted px-2 py-1 text-xs text-muted-foreground font-mono border border-border truncate">
          {provider.baseUrl}
        </code>
      </div>

      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-muted-foreground">Status</span>
          <button
            onClick={(e) => { e.stopPropagation(); onToggle() }}
            className={cn(
              "relative inline-flex h-5 w-9 items-center rounded-full border-2 transition-colors duration-200",
              provider.enabled
                ? "border-emerald-500 bg-emerald-500/30"
                : "border-zinc-500 bg-zinc-500/15",
            )}
            title={provider.enabled ? "Enabled" : "Disabled"}
          >
            <span
              className={cn(
                "inline-block h-3 w-3 rounded-full transition-transform duration-200",
                provider.enabled
                  ? "translate-x-4 bg-emerald-400"
                  : "translate-x-0.5 bg-zinc-400",
              )}
            />
          </button>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete() }}
          className="p-1 text-muted-foreground hover:text-destructive transition-colors border border-transparent hover:border-destructive/30"
          title="Delete provider"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}

// --- Add Provider Dialog ---

function AddProviderDialog({
  open,
  onOpenChange,
  onAdd,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onAdd: (data: ProviderCreate) => void
}) {
  const [name, setName] = useState("")
  const [baseUrl, setBaseUrl] = useState("")
  const [apiType, setApiType] = useState("")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name || !baseUrl || !apiType) return
    onAdd({ name, baseUrl, type: apiType })
    setName("")
    setBaseUrl("")
    setApiType("")
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Provider</DialogTitle>
          <DialogDescription>Configure a new model provider.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="prov-name">Name</Label>
            <Input id="prov-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Anthropic" required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="prov-baseurl">Base URL</Label>
            <Input id="prov-baseurl" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder="e.g. https://api.anthropic.com" required />
          </div>
          <div className="space-y-1.5">
            <Label>API Type</Label>
            <Select value={apiType} onValueChange={setApiType}>
              <SelectTrigger>
                <SelectValue placeholder="Select API type..." />
              </SelectTrigger>
              <SelectContent>
                {PROVIDER_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>{t}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={!name || !baseUrl || !apiType}>Add Provider</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// --- Add Model Dialog ---

function AddModelDialog({
  open,
  onOpenChange,
  onAdd,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onAdd: (data: ModelCreate) => void
}) {
  const [name, setName] = useState("")
  const [modelId, setModelId] = useState("")
  const [contextWindow, setContextWindow] = useState("")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const cw = parseInt(contextWindow, 10)
    if (!name || !modelId || isNaN(cw)) return
    onAdd({ name, modelId, contextWindow: cw })
    setName("")
    setModelId("")
    setContextWindow("")
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Model</DialogTitle>
          <DialogDescription>Register a new model under this provider.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="mod-name">Name</Label>
            <Input id="mod-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Claude Opus 4.7" required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="mod-id">Model ID</Label>
            <Input id="mod-id" value={modelId} onChange={(e) => setModelId(e.target.value)} placeholder="e.g. claude-opus-4-7" required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="mod-cw">Context Window</Label>
            <Input id="mod-cw" type="number" value={contextWindow} onChange={(e) => setContextWindow(e.target.value)} placeholder="e.g. 200000" required />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={!name || !modelId || !contextWindow}>Add Model</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// --- Model Table ---

function ModelTable({
  models,
  onDelete,
}: {
  models: Model[]
  onDelete: (model: Model) => void
}) {
  function formatContextWindow(cw: number): string {
    if (cw >= 1_000_000) return `${(cw / 1_000_000).toFixed(0)}M`
    if (cw >= 1_000) return `${(cw / 1_000).toFixed(0)}K`
    return String(cw)
  }

  if (models.length === 0) {
    return (
      <p className="text-xs text-muted-foreground py-8 text-center border-2 border-dashed border-border">
        No models configured for this provider.
      </p>
    )
  }

  return (
    <div className="border-2 border-border overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="bg-muted/50">
            <th className="text-left px-3 py-2 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Name</th>
            <th className="text-left px-3 py-2 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Model ID</th>
            <th className="text-right px-3 py-2 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Context Window</th>
            <th className="w-10 px-2 py-2" />
          </tr>
        </thead>
        <tbody>
          {models.map((m) => (
            <tr key={m.id} className="border-t border-border hover:bg-accent/30 transition-colors">
              <td className="px-3 py-2 text-xs font-medium">{m.name}</td>
              <td className="px-3 py-2">
                <code className="text-[11px] font-mono text-muted-foreground bg-muted px-1.5 py-0.5 border border-border">
                  {m.modelId}
                </code>
              </td>
              <td className="px-3 py-2 text-xs text-muted-foreground text-right font-mono tabular-nums">
                {formatContextWindow(m.contextWindow)}
              </td>
              <td className="px-2 py-2 text-center">
                <button
                  onClick={() => onDelete(m)}
                  className="p-1 text-muted-foreground hover:text-destructive transition-colors border border-transparent hover:border-destructive/30"
                  title="Delete model"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// --- Page ---

export function ModelsPage() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [models, setModels] = useState<Model[]>([])
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null)
  const [addProviderOpen, setAddProviderOpen] = useState(false)
  const [addModelOpen, setAddModelOpen] = useState(false)

  const loadProviders = useCallback(async () => {
    const res = await providersApi.list()
    setProviders(res.providers)
  }, [])

  const loadModels = useCallback(async (providerId: string) => {
    const res = await modelsApi.list(providerId)
    setModels(res.models)
  }, [])

  useEffect(() => {
    loadProviders()
  }, [loadProviders])

  useEffect(() => {
    if (selectedProviderId) {
      loadModels(selectedProviderId)
    } else {
      setModels([])
    }
  }, [selectedProviderId, loadModels])

  async function handleAddProvider(data: ProviderCreate) {
    await providersApi.create(data)
    loadProviders()
  }

  async function handleToggleProvider(provider: Provider) {
    await providersApi.update(provider.id, { enabled: !provider.enabled })
    loadProviders()
  }

  async function handleDeleteProvider(id: string) {
    await providersApi.delete(id)
    if (selectedProviderId === id) setSelectedProviderId(null)
    loadProviders()
  }

  async function handleAddModel(data: ModelCreate) {
    if (!selectedProviderId) return
    await modelsApi.create(selectedProviderId, data)
    loadModels(selectedProviderId)
  }

  async function handleDeleteModel(model: Model) {
    await modelsApi.delete(model.providerId, model.id)
    loadModels(model.providerId)
  }

  const selectedProvider = providers.find((p) => p.id === selectedProviderId) ?? null
  const enabledCount = providers.filter((p) => p.enabled).length

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-lg font-semibold mb-1">Model Providers</h1>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>Total: {providers.length}</span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 bg-emerald-500 rounded-full" />
              Enabled: {enabledCount}
            </span>
          </div>
        </div>
        <Button onClick={() => setAddProviderOpen(true)}>
          <Plus className="h-3.5 w-3.5" />
          Add Provider
        </Button>
      </div>

      {/* Provider grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {providers.map((provider) => (
          <ProviderCard
            key={provider.id}
            provider={provider}
            selected={provider.id === selectedProviderId}
            onClick={() => setSelectedProviderId(provider.id === selectedProviderId ? null : provider.id)}
            onToggle={() => handleToggleProvider(provider)}
            onDelete={() => handleDeleteProvider(provider.id)}
          />
        ))}
        {providers.length === 0 && (
          <p className="text-xs text-muted-foreground py-8 text-center col-span-full border-2 border-dashed border-border">
            No providers configured. Click "Add Provider" to get started.
          </p>
        )}
      </div>

      {/* Model section */}
      {selectedProvider && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center bg-primary/15 text-primary border-2 border-primary/30">
                <Cpu className="h-3.5 w-3.5" />
              </div>
              <h2 className="text-sm font-semibold">
                {selectedProvider.name} <span className="text-muted-foreground font-normal">— Models ({models.length})</span>
              </h2>
            </div>
            <Button size="sm" onClick={() => setAddModelOpen(true)}>
              <Plus className="h-3 w-3" />
              Add Model
            </Button>
          </div>
          <ModelTable models={models} onDelete={handleDeleteModel} />
        </div>
      )}

      {/* Dialogs */}
      <AddProviderDialog open={addProviderOpen} onOpenChange={setAddProviderOpen} onAdd={handleAddProvider} />
      <AddModelDialog open={addModelOpen} onOpenChange={setAddModelOpen} onAdd={handleAddModel} />
    </div>
  )
}
