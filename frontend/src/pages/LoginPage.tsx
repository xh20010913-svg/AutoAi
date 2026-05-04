import { useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "@/context/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      await login(username, password)
      navigate("/")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen w-full items-center justify-center bg-background">
      <div className="w-full max-w-sm mx-4">
        <div className="pixel-border bg-card p-8">
          {/* Logo */}
          <div className="flex items-center justify-center gap-2.5 mb-8">
            <div className="relative h-8 w-8">
              <div className="grid grid-cols-4 gap-[1px] h-full w-full">
                <div className="bg-primary" />
                <div className="bg-primary" />
                <div className="bg-primary/60" />
                <div className="bg-transparent" />
                <div className="bg-primary" />
                <div className="bg-primary/80" />
                <div className="bg-primary/40" />
                <div className="bg-primary/60" />
                <div className="bg-primary/60" />
                <div className="bg-primary/40" />
                <div className="bg-primary/80" />
                <div className="bg-primary" />
                <div className="bg-transparent" />
                <div className="bg-primary/60" />
                <div className="bg-primary" />
                <div className="bg-primary" />
              </div>
            </div>
            <div>
              <span className="text-lg font-bold text-primary tracking-widest uppercase">
                AutoAI
              </span>
            </div>
          </div>

          <h1 className="text-sm font-bold text-center text-foreground tracking-[0.15em] uppercase mb-6">
            Login
          </h1>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && (
              <div className="pixel-border-sm bg-destructive/10 border-destructive px-3 py-2 text-xs text-destructive">
                {error}
              </div>
            )}

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                placeholder="Enter username"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="Enter password"
              />
            </div>

            <Button type="submit" disabled={loading} className="mt-2">
              {loading ? "Logging in..." : "Login"}
            </Button>
          </form>

          <div className="mt-6 text-center text-xs text-muted-foreground">
            Don't have an account?{" "}
            <Link to="/register" className="text-primary hover:underline">
              Register
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
