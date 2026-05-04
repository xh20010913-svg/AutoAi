import { BrowserRouter, Routes, Route } from "react-router-dom"
import { ThemeProvider } from "@/context/theme-context"
import { AppLayout } from "@/components/layout/AppLayout"
import { BoardPage } from "@/pages/BoardPage"
import { AgentsPage } from "@/pages/AgentsPage"
import { RuntimePage } from "@/pages/RuntimePage"
import { ModelsPage } from "@/pages/ModelsPage"
import { SettingsPage } from "@/pages/SettingsPage"
import { OfficePage } from "@/pages/OfficePage"

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<BoardPage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/office" element={<OfficePage />} />
            <Route path="/runtime" element={<RuntimePage />} />
            <Route path="/models" element={<ModelsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
