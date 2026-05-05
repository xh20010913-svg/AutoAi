const API_BASE = "http://localhost:18765/api/v1"

export type TaskStatus = "todo" | "in_progress" | "in_review" | "done" | "blocked"
export type TaskPriority = "high" | "medium" | "low" | "none"

export interface Task {
  id: string
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  assignee: string
  project_id: string | null
  position: number
  blocked_reason: string
  created_at: string
  updated_at: string
  depends_on_ids: string[]
  depended_by_ids: string[]
}

export interface TaskCreate {
  title: string
  description?: string
  priority?: TaskPriority
  assignee?: string
  depends_on_ids?: string[]
}

export interface TaskUpdate {
  title?: string
  description?: string
  status?: TaskStatus
  priority?: TaskPriority
  assignee?: string
  position?: number
}

export interface GraphNode {
  id: string
  title: string
  status: string
}

export interface GraphEdge {
  source: string
  target: string
}

export interface DependencyGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
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
  tasks: {
    list: (status?: string) =>
      request<Task[]>(`/tasks${status ? `?status=${encodeURIComponent(status)}` : ""}`),

    create: (data: TaskCreate) =>
      request<Task>("/tasks", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    get: (taskId: string) => request<Task>(`/tasks/${taskId}`),

    update: (taskId: string, data: TaskUpdate) =>
      request<Task>(`/tasks/${taskId}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),

    delete: (taskId: string) =>
      request<void>(`/tasks/${taskId}`, { method: "DELETE" }),

    updateStatus: (taskId: string, status: TaskStatus, position?: number) =>
      request<Task>(`/tasks/${taskId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status, position }),
      }),

    reorder: (taskIds: string[]) =>
      request<Task[]>("/tasks/reorder", {
        method: "POST",
        body: JSON.stringify({ task_ids: taskIds }),
      }),

    // Dependency operations
    dependencyGraph: () => request<DependencyGraph>("/tasks/dependency-graph"),

    addDependency: (taskId: string, dependsOnId: string) =>
      request<Task>(`/tasks/${taskId}/dependencies`, {
        method: "POST",
        body: JSON.stringify({ depends_on_id: dependsOnId }),
      }),

    removeDependency: (taskId: string, dependsOnId: string) =>
      request<Task>(`/tasks/${taskId}/dependencies/${dependsOnId}`, {
        method: "DELETE",
      }),
  },
}
