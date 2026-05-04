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

export type RunStatus = "running" | "succeeded" | "failed" | "stopped"

export interface Agent {
  id: string
  name: string
  role: string
  model: string
  status: string
}

export interface Run {
  id: string
  agent_id: string
  agent_name: string
  task_id: string | null
  task_title: string | null
  command: string | null
  status: RunStatus
  started_at: string
  finished_at: string | null
  duration_ms: number | null
}

export interface RunCreate {
  agent_id: string
  task_id?: string
  command?: string
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
    list: () => request<{ agents: Agent[] }>("/agents"),
  },

  runs: {
    list: (agentId?: string) =>
      request<{ runs: Run[] }>(
        `/runs${agentId ? `?agent_id=${encodeURIComponent(agentId)}` : ""}`,
      ),
    create: (data: RunCreate) =>
      request<Run>("/runs", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    stop: (runId: string) =>
      request<Run>(`/runs/${runId}/stop`, {
        method: "POST",
      }),
  },
}
