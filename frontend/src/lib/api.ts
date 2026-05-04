const API_BASE = "http://localhost:18765/api/v1"

export type TaskStatus = "todo" | "in_progress" | "in_review" | "done" | "blocked"
export type TaskPriority = "high" | "medium" | "low" | "none"
export type AgentStatus = "idle" | "working" | "blocked" | "error"

export interface Agent {
  id: string
  name: string
  role: string
  status: AgentStatus
  model: string
  provider: string
  api_key_env: string
  current_tasks: number
  completed_tasks: number
  created_at: string
  updated_at: string
}

export interface AgentCreate {
  name: string
  role: string
  model?: string
  provider?: string
  api_key_env?: string
}

export interface AgentUpdate {
  name?: string
  role?: string
  model?: string
  provider?: string
  api_key_env?: string
  status?: AgentStatus
}

export interface Role {
  id: string
  name: string
  description: string
  budget_level: string
  authority: string
  created_at: string
  updated_at: string
}

export interface RoleCreate {
  name: string
  description?: string
  budget_level?: string
  authority?: string
}

export interface RoleUpdate {
  name?: string
  description?: string
  budget_level?: string
  authority?: string
}

export interface Task {
  id: string
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  assignee_id: string | null
  parent_id: string | null
  position: number
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  title: string
  description?: string
  priority?: TaskPriority
  assignee_id?: string
}

export interface TaskUpdate {
  title?: string
  description?: string
  status?: TaskStatus
  priority?: TaskPriority
  assignee_id?: string
  position?: number
}

export interface Project {
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API ${res.status}: ${body}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  projects: {
    list: () => request<{ projects: Project[]; total: number }>("/projects"),
  },

  tasks: {
    list: (projectId: string, status?: string) =>
      request<{ tasks: Task[]; total: number }>(
        `/projects/${projectId}/tasks${status ? `?status=${encodeURIComponent(status)}` : ""}`,
      ),

    create: (projectId: string, data: TaskCreate) =>
      request<Task>(`/projects/${projectId}/tasks`, {
        method: "POST",
        body: JSON.stringify(data),
      }),

    update: (projectId: string, taskId: string, data: TaskUpdate) =>
      request<Task>(`/projects/${projectId}/tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),

    delete: (projectId: string, taskId: string) =>
      request<void>(`/projects/${projectId}/tasks/${taskId}`, {
        method: "DELETE",
      }),
  },

  agents: {
    list: () => request<{ agents: Agent[]; total: number }>("/agents"),

    get: (agentId: string) => request<Agent>(`/agents/${agentId}`),

    create: (data: AgentCreate) =>
      request<Agent>("/agents", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    update: (agentId: string, data: AgentUpdate) =>
      request<Agent>(`/agents/${agentId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),

    delete: (agentId: string) =>
      request<void>(`/agents/${agentId}`, {
        method: "DELETE",
      }),
  },

  roles: {
    list: () => request<{ roles: Role[]; total: number }>("/roles"),

    create: (data: RoleCreate) =>
      request<Role>("/roles", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    update: (roleId: string, data: RoleUpdate) =>
      request<Role>(`/roles/${roleId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),

    delete: (roleId: string) =>
      request<void>(`/roles/${roleId}`, {
        method: "DELETE",
      }),
  },
}
