import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../../lib/api'
import type { AnswerFeedback, Exercise, Material, VocabItem } from '../../lib/types'
import { Badge, Button, Card, Input, Select, Spinner, Textarea, cx } from '../../components/ui'
import { TokenizedText } from '../../components/TokenizedText'

const GRADABLE = ['fill-in-blank', 'conjugation', 'translation', 'multiple-choice', 'reorder']

/** Group exercises that share a variant group into ordered lists (seed first). */
function groupExercises(list: Exercise[]): Exercise[][] {
  const byGroup = new Map<number, Exercise[]>()
  for (const ex of list) {
    const gid = ex.group_id ?? ex.id
    const arr = byGroup.get(gid) ?? []
    arr.push(ex)
    byGroup.set(gid, arr)
  }
  const groups = [...byGroup.values()]
  for (const g of groups) {
    g.sort(
      (a, b) =>
        (a.variant_position ?? 0) - (b.variant_position ?? 0) ||
        a.created_at.localeCompare(b.created_at),
    )
  }
  // Newest slot first; adding a variant never moves a group (seed is stable).
  groups.sort((a, b) => b[0].created_at.localeCompare(a[0].created_at))
  return groups
}

/** Format a naive-UTC ISO timestamp from the API as a local date/time. */
function formatWhen(iso: string): string {
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`)
  return isNaN(d.getTime()) ? '' : d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export default function MaterialDetail() {
  const { id } = useParams()
  const materialId = Number(id)
  const [material, setMaterial] = useState<Material | null>(null)
  const [vocab, setVocab] = useState<VocabItem[]>([])
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [stage, setStage] = useState(2)
  const [generating, setGenerating] = useState(false)
  const [genNote, setGenNote] = useState<string | null>(null)
  const [genError, setGenError] = useState<string | null>(null)
  const [showRewrite, setShowRewrite] = useState(false)
  const [rewriteInstructions, setRewriteInstructions] = useState('')
  const [rewriting, setRewriting] = useState(false)

  function reload() {
    api.material(materialId).then(setMaterial).catch(() => {})
    api.vocab(materialId).then(setVocab).catch(() => {})
    api.exercises(materialId).then(setExercises).catch(() => {})
  }
  useEffect(reload, [materialId])

  async function generate() {
    setGenerating(true)
    setGenNote(null)
    setGenError(null)
    try {
      const res = await api.generate(materialId, stage)
      const [v, ex] = await Promise.all([api.vocab(materialId), api.exercises(materialId)])
      setVocab(v)
      setExercises(ex)
      setGenNote(
        `Saved · ${res.exercises_added} exercise${res.exercises_added === 1 ? '' : 's'} and ` +
          `${res.vocab_added} new word${res.vocab_added === 1 ? '' : 's'}.`,
      )
    } catch (e) {
      setGenError(
        e instanceof Error ? e.message : 'Generation failed — is the language model running?',
      )
    } finally {
      setGenerating(false)
    }
  }

  function addExercise(ex: Exercise) {
    setExercises((prev) => [...prev, ex])
  }

  async function rewrite(instructions: string) {
    setRewriting(true)
    try {
      const updated = await api.rewriteMaterial(materialId, {
        instructions: instructions || undefined,
        target_lines: 15,
      })
      setMaterial(updated)
      setShowRewrite(false)
      setRewriteInstructions('')
    } finally {
      setRewriting(false)
    }
  }

  if (!material) return <Spinner />

  return (
    <div className="space-y-6">
      <div>
        <Link to="/library" className="text-sm text-muted hover:text-ink">
          ← Library
        </Link>
        <div className="mt-1 flex items-center gap-3">
          <h1 className="text-3xl">{material.title}</h1>
          <Badge>{material.level}</Badge>
        </div>
        {material.source_url && (
          <a className="text-sm text-accent" href={material.source_url} target="_blank" rel="noreferrer">
            {material.source_url}
          </a>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <div className="mb-2 flex items-center justify-between gap-2">
            <div className="text-xs font-medium uppercase tracking-wide text-muted">
              Transcript · hover any word
            </div>
            <Button variant="ghost" onClick={() => setShowRewrite((v) => !v)}>
              {showRewrite ? 'Cancel' : 'Expand / rewrite'}
            </Button>
          </div>
          {showRewrite && (
            <div className="mb-3 space-y-2 rounded-lg border border-line bg-paper/60 p-3">
              <Textarea
                rows={2}
                value={rewriteInstructions}
                placeholder="How should the text change? e.g. 'make it about a business trip and longer'"
                onChange={(e) => setRewriteInstructions(e.target.value)}
              />
              <div className="flex flex-wrap items-center gap-2">
                <Button onClick={() => rewrite(rewriteInstructions)} disabled={rewriting}>
                  {rewriting ? <Spinner /> : 'Expand text'}
                </Button>
                <Button
                  variant="soft"
                  onClick={() =>
                    rewrite(
                      'Make the text noticeably longer and richer (at least 15 lines), same topic and level.',
                    )
                  }
                  disabled={rewriting}
                >
                  Make longer (15+ lines)
                </Button>
              </div>
            </div>
          )}
          <div className="notebook-lines">
            <TokenizedText text={material.transcript} className="block text-[15px] leading-7" />
          </div>
        </Card>
        {material.translation && (
          <Card className="p-5">
            <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">Translation</div>
            <p className="text-[15px] leading-7 text-muted">{material.translation}</p>
          </Card>
        )}
      </div>

      <Card className="flex flex-wrap items-center justify-between gap-3 p-4">
        <div>
          <div className="font-medium">Generate study material</div>
          <div className="text-sm text-muted">
            Saved to this material so you can revisit it anytime. Each generation adds a new set.
          </div>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-muted">Stage</label>
          <Select value={stage} onChange={(e) => setStage(Number(e.target.value))}>
            <option value={1}>1 · most hints</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
            <option value={4}>4 · no hints</option>
          </Select>
          <Button onClick={generate} disabled={generating}>
            {generating ? <Spinner /> : 'Generate'}
          </Button>
        </div>
      </Card>
      {genNote && <div className="-mt-2 text-sm text-success">{genNote}</div>}
      {genError && <div className="-mt-2 text-sm text-danger">{genError}</div>}

      {vocab.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-xl">Vocabulary</h2>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {vocab.map((v) => (
              <Card key={v.id} className="p-3">
                <div className="flex items-baseline justify-between">
                  <span className="font-serif">{v.word}</span>
                  {v.cefr && <Badge>{v.cefr}</Badge>}
                </div>
                <div className="text-sm text-muted">{v.meaning_en}</div>
                {v.example_de && <div className="mt-1 text-xs italic text-muted">{v.example_de}</div>}
              </Card>
            ))}
          </div>
        </section>
      )}

      {exercises.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-xl">Exercises</h2>
          <div className="space-y-3">
            {groupExercises(exercises).map((variants) => (
              <ExerciseGroupCard
                key={variants[0].group_id ?? variants[0].id}
                variants={variants}
                stage={stage}
                onAddVariant={addExercise}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

function ExerciseGroupCard({
  variants,
  stage,
  onAddVariant,
}: {
  variants: Exercise[]
  stage: number
  onAddVariant: (ex: Exercise) => void
}) {
  const [active, setActive] = useState(0)
  const [menuOpen, setMenuOpen] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resetKeys, setResetKeys] = useState<Record<number, number>>({})

  const count = variants.length
  const clampedActive = Math.min(active, count - 1)
  const current = variants[clampedActive]

  async function generateAnother() {
    setMenuOpen(false)
    setGenerating(true)
    setError(null)
    try {
      const created = await api.generateVariant(current.id, stage)
      onAddVariant(created)
      setActive(count) // appended at the end -> becomes the active variant
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not generate another exercise')
    } finally {
      setGenerating(false)
    }
  }

  function tryAgain() {
    setMenuOpen(false)
    setResetKeys((prev) => ({ ...prev, [current.id]: (prev[current.id] ?? 0) + 1 }))
  }

  return (
    <Card className="space-y-3 p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge>{current.type}</Badge>
          <div className="flex gap-2 text-xs text-muted">
            {current.grammar_tags?.map((t) => <span key={t}>#{t}</span>)}
            {current.cefr && <span>{current.cefr}</span>}
          </div>
        </div>
        <div className="flex items-center gap-1">
          {count > 1 && (
            <div className="flex items-center gap-1 text-xs text-muted" title="Saved variants">
              <button
                type="button"
                className="rounded px-1.5 py-0.5 hover:bg-accent-soft disabled:opacity-40"
                onClick={() => setActive(Math.max(0, clampedActive - 1))}
                disabled={clampedActive === 0}
                aria-label="Previous variant"
              >
                ‹
              </button>
              <span className="tabular-nums">
                {clampedActive + 1} / {count}
              </span>
              <button
                type="button"
                className="rounded px-1.5 py-0.5 hover:bg-accent-soft disabled:opacity-40"
                onClick={() => setActive(Math.min(count - 1, clampedActive + 1))}
                disabled={clampedActive === count - 1}
                aria-label="Next variant"
              >
                ›
              </button>
            </div>
          )}
          <div className="relative">
            <button
              type="button"
              onClick={() => setMenuOpen((v) => !v)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-paper px-2.5 py-1.5 text-sm text-ink shadow-sm hover:bg-accent-soft/60"
              aria-label="Exercise options"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              title="Options: try again or generate another"
            >
              {generating ? (
                <Spinner />
              ) : (
                <>
                  <span className="text-base leading-none">⋯</span>
                  <span>Options</span>
                </>
              )}
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                <div
                  className="absolute right-0 z-20 mt-1 w-56 overflow-hidden rounded-lg border border-line bg-card shadow-md"
                  role="menu"
                >
                  <button
                    type="button"
                    role="menuitem"
                    className="block w-full px-3 py-2 text-left text-sm hover:bg-accent-soft/60"
                    onClick={tryAgain}
                  >
                    Try again
                    <span className="block text-xs text-muted">Clear my answer and retry</span>
                  </button>
                  <button
                    type="button"
                    role="menuitem"
                    className="block w-full px-3 py-2 text-left text-sm hover:bg-accent-soft/60 disabled:opacity-50"
                    onClick={generateAnother}
                    disabled={generating}
                  >
                    Generate another
                    <span className="block text-xs text-muted">
                      A new variant, saved alongside this one
                    </span>
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {error && <div className="text-xs text-danger">{error}</div>}

      {variants.map((v, i) => (
        <div key={v.id} className={i === clampedActive ? '' : 'hidden'}>
          <ExerciseView
            key={`${v.id}:${resetKeys[v.id] ?? 0}`}
            ex={v}
            loadHistory={(resetKeys[v.id] ?? 0) === 0}
          />
        </div>
      ))}
    </Card>
  )
}

function ExerciseView({ ex, loadHistory = true }: { ex: Exercise; loadHistory?: boolean }) {
  const gradable = GRADABLE.includes(ex.type)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const items: any[] = Array.isArray(ex.payload?.items) ? ex.payload.items : []
  const inputCount = gradable ? Math.max(items.length, 1) : 0
  const [responses, setResponses] = useState<string[]>(() => Array(inputCount).fill(''))
  const [draft, setDraft] = useState('')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any>(null)
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null)
  const [checking, setChecking] = useState(false)
  const [attemptCount, setAttemptCount] = useState(0)
  const [lastAt, setLastAt] = useState<string | null>(null)

  function refreshAttempts() {
    api
      .attempts(ex.id)
      .then((list) => {
        setAttemptCount(list.length)
        setLastAt(list[0]?.created_at ?? null)
      })
      .catch(() => {})
  }

  useEffect(() => {
    if (!loadHistory) return
    let cancelled = false
    api
      .attempts(ex.id)
      .then((list) => {
        if (cancelled) return
        setAttemptCount(list.length)
        const last = list[0]
        if (!last) return
        setLastAt(last.created_at)
        if (gradable) {
          setResponses(Array.from({ length: inputCount }, (_, i) => last.responses[i] ?? ''))
          if (last.result) setResult(last.result)
        } else {
          setDraft(last.answer_text)
          if (last.result) setFeedback(last.result as AnswerFeedback)
        }
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ex.id, loadHistory])

  function setResp(i: number, val: string) {
    setResponses((prev) => {
      const copy = [...prev]
      copy[i] = val
      return copy
    })
  }

  async function check() {
    const r = await api.practiceAnswer({ exercise_id: ex.id, responses })
    setResult(r.check)
    refreshAttempts()
  }

  async function checkAnswer() {
    if (!draft.trim()) return
    setChecking(true)
    try {
      const fb = await api.practiceFeedback({ exercise_id: ex.id, answer: draft })
      setFeedback(fb)
      refreshAttempts()
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-baseline justify-between gap-2">
        <div className="text-sm font-medium">{ex.instructions}</div>
        {attemptCount > 0 && (
          <div className="shrink-0 text-xs text-success" title={lastAt ? `Last answered ${formatWhen(lastAt)}` : undefined}>
            Saved · answered {attemptCount}×
          </div>
        )}
      </div>

      {ex.payload?.text && (
        <div className="notebook-lines rounded-lg bg-paper/60 p-3">
          <TokenizedText text={String(ex.payload.text)} className="block text-sm leading-7" />
        </div>
      )}

      {gradable ? (
        <div className="space-y-3">
          {Array.from({ length: inputCount }).map((_, i) => {
            const it = items[i] ?? {}
            return (
            <div key={i} className="space-y-1">
              {it.prompt && (
                <div className="text-sm">
                  <TokenizedText text={String(it.prompt)} />
                </div>
              )}
              {it.person && <div className="text-sm text-muted">{String(it.person)}</div>}
              {ex.type === 'multiple-choice' && Array.isArray(it.options) ? (
                <div className="flex flex-wrap gap-2">
                  {it.options.map((opt: string) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => setResp(i, opt)}
                      className={cx(
                        'rounded-lg border px-3 py-1.5 text-sm',
                        responses[i] === opt
                          ? 'border-accent bg-accent-soft'
                          : 'border-line hover:bg-accent-soft/50',
                      )}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              ) : ex.type === 'reorder' && Array.isArray(it.tokens) ? (
                <div className="space-y-1">
                  <div className="flex flex-wrap gap-1">
                    {it.tokens.map((t: string, ti: number) => (
                      <span key={ti} className="rounded bg-accent-soft px-2 py-0.5 text-sm">
                        {t}
                      </span>
                    ))}
                  </div>
                  <Input
                    value={responses[i] ?? ''}
                    placeholder="Type the ordered sentence"
                    onChange={(e) => setResp(i, e.target.value)}
                  />
                </div>
              ) : (
                <Input value={responses[i] ?? ''} onChange={(e) => setResp(i, e.target.value)} />
              )}
              {result?.items?.[i] && (
                <div
                  className={cx(
                    'text-xs',
                    result.items[i].correct ? 'text-success' : 'text-danger',
                  )}
                >
                  {result.items[i].correct ? '✓ Correct' : `Expected: ${result.items[i].expected}`}
                </div>
              )}
            </div>
            )
          })}
          <div className="flex items-center gap-3">
            <Button onClick={check}>Check</Button>
            {result && (
              <span className="text-sm text-muted">
                {result.correct}/{result.total}
              </span>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <OpenPayload ex={ex} />
          <Textarea
            rows={5}
            value={draft}
            placeholder="Write your answer here..."
            onChange={(e) => setDraft(e.target.value)}
          />
          <div className="flex items-center gap-3">
            <Button variant="soft" onClick={checkAnswer} disabled={checking || !draft.trim()}>
              {checking ? <Spinner /> : 'Check my answer'}
            </Button>
            {feedback && !checking && (
              <span
                className={cx('text-sm', feedback.has_errors ? 'text-danger' : 'text-success')}
              >
                {feedback.has_errors
                  ? `${feedback.errors.length} correction${feedback.errors.length === 1 ? '' : 's'}`
                  : 'No errors found'}
              </span>
            )}
          </div>
          {feedback && <AnswerFeedbackView feedback={feedback} />}
        </div>
      )}
    </div>
  )
}

function AnswerFeedbackView({ feedback }: { feedback: AnswerFeedback }) {
  return (
    <div className="space-y-2 rounded-lg bg-paper p-3 text-sm">
      {feedback.summary && <p>{feedback.summary}</p>}
      {feedback.errors.length > 0 && (
        <ul className="space-y-1.5">
          {feedback.errors.map((e, i) => (
            <li key={i} className="rounded-lg border border-line/70 p-2">
              <div>
                {e.original && <span className="text-danger line-through">{e.original}</span>}
                {e.original && e.correction && <span className="mx-1 text-muted">→</span>}
                {e.correction && <span className="text-success">{e.correction}</span>}
              </div>
              {e.explanation && <div className="mt-0.5 text-xs text-muted">{e.explanation}</div>}
            </li>
          ))}
        </ul>
      )}
      {feedback.has_errors && feedback.corrected && (
        <div>
          <div className="text-xs font-medium text-muted">Corrected version</div>
          <p className="italic">{feedback.corrected}</p>
        </div>
      )}
    </div>
  )
}

function OpenPayload({ ex }: { ex: Exercise }) {
  const p = ex.payload || {}
  if (ex.type === 'writing') {
    return (
      <div className="space-y-1 text-sm">
        {p.theme && (
          <div>
            <span className="text-muted">Theme: </span>
            {p.theme}
          </div>
        )}
        {p.task && <div>{p.task}</div>}
        {p.target_length && <div className="text-xs text-muted">Length: {p.target_length}</div>}
        {Array.isArray(p.useful_phrases) && p.useful_phrases.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {p.useful_phrases.map((w: string) => (
              <span key={w} className="rounded bg-accent-soft px-2 py-0.5 text-xs">
                {w}
              </span>
            ))}
          </div>
        )}
        {Array.isArray(p.checklist) && (
          <ul className="list-disc pl-5 text-xs text-muted">
            {p.checklist.map((c: string, i: number) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        )}
      </div>
    )
  }
  if (ex.type === 'interpretation') {
    return (
      <div className="space-y-1 text-sm">
        {p.prompt && <div>{p.prompt}</div>}
        {Array.isArray(p.guiding_points) && (
          <ul className="list-disc pl-5 text-xs text-muted">
            {p.guiding_points.map((g: string, i: number) => (
              <li key={i}>{g}</li>
            ))}
          </ul>
        )}
      </div>
    )
  }
  return (
    <div className="space-y-1 text-sm">
      {Array.isArray(p.questions) && (
        <ul className="list-decimal space-y-1 pl-5">
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          {p.questions.map((q: any, i: number) => (
            <li key={i}>{q.prompt}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
