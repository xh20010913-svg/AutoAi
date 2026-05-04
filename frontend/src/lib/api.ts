const API_BASE = "http://localhost:18765/api/v1"

export type TaskStatus = "todo" | "in_progress" | "in_review" | "done" | "blocked"
export type TaskPriority = "high" | "medium" | "low" | "none"

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

export interface Agent {
  id: string
  name: string
  role: string
  status: "idle" | "working" | "blocked"
  model: string
  completed_tasks: number
  current_task_id: string | null
  active_tasks: number
}

export const api = {
  agents: {
    listAll: () => request<Agent[]>("/agents/status/all"),
    getStatus: (agentId: string) => request<Agent>(`/agents/${agentId}/status`),
  },

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
}
