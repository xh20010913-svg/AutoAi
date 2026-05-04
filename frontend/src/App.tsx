import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { ThemeProvider } from "@/context/theme-context"
import { AuthProvider } from "@/context/auth-context"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { ToastContainer } from "@/components/ToastContainer"
import { AppLayout } from "@/components/layout/AppLayout"
import { LoginPage } from "@/pages/LoginPage"
import { RegisterPage } from "@/pages/RegisterPage"
import { BoardPage } from "@/pages/BoardPage"
import { AgentsPage } from "@/pages/AgentsPage"
import { RuntimePage } from "@/pages/RuntimePage"
import { ModelsPage } from "@/pages/ModelsPage"
import { SettingsPage } from "@/pages/SettingsPage"

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<BoardPage />} />
              <Route path="/agents" element={<AgentsPage />} />
              <Route path="/runtime" element={<RuntimePage />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
        <ToastContainer />
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
