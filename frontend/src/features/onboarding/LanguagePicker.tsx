/**
 * Onboarding wizard shown by App until a target language is selected. Three steps:
 *
 *   1. Welcome   — a warm intro to what Sprachheft does.
 *   2. Choose    — pick a target language (with flags) + the language you speak.
 *   3. Preparing — a short "getting your learning ready" beat, then choose() flips
 *                  App into the main workbench.
 *
 * Only languages the backend reports as available (they have authored content)
 * are offered, so the picker never shows a language you can't actually study.
 */
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useLanguage } from '../../contexts/LanguageContext'
import { Button, Card, Field, Select, Spinner, cx } from '../../components/ui'
import { Flag } from '../../components/Flag'
import type { LanguageOption, NativeOption } from '../../lib/types'

type Step = 'welcome' | 'choose' | 'preparing'

const FEATURES: { title: string; body: string; icon: ReactNode }[] = [
  {
    title: 'Capture anything',
    body: 'Drop in a video, podcast or article — Sprachheft turns it into study material.',
    icon: (
      <>
        <path d="M12 3l9 5-9 5-9-5z" />
        <path d="M3 12l9 5 9-5" />
      </>
    ),
  },
  {
    title: 'AI-built exercises',
    body: 'Vocabulary and grammar drills, tagged by level and generated just for you.',
    icon: <path d="M12 3l1.8 4.7L18.5 9.5 13.8 11.3 12 16l-1.8-4.7L5.5 9.5l4.7-1.8z" />,
  },
  {
    title: 'Practice that sticks',
    body: 'Spaced repetition brings each word back right when you’re about to forget it.',
    icon: (
      <>
        <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
        <path d="M21 3v5h-5" />
        <path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
        <path d="M3 21v-5h5" />
      </>
    ),
  },
  {
    title: 'Instant dictionary',
    body: 'Hover any word for an offline definition — no tab-switching, no interruptions.',
    icon: (
      <>
        <path d="M5 4h11a2 2 0 0 1 2 2v14H7a2 2 0 0 1-2-2z" />
        <path d="M18 20a2 2 0 0 0-2-2H5" />
      </>
    ),
  },
]

const PREPARING_MESSAGES = [
  'Warming up your notebook…',
  'Sharpening your pencils…',
  'Sorting your vocabulary cards…',
  'Almost ready…',
]

export default function LanguagePicker() {
  const { languages, ready, native, choose, reselecting, target: currentTarget } = useLanguage()
  // When switching an already-chosen language, jump straight to the language
  // list; only first-time onboarding replays the welcome intro.
  const [step, setStep] = useState<Step>(reselecting ? 'choose' : 'welcome')
  const [target, setTarget] = useState<string | null>(null)
  const [nativeChoice, setNativeChoice] = useState(native || 'en')

  // Picking the language you're already learning is a no-op switch: skip the
  // "preparing" beat and let choose() drop you back where you left off. A
  // different language gets the preparing screen on the way to its dashboard.
  function handleContinue() {
    if (!target) return
    if (target === currentTarget) {
      choose(target, nativeChoice)
    } else {
      setStep('preparing')
    }
  }

  // Default the native selection to the first native option once loaded.
  useEffect(() => {
    if (languages && !languages.natives.some((n) => n.code === nativeChoice)) {
      setNativeChoice(languages.natives[0]?.code ?? 'en')
    }
  }, [languages, nativeChoice])

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper">
        <Spinner />
      </div>
    )
  }

  const targets = languages?.targets ?? []
  const natives = languages?.natives ?? []
  const chosen = targets.find((t) => t.code === target)

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-paper p-6">
      <Backdrop />
      <div className="relative z-10 w-full max-w-3xl">
        {step === 'welcome' && <Welcome targets={targets} onStart={() => setStep('choose')} />}
        {step === 'choose' && (
          <Choose
            targets={targets}
            natives={natives}
            target={target}
            nativeChoice={nativeChoice}
            onPickTarget={setTarget}
            onPickNative={setNativeChoice}
            onBack={() => setStep('welcome')}
            onContinue={handleContinue}
          />
        )}
        {step === 'preparing' && target && (
          <Preparing
            endonym={chosen?.endonym ?? target}
            onReady={() => choose(target, nativeChoice)}
          />
        )}
      </div>
    </div>
  )
}

function Backdrop() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-accent-soft/60 blur-3xl" />
      <div className="absolute -bottom-28 -right-24 h-80 w-80 rounded-full bg-success/10 blur-3xl" />
      <div className="notebook-lines absolute inset-x-0 bottom-0 h-40 opacity-[0.12]" />
    </div>
  )
}

function StepDots({ active }: { active: number }) {
  return (
    <div className="flex items-center gap-1.5">
      {[0, 1].map((i) => (
        <span
          key={i}
          className={cx(
            'h-1.5 rounded-full transition-all',
            i === active ? 'w-5 bg-accent' : 'w-1.5 bg-line',
          )}
        />
      ))}
    </div>
  )
}

function Welcome({ targets, onStart }: { targets: LanguageOption[]; onStart: () => void }) {
  return (
    <div className="animate-fade-in space-y-10 text-center">
      <header className="space-y-4">
        <div className="text-xs font-semibold uppercase tracking-[0.25em] text-accent">
          Your language notebook
        </div>
        <h1 className="font-serif text-5xl font-semibold sm:text-6xl">Sprachheft</h1>
        <p className="mx-auto max-w-xl text-lg text-muted">
          Turn the videos, podcasts and articles you already love into vocabulary, exercises and
          daily practice — all in one cozy notebook.
        </p>
      </header>

      <div className="grid gap-3 text-left sm:grid-cols-2">
        {FEATURES.map((f) => (
          <Card key={f.title} className="flex items-start gap-3 p-4">
            <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent-soft text-accent">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-5 w-5"
              >
                {f.icon}
              </svg>
            </span>
            <div>
              <div className="font-medium">{f.title}</div>
              <p className="text-sm text-muted">{f.body}</p>
            </div>
          </Card>
        ))}
      </div>

      <div className="space-y-5">
        {targets.length > 0 && (
          <div className="flex flex-col items-center gap-2">
            <span className="text-xs uppercase tracking-wide text-muted">Ready to learn</span>
            <div className="flex flex-wrap items-center justify-center gap-2">
              {targets.map((t) => (
                <span
                  key={t.code}
                  className="inline-flex items-center gap-2 rounded-full border border-line bg-card px-3 py-1 text-sm"
                >
                  <Flag code={t.code} className="h-4 w-6" />
                  {t.endonym}
                </span>
              ))}
            </div>
          </div>
        )}
        <Button className="px-6 py-2.5 text-base" onClick={onStart}>
          Get started
        </Button>
      </div>
    </div>
  )
}

function Choose({
  targets,
  natives,
  target,
  nativeChoice,
  onPickTarget,
  onPickNative,
  onBack,
  onContinue,
}: {
  targets: LanguageOption[]
  natives: NativeOption[]
  target: string | null
  nativeChoice: string
  onPickTarget: (code: string) => void
  onPickNative: (code: string) => void
  onBack: () => void
  onContinue: () => void
}) {
  return (
    <div className="animate-fade-in space-y-8">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={onBack}
          className="text-sm text-muted transition hover:text-ink"
        >
          ← Back
        </button>
        <StepDots active={0} />
      </div>

      <header className="space-y-2 text-center">
        <h1 className="font-serif text-3xl font-semibold">What would you like to learn?</h1>
        <p className="text-muted">Pick a language to open a fresh notebook. You can switch anytime.</p>
      </header>

      {targets.length === 0 ? (
        <Card className="p-6 text-center text-sm text-muted">
          No languages are available yet. Make sure the backend is running and has content under
          <code className="mx-1">content/&lt;lang&gt;/</code>.
        </Card>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {targets.map((t) => {
            const selected = target === t.code
            return (
              <button
                key={t.code}
                type="button"
                onClick={() => onPickTarget(t.code)}
                aria-pressed={selected}
                className={cx(
                  'flex items-center gap-4 rounded-xl border p-4 text-left transition',
                  selected
                    ? 'border-accent bg-accent-soft shadow-sm'
                    : 'border-line bg-card hover:border-accent/60 hover:bg-accent-soft/40',
                )}
              >
                <Flag code={t.code} className="h-12 w-16" />
                <div className="min-w-0 flex-1">
                  <div className="font-serif text-xl">{t.endonym}</div>
                  <div className="text-sm text-muted">{t.name}</div>
                </div>
                <span
                  className={cx(
                    'text-xs uppercase tracking-wide',
                    selected ? 'text-accent' : 'text-muted',
                  )}
                >
                  {t.level_framework}
                </span>
              </button>
            )
          })}
        </div>
      )}

      <Card className="space-y-4 p-5">
        <Field label="I already speak">
          <div className="flex items-center gap-3">
            <Flag code={nativeChoice} className="h-6 w-9" />
            <Select
              className="flex-1"
              value={nativeChoice}
              onChange={(e) => onPickNative(e.target.value)}
            >
              {natives.map((n) => (
                <option key={n.code} value={n.code}>
                  {n.name}
                </option>
              ))}
            </Select>
          </div>
        </Field>
        <p className="text-xs text-muted">
          Explanations, meanings and feedback are written in this language.
        </p>
        <Button className="w-full py-2.5 text-base" disabled={!target} onClick={onContinue}>
          Continue
        </Button>
      </Card>
    </div>
  )
}

function Preparing({ endonym, onReady }: { endonym: string; onReady: () => void }) {
  const [progress, setProgress] = useState(0)
  // Keep the latest onReady without restarting the countdown effect.
  const readyRef = useRef(onReady)
  readyRef.current = onReady

  useEffect(() => {
    const DURATION = 2200
    const start = performance.now()
    let raf = 0
    const tick = (now: number) => {
      const pct = Math.min(100, ((now - start) / DURATION) * 100)
      setProgress(pct)
      if (pct >= 100) {
        readyRef.current()
        return
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])

  const message =
    PREPARING_MESSAGES[
      Math.min(
        PREPARING_MESSAGES.length - 1,
        Math.floor((progress / 100) * PREPARING_MESSAGES.length),
      )
    ]

  return (
    <div className="animate-fade-in mx-auto max-w-md space-y-8 text-center">
      <div className="flex justify-center">
        <StepDots active={1} />
      </div>
      <div className="flex justify-center">
        <span className="animate-float inline-block">
          <span className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-accent border-t-transparent" />
        </span>
      </div>
      <div className="space-y-2">
        <h1 className="font-serif text-3xl font-semibold">
          We’re getting your learning ready for you
        </h1>
        <p className="text-muted">Preparing your {endonym} notebook…</p>
      </div>
      <div className="space-y-2">
        <div className="h-2 w-full overflow-hidden rounded-full bg-line">
          <div
            className="h-full rounded-full bg-accent transition-[width] duration-150 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-sm text-muted">{message}</p>
      </div>
    </div>
  )
}
