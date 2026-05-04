import { useState, type FormEvent } from "react"
import { cn } from "@/lib/utils"

interface LoginFormProps {
  onSubmit?: (email: string, password: string) => void | Promise<void>
  error?: string
}

export function LoginForm({ onSubmit, error }: LoginFormProps) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [emailError, setEmailError] = useState("")
  const [passwordError, setPasswordError] = useState("")
  const [submitting, setSubmitting] = useState(false)

  function validate(): boolean {
    let valid = true
    setEmailError("")
    setPasswordError("")

    if (!email.trim()) {
      setEmailError("Email is required")
      valid = false
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailError("Invalid email format")
      valid = false
    }

    if (!password) {
      setPasswordError("Password is required")
      valid = false
    } else if (password.length < 6) {
      setPasswordError("Password must be at least 6 characters")
      valid = false
    }

    return valid
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!validate()) return

    setSubmitting(true)
    try {
      await onSubmit?.(email, password)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4 p-6 pixel-border bg-card">
      <h2 className="text-lg font-semibold text-card-foreground">Login</h2>

      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      <div className="flex flex-col gap-1">
        <label htmlFor="email" className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Email
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={cn(
            "border-2 bg-background px-3 py-2 text-sm outline-none transition-colors",
            emailError ? "border-destructive" : "border-border focus:border-primary"
          )}
          placeholder="you@example.com"
        />
        {emailError && <p className="text-xs text-destructive">{emailError}</p>}
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="password" className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={cn(
            "border-2 bg-background px-3 py-2 text-sm outline-none transition-colors",
            passwordError ? "border-destructive" : "border-border focus:border-primary"
          )}
          placeholder="••••••••"
        />
        {passwordError && <p className="text-xs text-destructive">{passwordError}</p>}
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 transition-opacity disabled:opacity-50 pixel-border-sm"
      >
        {submitting ? "Signing in..." : "Sign In"}
      </button>
    </form>
  )
}
