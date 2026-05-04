import axios from "axios"
import { getToken } from "@/context/auth-context"

const API_BASE = "http://localhost:18765/api/v1"

export const axiosInstance = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
})

// Request interceptor — attach JWT token to every request
axiosInstance.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — handle 401 by clearing token and redirecting to login
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("auth_token")
      if (window.location.pathname !== "/login" && window.location.pathname !== "/register") {
        window.location.href = "/login"
      }
    }
    return Promise.reject(error)
  },
)

// --- Types ---

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

export const api = {
  projects: {
    list: () =>
      axiosInstance.get<{ projects: Project[]; total: number }>("/projects").then((r) => r.data),
  },

  tasks: {
    list: (projectId: string, status?: string) =>
      axiosInstance
        .get<{ tasks: Task[]; total: number }>(`/projects/${projectId}/tasks`, {
          params: status ? { status } : undefined,
        })
        .then((r) => r.data),

    create: (projectId: string, data: TaskCreate) =>
      axiosInstance.post<Task>(`/projects/${projectId}/tasks`, data).then((r) => r.data),

    update: (projectId: string, taskId: string, data: TaskUpdate) =>
      axiosInstance.patch<Task>(`/projects/${projectId}/tasks/${taskId}`, data).then((r) => r.data),

    delete: (projectId: string, taskId: string) =>
      axiosInstance.delete(`/projects/${projectId}/tasks/${taskId}`).then(() => undefined),
  },
}
