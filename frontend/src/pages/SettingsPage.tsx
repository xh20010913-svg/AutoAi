import { Moon, Sun, Monitor, Plus, Pencil, Trash2, X, Check } from "lucide-react"
import { useTheme } from "@/context/theme-context"
import { useI18n } from "@/context/i18n-context"
import { cn } from "@/lib/utils"
import { useState, useEffect, useCallback, type FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api, type Role, type RoleCreate } from "@/lib/api"

type Tab = "general" | "roles"

export function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const { t, locale, setLocale } = useI18n()
  const [tab, setTab] = useState<Tab>("general")
  const [roles, setRoles] = useState<Role[]>([])
  const [loadingRoles, setLoadingRoles] = useState(false)
  const [editingRole, setEditingRole] = useState<Role | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)

  const fetchRoles = useCallback(async () => {
    setLoadingRoles(true)
    try {
      const res = await api.roles.list()
      setRoles(res.roles)
    } catch (err) {
      console.error("Failed to fetch roles:", err)
    } finally {
      setLoadingRoles(false)
    }
  }, [])

  useEffect(() => {
    if (tab === "roles") fetchRoles()
  }, [tab, fetchRoles])

  const themeOptions = [
    { value: "light" as const, label: t("settings.themeLight"), icon: Sun },
    { value: "dark" as const, label: t("settings.themeDark"), icon: Moon },
    { value: "system" as const, label: t("settings.themeSystem"), icon: Monitor },
  ]

  const tabs: { value: Tab; label: string }[] = [
    { value: "general", label: t("settings.general") },
    { value: "roles", label: t("settings.roles") },
  ]

  return (
    <div className="max-w-2xl">
      <h1 className="text-lg font-semibold mb-6">{t("settings.title")}</h1>

      <div className="flex gap-1 mb-6 border-b-2 border-border">
        {tabs.map((tb) => (
          <button
            key={tb.value}
            onClick={() => setTab(tb.value)}
            className={cn(
              "px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-[2px]",
              tab === tb.value
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {tb.label}
          </button>
        ))}
      </div>

      {tab === "general" && (
        <>
          <section className="mb-8">
            <h2 className="text-sm font-semibold mb-1">{t("settings.general")}</h2>
            <p className="text-xs text-muted-foreground mb-4">{t("settings.generalDesc")}</p>
            <div className="bg-card p-4 space-y-4 pixel-border">
              <div>
                <label className="block text-sm font-medium mb-1.5">{t("settings.workspaceName")}</label>
                <input
                  type="text"
                  defaultValue="AutoAI"
                  className="w-full border-2 border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring font-mono"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5">{t("settings.agentTimeout")}</label>
                <input
                  type="number"
                  defaultValue={300}
                  className="w-full border-2 border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring font-mono"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-3">Language</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setLocale("en")}
                    className={cn(
                      "flex-1 border-2 p-2 text-xs transition-colors",
                      locale === "en"
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-border text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    )}
                  >
                    English
                  </button>
                  <button
                    onClick={() => setLocale("zh")}
                    className={cn(
                      "flex-1 border-2 p-2 text-xs transition-colors",
                      locale === "zh"
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-border text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    )}
                  >
                    中文
                  </button>
                </div>
              </div>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-sm font-semibold mb-1">{t("settings.appearance")}</h2>
            <p className="text-xs text-muted-foreground mb-4">{t("settings.appearanceDesc")}</p>
            <div className="bg-card p-4 pixel-border">
              <label className="block text-sm font-medium mb-3">{t("settings.theme")}</label>
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
            <h2 className="text-sm font-semibold mb-1">{t("settings.runtime")}</h2>
            <p className="text-xs text-muted-foreground mb-4">{t("settings.runtimeDesc")}</p>
            <div className="bg-card p-4 space-y-4 pixel-border">
              <div>
                <label className="block text-sm font-medium mb-1.5">{t("settings.maxConcurrent")}</label>
                <input
                  type="number"
                  defaultValue={8}
                  className="w-full border-2 border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring font-mono"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5">{t("settings.logLevel")}</label>
                <select className="w-full border-2 border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring font-mono">
                  <option value="debug">Debug</option>
                  <option value="info" selected>Info</option>
                  <option value="warn">Warn</option>
                  <option value="error">Error</option>
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
        </>
      )}

      {tab === "roles" && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold mb-1">{t("settings.roles")}</h2>
              <p className="text-xs text-muted-foreground">{t("settings.rolesDesc")}</p>
            </div>
            <Button size="sm" onClick={() => { setShowCreateForm(true); setEditingRole(null) }}>
              <Plus className="h-3.5 w-3.5" />
              {t("settings.addRole")}
            </Button>
          </div>

          {(showCreateForm || editingRole) && (
            <RoleForm
              role={editingRole}
              onSaved={(role) => {
                if (editingRole) {
                  setRoles((prev) => prev.map((r) => (r.id === role.id ? role : r)))
                } else {
                  setRoles((prev) => [...prev, role])
                }
                setShowCreateForm(false)
                setEditingRole(null)
              }}
              onCancel={() => { setShowCreateForm(false); setEditingRole(null) }}
            />
          )}

          <div className="space-y-2">
            {loadingRoles ? (
              <div className="text-sm text-muted-foreground py-8 text-center">Loading...</div>
            ) : roles.length === 0 && !showCreateForm ? (
              <div className="border-2 border-dashed border-border p-8 text-center pixel-border">
                <p className="text-sm text-muted-foreground">{t("settings.noRoles")}</p>
              </div>
            ) : (
              roles.map((role) => (
                <div key={role.id} className="bg-card p-3 pixel-border-sm flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-medium">{role.name}</h3>
                    {role.description && (
                      <p className="text-xs text-muted-foreground mt-0.5">{role.description}</p>
                    )}
                    <div className="flex gap-3 mt-1.5 text-xs text-muted-foreground">
                      {role.budget_level && <span>Budget: {role.budget_level}</span>}
                      {role.authority && <span>Authority: {role.authority}</span>}
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <button
                      className="p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground border border-transparent hover:border-border"
                      onClick={() => { setEditingRole(role); setShowCreateForm(false) }}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                    <button
                      className="p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive border border-transparent hover:border-border"
                      onClick={async () => {
                        await api.roles.delete(role.id)
                        setRoles((prev) => prev.filter((r) => r.id !== role.id))
                      }}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      )}
    </div>
  )
}

interface RoleFormProps {
  role: Role | null
  onSaved: (role: Role) => void
  onCancel: () => void
}

function RoleForm({ role, onSaved, onCancel }: RoleFormProps) {
  const { t } = useI18n()
  const [name, setName] = useState(role?.name ?? "")
  const [description, setDescription] = useState(role?.description ?? "")
  const [budgetLevel, setBudgetLevel] = useState(role?.budget_level ?? "")
  const [authority, setAuthority] = useState(role?.authority ?? "")
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setSaving(true)
    try {
      const data: RoleCreate = {
        name: name.trim(),
        description: description.trim() || undefined,
        budget_level: budgetLevel.trim() || undefined,
        authority: authority.trim() || undefined,
      }
      let saved: Role
      if (role) {
        saved = await api.roles.update(role.id, data)
      } else {
        saved = await api.roles.create(data)
      }
      onSaved(saved)
    } catch (err) {
      console.error("Failed to save role:", err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-card p-4 mb-4 pixel-border space-y-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold">
          {role ? t("settings.editRole") : t("settings.addRole")}
        </h3>
        <button type="button" onClick={onCancel} className="p-1 text-muted-foreground hover:text-foreground">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div>
        <Label htmlFor="role-name">{t("settings.roleName")}</Label>
        <Input
          id="role-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t("settings.roleNamePlaceholder")}
          required
          className="mt-1"
        />
      </div>

      <div>
        <Label htmlFor="role-desc">{t("settings.roleDesc")}</Label>
        <Input
          id="role-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={t("settings.roleDescPlaceholder")}
          className="mt-1"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label htmlFor="role-budget">{t("settings.budgetLevel")}</Label>
          <Input
            id="role-budget"
            value={budgetLevel}
            onChange={(e) => setBudgetLevel(e.target.value)}
            placeholder="low / medium / high"
            className="mt-1"
          />
        </div>
        <div>
          <Label htmlFor="role-authority">{t("settings.authority")}</Label>
          <Input
            id="role-authority"
            value={authority}
            onChange={(e) => setAuthority(e.target.value)}
            placeholder="readonly / standard / admin"
            className="mt-1"
          />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel}>
          {t("common.cancel")}
        </Button>
        <Button type="submit" disabled={saving || !name.trim()}>
          {saving ? <><Check className="h-3.5 w-3.5" /> {t("common.saving")}</> : <><Check className="h-3.5 w-3.5" /> {t("common.save")}</>}
        </Button>
      </div>
    </form>
  )
}
