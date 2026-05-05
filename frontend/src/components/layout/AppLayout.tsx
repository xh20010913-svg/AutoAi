import { useEffect } from "react"
import { Outlet } from "react-router-dom"
import { Sidebar } from "./Sidebar"
import { Topbar } from "./Topbar"
import { connectWebSocket } from "@/lib/ws"
import { showToast } from "@/lib/toast"

export function AppLayout() {
  useEffect(() => {
    const unsubscribe = connectWebSocket((data) => {
      if (data.event === "notification") {
        const payload = data.data ?? {}
        showToast(payload.message ?? "New notification", payload.level ?? "info")
      }
    })
    return unsubscribe
  }, [])

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-auto p-6 relative">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
