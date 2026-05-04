import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react"

interface User {
  id: string
  username: string
  email: string
  created_at: string
}

interface AuthContextValue {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const TOKEN_KEY = "auth_token"

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const fetchUser = useCallback(async (authToken: string) => {
    const res = await fetch("http://localhost:18765/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${authToken}` },
    })
    if (!res.ok) throw new Error("Invalid token")
    return res.json() as Promise<User>
  }, [])

  useEffect(() => {
    if (!token) {
      setIsLoading(false)
      return
    }
    fetchUser(token)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
      })
      .finally(() => setIsLoading(false))
  }, [token, fetchUser])

  const login = async (username: string, password: string) => {
    const res = await fetch("http://localhost:18765/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
      const body = await res.text()
      throw new Error(body || "Login failed")
    }
    const data: { access_token: string; token_type: string } = await res.json()
    localStorage.setItem(TOKEN_KEY, data.access_token)
    setToken(data.access_token)
    const me = await fetchUser(data.access_token)
    setUser(me)
  }

  const register = async (username: string, email: string, password: string) => {
    const res = await fetch("http://localhost:18765/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    })
    if (!res.ok) {
      const body = await res.text()
      throw new Error(body || "Registration failed")
    }
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
