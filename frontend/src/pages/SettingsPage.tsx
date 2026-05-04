import { Moon, Sun, Monitor, Globe } from "lucide-react"
import { useTheme } from "@/context/theme-context"
import { cn } from "@/lib/utils"
import { useTranslation } from "@/hooks/useLanguage"

export function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const { t, currentLanguage, changeLanguage } = useTranslation()

  const themeOptions = [
    { value: "light" as const, labelKey: "settings.themeLight", icon: Sun },
    { value: "dark" as const, labelKey: "settings.themeDark", icon: Moon },
    { value: "system" as const, labelKey: "settings.themeSystem", icon: Monitor },
  ]

  const languageOptions = [
    { value: "zh", label: t("settings.languageChinese") },
    { value: "en", label: t("settings.languageEnglish") },
  ]

  return (
    <div className="max-w-2xl">
      <h1 className="text-lg font-semibold mb-6">{t("settings.title")}</h1>

      <section className="mb-8">
        <h2 className="text-sm font-semibold mb-1">{t("settings.general")}</h2>
        <p className="text-xs text-muted-foreground mb-4">{t("settings.generalDesc")}</p>
        <div className="bg-card p-4 space-y-4 pixel-border">
          <div>
            <label className="block text-sm font-medium mb-1.5">{t("settings.workspaceName")}</label>
            <input type="text" defaultValue="AutoAI" className="w-full border-2 border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring font-mono" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">{t("settings.defaultTimeout")}</label>
            <input type="number" defaultValue={300} className="w-full border-2 border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring font-mono" />
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-sm font-semibold mb-1">{t("settings.appearance")}</h2>
        <p className="text-xs text-muted-foreground mb-4">{t("settings.appearanceDesc")}</p>
        <div className="bg-card p-4 pixel-border">
          <label className="block text-sm font-medium mb-3">{t("settings.theme")}</label>
          <div className="flex gap-2">
            {themeOptions.map(({ value, labelKey, icon: Icon }) => (
              <button key={value} onClick={() => setTheme(value)} className={cn("flex flex-1 flex-col items-center gap-2 border-2 p-3 text-xs transition-colors", theme === value ? "border-primary bg-primary/5 text-primary" : "border-border text-muted-foreground hover:bg-accent hover:text-accent-foreground")}>
                <Icon className="h-5 w-5" />{t(labelKey)}
              </button>
            ))}
          </div>

          <div className="mt-6">
            <label className="flex items-center gap-2 text-sm font-medium mb-3">
              <Globe className="h-4 w-4" />{t("settings.language")}
            </label>
            <p className="text-xs text-muted-foreground mb-3">{t("settings.languageDesc")}</p>
            <div className="flex gap-2">
              {languageOptions.map(({ value, label }) => (
                <button key={value} onClick={() => changeLanguage(value)} className={cn("flex flex-1 items-center justify-center gap-2 border-2 p-3 text-xs transition-colors", currentLanguage === value || currentLanguage.startsWith(value) ? "border-primary bg-primary/5 text-primary" : "border-border text-muted-foreground hover:bg-accent hover:text-accent-foreground")}>
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-sm font-semibold mb-1">{t("settings.runtime")}</h2>
        <p className="text-xs text-muted-foreground mb-4">{t("settings.runtimeDesc")}</p>
        <div className="bg-card p-4 space-y-4 pixel-border">
          <div>
            <label className="block text-sm font-medium mb-1.5">{t("settings.maxConcurrentAgents")}</label>
            <input type="number" defaultValue={8} className="w-full border-2 border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring font-mono" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">{t("settings.logLevel")}</label>
            <select className="w-full border-2 border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring font-mono">
              <option value="debug">{t("settings.logLevelDebug")}</option>
              <option value="info" selected>{t("settings.logLevelInfo")}</option>
              <option value="warn">{t("settings.logLevelWarn")}</option>
              <option value="error">{t("settings.logLevelError")}</option>
            </select>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium">{t("settings.autoRestart")}</label>
              <p className="text-xs text-muted-foreground">{t("settings.autoRestartDesc")}</p>
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
