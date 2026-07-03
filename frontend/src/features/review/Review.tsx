import { useEffect, useState, type ReactNode } from 'react'
import { api } from '../../lib/api'
import type { Rating, ReviewQueueItem, ReviewStats } from '../../lib/types'
import { Badge, Button, Card, Spinner } from '../../components/ui'
import { TokenizedText } from '../../components/TokenizedText'
import { CardEditor } from './CardEditor'
import { ManageCards } from './ManageCards'

const RATINGS: { key: Rating; label: string; className: string }[] = [
  { key: 'again', label: 'Again', className: 'bg-danger/10 text-danger' },
  { key: 'hard', label: 'Hard', className: 'bg-accent-soft text-ink' },
  { key: 'good', label: 'Good', className: 'bg-accent text-white' },
  { key: 'easy', label: 'Easy', className: 'bg-success/15 text-success' },
]

export default function Review() {
  const [queue, setQueue] = useState<ReviewQueueItem[] | null>(null)
  const [idx, setIdx] = useState(0)
  const [revealed, setRevealed] = useState(false)
  const [stats, setStats] = useState<ReviewStats | null>(null)
  const [mode, setMode] = useState<'review' | 'manage'>('review')
  const [editing, setEditing] = useState<ReviewQueueItem | null>(null)

  function load() {
    api
      .reviewQueue(30)
      .then((q) => {
        setQueue(q)
        setIdx(0)
        setRevealed(false)
      })
      .catch(() => setQueue([]))
    api.reviewStats().then(setStats).catch(() => {})
  }
  useEffect(load, [])

  // Anki-style browser notification when items are due.
  useEffect(() => {
    if (!stats || stats.due_now <= 0 || typeof Notification === 'undefined') return
    if (Notification.permission === 'granted') {
      new Notification('Sprachheft', { body: `${stats.due_now} item(s) due for review.` })
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission()
    }
  }, [stats])

  async function grade(rating: Rating) {
    if (!queue) return
    const item = queue[idx]
    await api.reviewGrade({ item_type: item.item_type, item_id: item.item_id, rating })
    if (idx + 1 >= queue.length) {
      load()
    } else {
      setIdx(idx + 1)
      setRevealed(false)
    }
  }

  // Drop the current card locally after it was removed/deleted, advancing the queue.
  function dropCurrent() {
    if (!queue) return
    const next = queue.filter((_, i) => i !== idx)
    if (next.length === 0) {
      load()
      return
    }
    setQueue(next)
    if (idx >= next.length) setIdx(next.length - 1)
    setRevealed(false)
    api.reviewStats().then(setStats).catch(() => {})
  }

  async function removeFromReview() {
    const item = queue?.[idx]
    if (!item) return
    await api.reviewRemoveCards([item.srstate_id])
    dropCurrent()
  }

  async function deleteEntirely() {
    const item = queue?.[idx]
    if (!item) return
    if (!window.confirm('Delete this item entirely? It will be removed from your library.')) return
    await api.reviewDeleteCards([item.srstate_id])
    dropCurrent()
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function applyEdit(patch: Record<string, any>) {
    setQueue((q) =>
      q ? q.map((c, i) => (i === idx ? { ...c, item: { ...c.item, ...patch } } : c)) : q,
    )
    setEditing(null)
  }

  if (queue === null && mode === 'review') return <Spinner />

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl">Review</h1>
          <p className="text-muted">Spaced repetition · {stats?.streak ?? 0} day streak</p>
        </div>
        <div className="flex items-center gap-2">
          {mode === 'review' && (
            <Badge>{queue && queue.length ? `${idx + 1} / ${queue.length}` : '0 due'}</Badge>
          )}
          <Button
            variant="soft"
            onClick={() => {
              if (mode === 'manage') load()
              setMode(mode === 'review' ? 'manage' : 'review')
            }}
          >
            {mode === 'review' ? 'Manage cards' : 'Back to review'}
          </Button>
        </div>
      </header>

      {mode === 'manage' ? (
        <ManageCards onChanged={() => api.reviewStats().then(setStats).catch(() => {})} />
      ) : queue && queue.length === 0 ? (
        <Card className="p-10 text-center">
          <div className="font-serif text-2xl">All caught up 🎉</div>
          <p className="mt-1 text-muted">
            Nothing due right now. Generate more material or come back later.
          </p>
        </Card>
      ) : (
        queue && (
          <ReviewCard
            item={queue[idx]}
            revealed={revealed}
            onReveal={() => setRevealed(true)}
            onGrade={grade}
            onEdit={() => setEditing(queue[idx])}
            onRemoveFromReview={removeFromReview}
            onDelete={deleteEntirely}
          />
        )
      )}

      {editing && (
        <CardEditor card={editing} onClose={() => setEditing(null)} onSaved={applyEdit} />
      )}
    </div>
  )
}

function ReviewCard({
  item,
  revealed,
  onReveal,
  onGrade,
  onEdit,
  onRemoveFromReview,
  onDelete,
}: {
  item: ReviewQueueItem
  revealed: boolean
  onReveal: () => void
  onGrade: (r: Rating) => void
  onEdit: () => void
  onRemoveFromReview: () => void
  onDelete: () => void
}) {
  const data = item.item
  return (
    <Card className="p-8">
      <div className="mb-4 flex items-center justify-end gap-1">
        <Button variant="ghost" onClick={onEdit}>
          Edit
        </Button>
        <Button
          variant="ghost"
          onClick={onRemoveFromReview}
          title="Remove from review (keeps the item in your library)"
        >
          Remove
        </Button>
        <Button variant="danger" onClick={onDelete} title="Delete the item entirely">
          Delete
        </Button>
      </div>
      {item.item_type === 'vocab' ? (
        <div className="text-center">
          <div className="font-serif text-3xl">{data.word}</div>
          {revealed && (
            <div className="mt-4 space-y-1">
              <div className="text-lg">{data.meaning_en}</div>
              {data.example_de && <div className="text-sm italic text-muted">{data.example_de}</div>}
            </div>
          )}
        </div>
      ) : (
        <ExerciseReview data={data} revealed={revealed} />
      )}

      <div className="mt-8">
        {!revealed ? (
          <div className="text-center">
            <Button onClick={onReveal}>Show answer</Button>
          </div>
        ) : (
          <div className="grid grid-cols-4 gap-2">
            {RATINGS.map((r) => (
              <button
                key={r.key}
                onClick={() => onGrade(r.key)}
                className={`rounded-lg px-3 py-2 text-sm font-medium ${r.className}`}
              >
                {r.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </Card>
  )
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ExerciseReview({ data, revealed }: { data: any; revealed: boolean }) {
  const payload = data.payload || {}
  const answerKey = data.answer_key || {}

  // Teacher flashcards (saved from the chat) render as a simple front/back card.
  if (data.type === 'flashcard') {
    const back = answerKey.model_answer || answerKey.sample_answer || ''
    return (
      <div className="space-y-4 text-center">
        <Badge>flashcard</Badge>
        <div className="font-serif text-2xl">
          <TokenizedText text={String(data.instructions || payload.prompt || '')} />
        </div>
        {revealed ? (
          back && (
            <div className="mx-auto max-w-prose rounded-lg border border-success/30 bg-success/5 p-3 text-left text-sm">
              <TokenizedText text={String(back)} />
            </div>
          )
        ) : (
          <p className="text-xs text-muted">Recall the answer, then reveal to check yourself.</p>
        )}
      </div>
    )
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const items: any[] = Array.isArray(payload.items) ? payload.items : []
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const answers: any[] = Array.isArray(answerKey.items) ? answerKey.items : []
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const questions: any[] = Array.isArray(payload.questions) ? payload.questions : []
  const modelAnswer: string = answerKey.model_answer || answerKey.sample_answer || ''
  const hasKnown =
    items.length > 0 ||
    questions.length > 0 ||
    Boolean(payload.text) ||
    Boolean(payload.prompt) ||
    Boolean(payload.task) ||
    (Array.isArray(payload.guiding_points) && payload.guiding_points.length > 0)

  return (
    <div className="space-y-3">
      <Badge>{data.type}</Badge>
      <div className="text-lg font-medium">{data.instructions}</div>

      {payload.text && (
        <div className="notebook-lines rounded-lg bg-paper/60 p-3">
          <TokenizedText text={String(payload.text)} className="block text-sm leading-7" />
        </div>
      )}

      {items.length > 0 && (
        <ol className="space-y-2">
          {items.map((it, i) => (
            <li key={i} className="rounded-lg border border-line/60 bg-paper/40 p-3">
              {it.prompt && (
                <div className="text-sm">
                  <TokenizedText text={String(it.prompt)} />
                </div>
              )}
              {it.person && <div className="text-xs text-muted">{String(it.person)}</div>}
              {Array.isArray(it.options) && (
                <div className="mt-1 flex flex-wrap gap-1">
                  {it.options.map((o: string) => (
                    <span key={o} className="rounded bg-accent-soft px-2 py-0.5 text-xs">
                      {o}
                    </span>
                  ))}
                </div>
              )}
              {Array.isArray(it.tokens) && (
                <div className="mt-1 flex flex-wrap gap-1">
                  {it.tokens.map((t: string, ti: number) => (
                    <span key={ti} className="rounded bg-accent-soft px-2 py-0.5 text-xs">
                      {t}
                    </span>
                  ))}
                </div>
              )}
              {revealed && answers[i]?.answer != null && (
                <div className="mt-1 text-sm text-success">
                  <span className="text-xs uppercase tracking-wide text-muted">Answer: </span>
                  {String(answers[i].answer)}
                </div>
              )}
            </li>
          ))}
        </ol>
      )}

      {questions.length > 0 && (
        <ol className="list-decimal space-y-1 pl-5 text-sm">
          {questions.map((q, i) => (
            <li key={i}>
              {String(q?.prompt ?? q)}
              {revealed && answers[i]?.answer != null && (
                <div className="text-success">→ {String(answers[i].answer)}</div>
              )}
            </li>
          ))}
        </ol>
      )}

      {payload.prompt && <div className="text-sm">{String(payload.prompt)}</div>}
      {payload.task && <div className="text-sm">{String(payload.task)}</div>}
      {Array.isArray(payload.guiding_points) && payload.guiding_points.length > 0 && (
        <ul className="list-disc pl-5 text-xs text-muted">
          {payload.guiding_points.map((g: string, i: number) => (
            <li key={i}>{String(g)}</li>
          ))}
        </ul>
      )}

      {!hasKnown && <GenericContent payload={payload} answerKey={answerKey} revealed={revealed} />}

      {revealed && modelAnswer && (
        <div className="rounded-lg border border-success/30 bg-success/5 p-3 text-sm">
          <div className="text-xs uppercase tracking-wide text-muted">Model answer</div>
          <TokenizedText text={String(modelAnswer)} className="italic" />
        </div>
      )}

      {!revealed && (
        <p className="text-xs text-muted">Recall the answer, then reveal to check yourself.</p>
      )}
    </div>
  )
}

const ANSWER_KEY_RE = /answer|solution|lösung|loesung|correct|result|richtig/i
const MODEL_ANSWER_KEYS = new Set(['model_answer', 'sample_answer'])

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function isPlainObject(v: any): boolean {
  return v != null && typeof v === 'object' && !Array.isArray(v)
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function isEmpty(v: any): boolean {
  if (v == null) return true
  if (typeof v === 'string') return v.trim() === ''
  if (Array.isArray(v)) return v.length === 0
  if (isPlainObject(v)) return Object.keys(v).length === 0
  return false
}

/** Render an arbitrary JSON value (from a non-standard exercise payload) readably. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function renderValue(value: any): ReactNode {
  if (isEmpty(value)) return null
  if (Array.isArray(value)) {
    return (
      <ul className="list-disc pl-5">
        {value.map((v, i) => (
          <li key={i}>{renderValue(v)}</li>
        ))}
      </ul>
    )
  }
  if (isPlainObject(value)) {
    return (
      <ul className="space-y-0.5">
        {Object.entries(value).map(([k, v]) => (
          <li key={k}>
            <span className="text-muted">{k}: </span>
            {renderValue(v)}
          </li>
        ))}
      </ul>
    )
  }
  return <TokenizedText text={String(value)} />
}

/** Fallback for exercises whose payload does not match a known schema. Shows the
 *  question fields always and answer-like fields only once revealed. */
function GenericContent({
  payload,
  answerKey,
  revealed,
}: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  payload: any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  answerKey: any
  revealed: boolean
}) {
  const entries = isPlainObject(payload)
    ? Object.entries(payload).filter(([k, v]) => k !== 'hints' && !isEmpty(v))
    : []
  const questionEntries = entries.filter(([k]) => !ANSWER_KEY_RE.test(k))
  const answerEntries = entries.filter(([k]) => ANSWER_KEY_RE.test(k))
  const answerKeyEntries = (isPlainObject(answerKey) ? Object.entries(answerKey) : []).filter(
    ([k, v]) => !MODEL_ANSWER_KEYS.has(k) && !isEmpty(v),
  )
  const revealEntries = [...answerEntries, ...answerKeyEntries]

  return (
    <div className="space-y-2 text-sm">
      {questionEntries.length > 0 && (
        <dl className="space-y-1">
          {questionEntries.map(([k, v]) => (
            <div key={k}>
              <dt className="text-xs uppercase tracking-wide text-muted">{k}</dt>
              <dd>{renderValue(v)}</dd>
            </div>
          ))}
        </dl>
      )}
      {revealed && revealEntries.length > 0 && (
        <div className="rounded-lg border border-success/30 bg-success/5 p-3">
          <div className="text-xs uppercase tracking-wide text-muted">Answer</div>
          <div className="text-success">
            {revealEntries.map(([k, v]) => (
              <div key={k}>{renderValue(v)}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
