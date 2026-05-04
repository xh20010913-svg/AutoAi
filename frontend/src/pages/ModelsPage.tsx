import { Plus, Key, Check, X } from "lucide-react"

interface Provider {
  id: string
  name: string
  type: string
  baseUrl: string
  models: string[]
  keyConfigured: boolean
}

const mockProviders: Provider[] = [
  {
    id: "1",
    name: "Anthropic",
    type: "Anthropic",
    baseUrl: "https://api.anthropic.com",
    models: ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5"],
    keyConfigured: true,
  },
  {
    id: "2",
    name: "OpenAI",
    type: "OpenAI",
    baseUrl: "https://api.openai.com/v1",
    models: ["gpt-4o", "gpt-4o-mini", "o3-mini"],
    keyConfigured: true,
  },
  {
    id: "3",
    name: "DeepSeek",
    type: "DeepSeek",
    baseUrl: "https://api.deepseek.com/v1",
    models: ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
    keyConfigured: false,
  },
]

function ProviderCard({ provider }: { provider: Provider }) {
  return (
    <div className="bg-card p-4 pixel-border">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-medium text-card-foreground">{provider.name}</h3>
          <p className="text-xs text-muted-foreground mt-0.5 font-mono">{provider.type}</p>
        </div>
        <div className="flex items-center gap-1.5">
          {provider.keyConfigured ? (
            <span className="flex items-center gap-1 bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-medium text-emerald-400 border border-emerald-500/20">
              <Check className="h-3 w-3" /> Configured
            </span>
          ) : (
            <span className="flex items-center gap-1 bg-zinc-500/15 px-1.5 py-0.5 text-[10px] font-medium text-zinc-400 border border-zinc-500/20">
              <X className="h-3 w-3" /> Not configured
            </span>
          )}
        </div>
      </div>
      <div className="mt-3">
        <p className="text-[11px] text-muted-foreground mb-1.5 uppercase tracking-wider">Base URL</p>
        <code className="block bg-muted px-2 py-1 text-xs text-muted-foreground font-mono border border-border">
          {provider.baseUrl}
        </code>
      </div>
      <div className="mt-3">
        <p className="text-[11px] text-muted-foreground mb-1.5 uppercase tracking-wider">Available Models</p>
        <div className="flex flex-wrap gap-1">
          {provider.models.map((model) => (
            <span key={model} className="bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground font-mono border border-border">
              {model}
            </span>
          ))}
        </div>
      </div>
      <div className="mt-4 flex gap-2">
        <button className="inline-flex items-center gap-1.5 border-2 border-input bg-transparent px-2.5 py-1.5 text-xs font-medium hover:bg-accent hover:text-accent-foreground transition-colors">
          <Key className="h-3 w-3" />
          Update Key
        </button>
      </div>
    </div>
  )
}

export function ModelsPage() {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold">Model Providers</h1>
        <button className="inline-flex items-center gap-1.5 bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:opacity-90 transition-opacity pixel-border-sm">
          <Plus className="h-3.5 w-3.5" />
          Add Provider
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockProviders.map((provider) => (
          <ProviderCard key={provider.id} provider={provider} />
        ))}
      </div>
    </div>
  )
}
