import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../lib/api'
import type { CourseProgress, ReviewStats } from '../../lib/types'
import { useLanguage } from '../../contexts/LanguageContext'
import { Badge, Button, Card, ProgressBar, Spinner } from '../../components/ui'

export default function Dashboard() {
  const [stats, setStats] = useState<ReviewStats | null>(null)
  const [dict, setDict] = useState<{ available: boolean; entry_count: number } | null>(null)
  const [progress, setProgress] = useState<CourseProgress | null>(null)
  const [starting, setStarting] = useState(false)
  const navigate = useNavigate()
  const { targetProfile, target } = useLanguage()
  const langName = targetProfile?.name ?? 'language'

  // Re-fetch whenever the active language changes so the cards stay scoped to it.
  useEffect(() => {
    api.reviewStats().then(setStats).catch(() => {})
    api.dictStatus().then(setDict).catch(() => {})
    api.courseProgress().then(setProgress).catch(() => {})
  }, [target])

  async function startNext() {
    const next = progress?.next_lesson
    if (!next) return
    setStarting(true)
    try {
      const material = await api.startLesson(next.code)
      navigate(`/materials/${material.id}`)
    } finally {
      setStarting(false)
    }
  }

  const cards = [
    { label: 'Due now', value: stats?.due_now ?? '—' },
    { label: 'Reviews today', value: stats?.reviews_today ?? '—' },
    { label: 'Streak', value: stats ? `${stats.streak} d` : '—' },
    { label: 'Vocabulary', value: stats?.total_vocab ?? '—' },
  ]

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl">Welcome back</h1>
        <p className="text-muted">Your {langName} learning notebook.</p>
      </header>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {cards.map((c) => (
          <Card key={c.label} className="p-4">
            <div className="font-serif text-3xl">{c.value}</div>
            <div className="mt-1 text-xs text-muted">{c.label}</div>
          </Card>
        ))}
      </div>

      {progress && progress.total_lessons > 0 && (
        <Card className="space-y-4 p-5">
          <div className="flex items-baseline justify-between">
            <div className="font-medium">Course progress</div>
            <div className="text-sm text-muted">
              {progress.completed_lessons}/{progress.total_lessons} lessons · {progress.percent}%
            </div>
          </div>
          <ProgressBar
            value={progress.completed_lessons}
            max={progress.total_lessons}
            showCount={false}
          />
          <div className="grid gap-3 sm:grid-cols-2">
            {progress.levels.map((l) => (
              <ProgressBar
                key={l.level}
                value={l.lessons_completed}
                max={l.lessons_total}
                label={`${l.level} · ${l.title}`}
              />
            ))}
          </div>
          {progress.next_lesson && (
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4">
              <div className="min-w-0">
                <div className="text-xs uppercase tracking-wide text-muted">
                  {progress.completed_lessons > 0 ? 'Up next' : 'Start here'}
                </div>
                <div className="mt-0.5 flex items-center gap-2">
                  <Badge>{progress.next_lesson.level}</Badge>
                  <span className="font-medium">{progress.next_lesson.title}</span>
                </div>
                <div className="text-xs text-muted">{progress.next_lesson.can_do}</div>
              </div>
              <Button onClick={startNext} disabled={starting}>
                {starting ? (
                  <Spinner />
                ) : progress.completed_lessons > 0 ? (
                  'Continue'
                ) : (
                  'Start lesson'
                )}
              </Button>
            </div>
          )}
        </Card>
      )}

      <Card className="flex flex-wrap items-center justify-between gap-3 p-5">
        <div>
          <div className="font-medium">Ready to review?</div>
          <div className="text-sm text-muted">
            {stats?.due_now ? `${stats.due_now} item(s) due.` : 'Nothing due right now.'}
          </div>
        </div>
        <Link to="/review" className="rounded-lg bg-accent px-4 py-2 text-sm text-white">
          Start review
        </Link>
      </Card>

      <Card className="p-5">
        <div className="font-medium">Offline dictionary</div>
        <div className="text-sm text-muted">
          {dict?.available
            ? `${dict.entry_count.toLocaleString()} entries loaded (WikDict). Hover any ${langName} word in a material.`
            : 'Not loaded — run the dictionary loader in the backend.'}
        </div>
      </Card>
    </div>
  )
}
