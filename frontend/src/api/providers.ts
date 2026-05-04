export interface Provider {
  id: string
  name: string
  type: string
  baseUrl: string
  enabled: boolean
  keyConfigured: boolean
  createdAt: string
}

export interface Model {
  id: string
  providerId: string
  name: string
  modelId: string
  contextWindow: number
  createdAt: string
}

export interface ProviderCreate {
  name: string
  type: string
  baseUrl: string
}

export interface ProviderUpdate {
  name?: string
  type?: string
  baseUrl?: string
  enabled?: boolean
}

export interface ModelCreate {
  name: string
  modelId: string
  contextWindow: number
}

export interface ModelUpdate {
  name?: string
  modelId?: string
  contextWindow?: number
}

// --- Mock data ---

const now = new Date().toISOString()

let mockProviders: Provider[] = [
  {
    id: "prov-1",
    name: "Anthropic",
    type: "Anthropic",
    baseUrl: "https://api.anthropic.com",
    enabled: true,
    keyConfigured: true,
    createdAt: "2026-04-15T08:00:00Z",
  },
  {
    id: "prov-2",
    name: "OpenAI",
    type: "OpenAI",
    baseUrl: "https://api.openai.com/v1",
    enabled: true,
    keyConfigured: true,
    createdAt: "2026-04-16T10:30:00Z",
  },
  {
    id: "prov-3",
    name: "DeepSeek",
    type: "DeepSeek",
    baseUrl: "https://api.deepseek.com/v1",
    enabled: true,
    keyConfigured: false,
    createdAt: "2026-04-20T14:00:00Z",
  },
  {
    id: "prov-4",
    name: "Groq",
    type: "Groq",
    baseUrl: "https://api.groq.com/openai/v1",
    enabled: false,
    keyConfigured: true,
    createdAt: "2026-04-25T09:15:00Z",
  },
]

let mockModels: Model[] = [
  { id: "mod-1", providerId: "prov-1", name: "Claude Opus 4.7", modelId: "claude-opus-4-7", contextWindow: 200000, createdAt: "2026-04-15T08:00:00Z" },
  { id: "mod-2", providerId: "prov-1", name: "Claude Sonnet 4.6", modelId: "claude-sonnet-4-6", contextWindow: 200000, createdAt: "2026-04-15T08:00:00Z" },
  { id: "mod-3", providerId: "prov-1", name: "Claude Haiku 4.5", modelId: "claude-haiku-4-5", contextWindow: 200000, createdAt: "2026-04-15T08:00:00Z" },
  { id: "mod-4", providerId: "prov-2", name: "GPT-4o", modelId: "gpt-4o", contextWindow: 128000, createdAt: "2026-04-16T10:30:00Z" },
  { id: "mod-5", providerId: "prov-2", name: "GPT-4o Mini", modelId: "gpt-4o-mini", contextWindow: 128000, createdAt: "2026-04-16T10:30:00Z" },
  { id: "mod-6", providerId: "prov-2", name: "o3 Mini", modelId: "o3-mini", contextWindow: 200000, createdAt: "2026-04-16T10:30:00Z" },
  { id: "mod-7", providerId: "prov-3", name: "DeepSeek Chat", modelId: "deepseek-chat", contextWindow: 65536, createdAt: "2026-04-20T14:00:00Z" },
  { id: "mod-8", providerId: "prov-3", name: "DeepSeek Coder", modelId: "deepseek-coder", contextWindow: 65536, createdAt: "2026-04-20T14:00:00Z" },
  { id: "mod-9", providerId: "prov-3", name: "DeepSeek Reasoner", modelId: "deepseek-reasoner", contextWindow: 65536, createdAt: "2026-04-20T14:00:00Z" },
  { id: "mod-10", providerId: "prov-4", name: "Llama 4 Maestro", modelId: "llama-4-maestro", contextWindow: 128000, createdAt: "2026-04-25T09:15:00Z" },
  { id: "mod-11", providerId: "prov-4", name: "Llama 4 Scout", modelId: "llama-4-scout", contextWindow: 10000000, createdAt: "2026-04-25T09:15:00Z" },
  { id: "mod-12", providerId: "prov-4", name: "Mixtral 8x22B", modelId: "mixtral-8x22b", contextWindow: 65536, createdAt: "2026-04-25T09:15:00Z" },
]

let nextProvId = 5
let nextModId = 13

function delay(): Promise<void> {
  return new Promise((r) => setTimeout(r, 150 + Math.random() * 200))
}

// --- Provider API ---

export const providersApi = {
  list: async (): Promise<{ providers: Provider[] }> => {
    await delay()
    return { providers: [...mockProviders] }
  },

  get: async (id: string): Promise<Provider> => {
    await delay()
    const p = mockProviders.find((p) => p.id === id)
    if (!p) throw new Error("Provider not found")
    return { ...p }
  },

  create: async (data: ProviderCreate): Promise<Provider> => {
    await delay()
    const p: Provider = {
      id: `prov-${nextProvId++}`,
      name: data.name,
      type: data.type,
      baseUrl: data.baseUrl,
      enabled: true,
      keyConfigured: false,
      createdAt: new Date().toISOString(),
    }
    mockProviders.push(p)
    return p
  },

  update: async (id: string, data: ProviderUpdate): Promise<Provider> => {
    await delay()
    const idx = mockProviders.findIndex((p) => p.id === id)
    if (idx === -1) throw new Error("Provider not found")
    mockProviders[idx] = { ...mockProviders[idx], ...data }
    return mockProviders[idx]
  },

  delete: async (id: string): Promise<void> => {
    await delay()
    mockProviders = mockProviders.filter((p) => p.id !== id)
    mockModels = mockModels.filter((m) => m.providerId !== id)
  },
}

// --- Model API ---

export const modelsApi = {
  list: async (providerId: string): Promise<{ models: Model[] }> => {
    await delay()
    return { models: mockModels.filter((m) => m.providerId === providerId) }
  },

  create: async (providerId: string, data: ModelCreate): Promise<Model> => {
    await delay()
    const m: Model = {
      id: `mod-${nextModId++}`,
      providerId,
      name: data.name,
      modelId: data.modelId,
      contextWindow: data.contextWindow,
      createdAt: new Date().toISOString(),
    }
    mockModels.push(m)
    return m
  },

  update: async (providerId: string, modelId: string, data: ModelUpdate): Promise<Model> => {
    await delay()
    const idx = mockModels.findIndex((m) => m.id === modelId && m.providerId === providerId)
    if (idx === -1) throw new Error("Model not found")
    mockModels[idx] = { ...mockModels[idx], ...data }
    return mockModels[idx]
  },

  delete: async (providerId: string, modelId: string): Promise<void> => {
    await delay()
    mockModels = mockModels.filter((m) => !(m.id === modelId && m.providerId === providerId))
  },
}
