import { createContext, useContext, useState, type ReactNode } from "react"
import { translations, type Locale, type TranslationKey } from "@/lib/i18n"

interface I18nContextValue {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: TranslationKey) => string
}

const I18nContext = createContext<I18nContextValue | null>(null)

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(() => {
    const saved = localStorage.getItem("autoai-locale")
    if (saved === "zh" || saved === "en") return saved
    return navigator.language.startsWith("zh") ? "zh" : "en"
  })

  function setLocaleAndSave(l: Locale) {
    setLocale(l)
    localStorage.setItem("autoai-locale", l)
  }

  function t(key: TranslationKey): string {
    return translations[locale][key] ?? translations.en[key] ?? key
  }

  return (
    <I18nContext.Provider value={{ locale, setLocale: setLocaleAndSave, t }}>
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n() {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error("useI18n must be used within I18nProvider")
  return ctx
}
