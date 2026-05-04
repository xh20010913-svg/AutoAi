import { Navigate, Outlet } from "react-router-dom"
import { useAuth } from "@/context/auth-context"

export function ProtectedRoute() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <div className="text-xs text-muted-foreground tracking-widest uppercase animate-pulse">
          Loading...
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
