import { Moon, Sun, Monitor } from "lucide-react"
import { useTheme } from "@/context/theme-context"
import { cn } from "@/lib/utils"

export function SettingsPage() {
  const { theme, setTheme } = useTheme()

  const themeOptions = [
    { value: "light" as const, label: "Light", icon: Sun },
    { value: "dark" as const, label: "Dark", icon: Moon },
    { value: "system" as const, label: "System", icon: Monitor },
  ]

  return (
    <div className="max-w-2xl">
      <h1 className="text-lg font-semibold mb-6">Settings</h1>

      <section className="mb-8">
        <h2 className="text-sm font-semibold mb-1">General</h2>
        <p className="text-xs text-muted-foreground mb-4">Basic workspace configuration</p>
        <div className="bg-card p-4 space-y-4 pixel-border">
          <div>
            <label className="block text-sm font-medium mb-1.5">Workspace Name</label>
            <input
              type="text"
              defaultValue="AutoAI"
              className="w-full border-2 border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring font-mono"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Default Agent Timeout (seconds)</label>
            <input
              type="number"
              defaultValue={300}
              className="w-full border-2 border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring font-mono"
            />
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-sm font-semibold mb-1">Appearance</h2>
        <p className="text-xs text-muted-foreground mb-4">Customize how AutoAI looks</p>
        <div className="bg-card p-4 pixel-border">
          <label className="block text-sm font-medium mb-3">Theme</label>
          <div className="flex gap-2">
            {themeOptions.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                onClick={() => setTheme(value)}
                className={cn(
                  "flex flex-1 flex-col items-center gap-2 border-2 p-3 text-xs transition-colors",
                  theme === value
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-border text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <Icon className="h-5 w-5" />
                {label}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-sm font-semibold mb-1">Runtime</h2>
        <p className="text-xs text-muted-foreground mb-4">Agent runtime configuration</p>
        <div className="bg-card p-4 space-y-4 pixel-border">
          <div>
            <label className="block text-sm font-medium mb-1.5">Max Concurrent Agents</label>
            <input
              type="number"
              defaultValue={8}
              className="w-full border-2 border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring font-mono"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Log Level</label>
            <select className="w-full border-2 border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring font-mono">
              <option value="debug">Debug</option>
              <option value="info" selected>Info</option>
              <option value="warn">Warn</option>
              <option value="error">Error</option>
            </select>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium">Auto-restart on failure</label>
              <p className="text-xs text-muted-foreground">Automatically restart agents that crash</p>
            </div>
            <button className="relative inline-flex h-5 w-9 items-center bg-primary transition-colors border-2 border-primary">
              <span className="inline-block h-3.5 w-3.5 translate-x-4 bg-white" />
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}
