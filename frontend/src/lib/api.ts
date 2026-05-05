import axios from "axios"

const API_BASE = "http://localhost:18765/api/v1"

// ── Axios instance ──────────────────────────────────────────────

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
})

// Attach JWT token to every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 → redirect to login
apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token")
      localStorage.removeItem("user")
      if (window.location.pathname !== "/login") {
        window.location.href = "/login"
      }
    }
    return Promise.reject(error)
  },
)

// ── Types ───────────────────────────────────────────────────────

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
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  title: string
  description?: string
  status?: TaskStatus
  priority?: TaskPriority
  assignee?: string
  position?: number
}

export interface TaskUpdate {
  title?: string
  description?: string
  status?: TaskStatus
  priority?: TaskPriority
  assignee?: string
  position?: number
}

// ── Auth API ────────────────────────────────────────────────────

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user?: { id: string; username: string; email: string }
}

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>("/auth/login", data)
    return res.data
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>("/auth/register", data)
    return res.data
  },
}

// ── Agent types ─────────────────────────────────────────────────

export interface Agent {
  id: string
  name: string
  role: string
  model: string
  provider_id: string | null
  status: string
  system_prompt: string
  created_at: string
  updated_at: string
}

export const agentApi = {
  list: async (): Promise<Agent[]> => {
    const res = await apiClient.get<Agent[]>("/agents")
    return res.data
  },

  get: async (agentId: string): Promise<Agent> => {
    const res = await apiClient.get<Agent>(`/agents/${agentId}`)
    return res.data
  },
}

// ── Task API ────────────────────────────────────────────────────

export const taskApi = {
  list: async (status?: string): Promise<Task[]> => {
    const params = status ? { status } : undefined
    const res = await apiClient.get<Task[]>("/tasks", { params })
    return res.data
  },

  get: async (taskId: string): Promise<Task> => {
    const res = await apiClient.get<Task>(`/tasks/${taskId}`)
    return res.data
  },

  create: async (data: TaskCreate): Promise<Task> => {
    const res = await apiClient.post<Task>("/tasks", data)
    return res.data
  },

  update: async (taskId: string, data: TaskUpdate): Promise<Task> => {
    const res = await apiClient.put<Task>(`/tasks/${taskId}`, data)
    return res.data
  },

  updateStatus: async (taskId: string, status: string, position?: number): Promise<Task> => {
    const res = await apiClient.patch<Task>(`/tasks/${taskId}/status`, { status, position })
    return res.data
  },

  delete: async (taskId: string): Promise<void> => {
    await apiClient.delete(`/tasks/${taskId}`)
  },
}
