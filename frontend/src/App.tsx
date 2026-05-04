import { BrowserRouter, Routes, Route } from "react-router-dom"
import { ThemeProvider } from "@/context/theme-context"
import { AuthProvider } from "@/context/auth-context"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { AppLayout } from "@/components/layout/AppLayout"
import { BoardPage } from "@/pages/BoardPage"
import { AgentsPage } from "@/pages/AgentsPage"
import { RuntimePage } from "@/pages/RuntimePage"
import { ModelsPage } from "@/pages/ModelsPage"
import { SettingsPage } from "@/pages/SettingsPage"
import { LoginPage } from "@/pages/LoginPage"
import { RegisterPage } from "@/pages/RegisterPage"

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<BoardPage />} />
                <Route path="/agents" element={<AgentsPage />} />
                <Route path="/runtime" element={<RuntimePage />} />
                <Route path="/models" element={<ModelsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
