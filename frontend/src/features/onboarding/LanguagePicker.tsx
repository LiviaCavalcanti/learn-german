/**
 * Landing page: choose what you want to learn (target language) and which
 * language you already speak (native/explanation language). Shown by App when no
 * target is selected. Writing the choice re-renders App into the main workbench.
 */
import { useEffect, useState } from 'react'
import { useLanguage } from '../../contexts/LanguageContext'
import { Button, Card, Field, Select, Spinner, cx } from '../../components/ui'

export default function LanguagePicker() {
  const { languages, ready, native, choose } = useLanguage()
  const [target, setTarget] = useState<string | null>(null)
  const [nativeChoice, setNativeChoice] = useState(native || 'en')

  // Default the native selection to the first native option once loaded.
  useEffect(() => {
    if (languages && !languages.natives.some((n) => n.code === nativeChoice)) {
      setNativeChoice(languages.natives[0]?.code ?? 'en')
    }
  }, [languages, nativeChoice])

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner />
      </div>
    )
  }

  const targets = languages?.targets ?? []
  const natives = languages?.natives ?? []

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper p-6">
      <div className="w-full max-w-2xl space-y-8">
        <header className="text-center">
          <div className="font-serif text-4xl font-semibold">Sprachheft</div>
          <p className="mt-2 text-muted">Choose what you want to learn.</p>
        </header>

        {targets.length === 0 ? (
          <Card className="p-6 text-center text-sm text-muted">
            No languages are available yet. Make sure the backend is running and has content under
            <code className="mx-1">content/&lt;lang&gt;/</code>.
          </Card>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {targets.map((t) => (
              <button
                key={t.code}
                type="button"
                onClick={() => setTarget(t.code)}
                className={cx(
                  'rounded-xl border p-4 text-left transition',
                  target === t.code
                    ? 'border-accent bg-accent-soft'
                    : 'border-line bg-card hover:border-accent/60 hover:bg-accent-soft/40',
                )}
              >
                <div className="font-serif text-xl">{t.endonym}</div>
                <div className="text-sm text-muted">{t.name}</div>
                <div className="mt-2 text-xs uppercase tracking-wide text-muted">
                  {t.level_framework}
                </div>
              </button>
            ))}
          </div>
        )}

        <Card className="space-y-4 p-5">
          <Field label="I already speak">
            <Select value={nativeChoice} onChange={(e) => setNativeChoice(e.target.value)}>
              {natives.map((n) => (
                <option key={n.code} value={n.code}>
                  {n.name}
                </option>
              ))}
            </Select>
          </Field>
          <p className="text-xs text-muted">
            Explanations, meanings and feedback are written in this language.
          </p>
          <Button
            className="w-full"
            disabled={!target}
            onClick={() => target && choose(target, nativeChoice)}
          >
            Start learning
          </Button>
        </Card>
      </div>
    </div>
  )
}
