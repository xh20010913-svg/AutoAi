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
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-lg font-semibold">Settings</h1>
        <span className="text-[10px] font-mono text-muted-foreground/40 tracking-wider uppercase">// configuration</span>
      </div>

      <section className="mb-8">
        <div className="flex items-center gap-2 mb-1">
          <h2 className="text-sm font-semibold">General</h2>
          <div className="flex-1 h-px bg-gradient-to-r from-border to-transparent" />
        </div>
        <p className="text-xs text-muted-foreground mb-4 font-mono">Basic workspace configuration</p>
        <div className="bg-card p-4 space-y-4 pixel-border relative">
          <div className="absolute top-0 left-0 w-[6px] h-[6px] border-t-2 border-l-2 border-primary/30" />
          <div className="absolute bottom-0 right-0 w-[6px] h-[6px] border-b-2 border-r-2 border-primary/30" />
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
        <div className="flex items-center gap-2 mb-1">
          <h2 className="text-sm font-semibold">Appearance</h2>
          <div className="flex-1 h-px bg-gradient-to-r from-border to-transparent" />
        </div>
        <p className="text-xs text-muted-foreground mb-4 font-mono">Customize how AutoAI looks</p>
        <div className="bg-card p-4 pixel-border relative">
          <div className="absolute top-0 left-0 w-[6px] h-[6px] border-t-2 border-l-2 border-primary/30" />
          <div className="absolute bottom-0 right-0 w-[6px] h-[6px] border-b-2 border-r-2 border-primary/30" />
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
        <div className="flex items-center gap-2 mb-1">
          <h2 className="text-sm font-semibold">Runtime</h2>
          <div className="flex-1 h-px bg-gradient-to-r from-border to-transparent" />
        </div>
        <p className="text-xs text-muted-foreground mb-4 font-mono">Agent runtime configuration</p>
        <div className="bg-card p-4 space-y-4 pixel-border relative">
          <div className="absolute top-0 left-0 w-[6px] h-[6px] border-t-2 border-l-2 border-primary/30" />
          <div className="absolute bottom-0 right-0 w-[6px] h-[6px] border-b-2 border-r-2 border-primary/30" />
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
