/**
 * Global language selection: the target language being learned and the native
 * (explanation) language. Persisted to localStorage and threaded into every
 * language-scoped API call (via setApiLanguage) and speech output (setSpeechLang).
 *
 * The app has no other global state; this is the single provider that wraps the
 * router so the landing picker and every page can read/update the selection.
 */
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, getApiLanguage, setApiLanguage } from '../lib/api'
import { setSpeechLang } from '../lib/pronunciation'
import type { LanguageOption, LanguagesResponse } from '../lib/types'

const TARGET_KEY = 'sprachheft.lang.target'
const NATIVE_KEY = 'sprachheft.lang.native'

function readStored(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

// Prime the API/speech language from storage before any component renders, so
// early requests from returning users use the right language immediately.
setApiLanguage(readStored(TARGET_KEY) || 'de', readStored(NATIVE_KEY) || 'en')

interface LanguageContextValue {
  /** Selected target language code, or null until the learner has chosen one. */
  target: string | null
  /** Native/explanation language code (defaults to English). */
  native: string
  /** Metadata for available targets + native options (null until loaded). */
  languages: LanguagesResponse | null
  /** True once the language list has been fetched. */
  ready: boolean
  /** Profile of the currently selected target, if any. */
  targetProfile: LanguageOption | undefined
  /** Choose the target + native language. */
  choose: (target: string, native: string) => void
  /** Clear the target selection to return to the picker. */
  reset: () => void
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLanguage must be used within a LanguageProvider')
  return ctx
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [languages, setLanguages] = useState<LanguagesResponse | null>(null)
  const [ready, setReady] = useState(false)
  const [target, setTarget] = useState<string | null>(() => readStored(TARGET_KEY))
  const [native, setNative] = useState<string>(() => readStored(NATIVE_KEY) || 'en')

  // Fetch the language registry once.
  useEffect(() => {
    let cancelled = false
    api
      .languages()
      .then((data) => {
        if (cancelled) return
        setLanguages(data)
        // If the stored target isn't actually available, force re-selection.
        setTarget((current) =>
          current && data.targets.some((t) => t.code === current) ? current : null,
        )
      })
      .catch(() => {
        /* leave languages null; picker will show a retry-friendly message */
      })
      .finally(() => {
        if (!cancelled) setReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const targetProfile = useMemo(
    () => languages?.targets.find((t) => t.code === target),
    [languages, target],
  )

  // Keep the API + speech language in sync with the selection.
  useEffect(() => {
    setApiLanguage(target || 'de', native)
    setSpeechLang(targetProfile?.voice || `${target || 'de'}-${(target || 'de').toUpperCase()}`)
  }, [target, native, targetProfile])

  function choose(nextTarget: string, nextNative: string) {
    const voice =
      languages?.targets.find((t) => t.code === nextTarget)?.voice ||
      `${nextTarget}-${nextTarget.toUpperCase()}`
    setApiLanguage(nextTarget, nextNative)
    setSpeechLang(voice)
    try {
      localStorage.setItem(TARGET_KEY, nextTarget)
      localStorage.setItem(NATIVE_KEY, nextNative)
    } catch {
      /* ignore unavailable storage */
    }
    setTarget(nextTarget)
    setNative(nextNative)
  }

  function reset() {
    try {
      localStorage.removeItem(TARGET_KEY)
    } catch {
      /* ignore */
    }
    setTarget(null)
  }

  const value: LanguageContextValue = {
    target,
    native,
    languages,
    ready,
    targetProfile,
    choose,
    reset,
  }

  // Ensure the module-level API language reflects the current selection even on
  // the very first synchronous render (before effects run).
  if (getApiLanguage().target !== (target || 'de')) {
    setApiLanguage(target || 'de', native)
  }

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}
