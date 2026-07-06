import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../lib/api'
import type { CourseIndex, CourseLevelDetail, CourseProgress } from '../../lib/types'
import { Badge, Button, Card, ProgressBar, Spinner, cx } from '../../components/ui'
import { TokenizedText } from '../../components/TokenizedText'

export default function Curriculum() {
  const [index, setIndex] = useState<CourseIndex | null>(null)
  const [level, setLevel] = useState('A1')
  const [detail, setDetail] = useState<CourseLevelDetail | null>(null)
  const [progress, setProgress] = useState<CourseProgress | null>(null)
  const [starting, setStarting] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.course().then(setIndex).catch(() => {})
    api.courseProgress().then(setProgress).catch(() => {})
  }, [])
  useEffect(() => {
    setDetail(null)
    api.courseLevel(level).then(setDetail).catch(() => {})
  }, [level])

  async function start(code: string) {
    setStarting(code)
    try {
      const material = await api.startLesson(code)
      navigate(`/materials/${material.id}`)
    } finally {
      setStarting(null)
    }
  }

  const completed = new Set(progress?.completed_codes ?? [])
  const levelProgress = progress?.levels.find((l) => l.level === level) ?? null

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl">Course</h1>
        <p className="text-muted">A1–C1 curriculum. Start a lesson to generate its exercises.</p>
      </header>

      <div className="flex flex-wrap gap-2">
        {(index?.levels ?? []).map((l) => (
          <button
            key={l.level}
            onClick={() => setLevel(l.level)}
            className={cx(
              'rounded-lg px-3 py-1.5 text-sm',
              level === l.level ? 'bg-accent text-white' : 'bg-accent-soft text-ink',
            )}
          >
            {l.level} · {l.title}
          </button>
        ))}
      </div>

      {levelProgress && (
        <ProgressBar
          value={levelProgress.lessons_completed}
          max={levelProgress.lessons_total}
          label={`${levelProgress.lessons_completed} of ${levelProgress.lessons_total} lessons practiced`}
        />
      )}

      {!detail ? (
        <Spinner />
      ) : (
        <div className="space-y-6">
          {detail.units.map((unit) => (
            <section key={unit.unit} className="space-y-3">
              <h2 className="text-xl">
                {unit.unit}. {unit.title}
              </h2>
              <div className="grid gap-3 sm:grid-cols-2">
                {unit.lessons.map((lesson) => (
                  <Card key={lesson.code} className="space-y-2 p-4">
                    <div className="flex items-center justify-between gap-2">
                      <div className="font-serif text-lg">{lesson.title}</div>
                      {completed.has(lesson.code) && (
                        <Badge className="shrink-0 border-success/40 bg-success/10 text-success">
                          ✓ Done
                        </Badge>
                      )}
                    </div>
                    <div className="text-xs text-muted">{lesson.can_do}</div>
                    <div className="rounded-lg bg-paper/60 p-2 text-sm">
                      <TokenizedText text={lesson.seed_text} />
                    </div>
                    <Button onClick={() => start(lesson.code)} disabled={starting === lesson.code}>
                      {starting === lesson.code ? <Spinner /> : 'Start lesson'}
                    </Button>
                  </Card>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
