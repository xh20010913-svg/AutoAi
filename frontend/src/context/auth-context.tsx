import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react"
import { authApi, type LoginRequest, type RegisterRequest } from "@/lib/api"

interface User {
  id: string
  username: string
  email: string
}

interface AuthContextValue {
  user: User | null
  token: string | null
  loading: boolean
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Restore auth state from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem("token")
    const storedUser = localStorage.getItem("user")
    if (storedToken && storedUser) {
      try {
        setToken(storedToken)
        setUser(JSON.parse(storedUser))
      } catch {
        localStorage.removeItem("token")
        localStorage.removeItem("user")
      }
    }
    setLoading(false)
  }, [])

  const login = useCallback(async (data: LoginRequest) => {
    const res = await authApi.login(data)
    localStorage.setItem("token", res.access_token)
    setToken(res.access_token)
    if (res.user) {
      localStorage.setItem("user", JSON.stringify(res.user))
      setUser(res.user)
    } else {
      // If backend doesn't return user, store username as fallback
      const fallbackUser = { id: "", username: data.username, email: "" }
      localStorage.setItem("user", JSON.stringify(fallbackUser))
      setUser(fallbackUser)
    }
  }, [])

  const register = useCallback(async (data: RegisterRequest) => {
    const res = await authApi.register(data)
    localStorage.setItem("token", res.access_token)
    setToken(res.access_token)
    if (res.user) {
      localStorage.setItem("user", JSON.stringify(res.user))
      setUser(res.user)
    } else {
      const fallbackUser = { id: "", username: data.username, email: data.email }
      localStorage.setItem("user", JSON.stringify(fallbackUser))
      setUser(fallbackUser)
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
