import { BrowserRouter, Routes, Route } from "react-router-dom"
import { ThemeProvider } from "@/context/theme-context"
import { I18nProvider } from "@/context/i18n-context"
import { AppLayout } from "@/components/layout/AppLayout"
import { BoardPage } from "@/pages/BoardPage"
import { AgentsPage } from "@/pages/AgentsPage"
import { RuntimePage } from "@/pages/RuntimePage"
import { ModelsPage } from "@/pages/ModelsPage"
import { SettingsPage } from "@/pages/SettingsPage"

function App() {
  return (
    <ThemeProvider>
      <I18nProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<BoardPage />} />
              <Route path="/agents" element={<AgentsPage />} />
              <Route path="/runtime" element={<RuntimePage />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </I18nProvider>
    </ThemeProvider>
  )
}

export default App
