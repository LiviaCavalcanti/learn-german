import { useEffect, useState } from 'react'
import { api } from '../../lib/api'
import type { Rating, ReviewQueueItem, ReviewStats } from '../../lib/types'
import { Badge, Button, Card, Spinner } from '../../components/ui'

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

  if (queue === null) return <Spinner />

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl">Review</h1>
          <p className="text-muted">Spaced repetition · {stats?.streak ?? 0} day streak</p>
        </div>
        <Badge>{queue.length ? `${idx + 1} / ${queue.length}` : '0 due'}</Badge>
      </header>

      {queue.length === 0 ? (
        <Card className="p-10 text-center">
          <div className="font-serif text-2xl">All caught up 🎉</div>
          <p className="mt-1 text-muted">
            Nothing due right now. Generate more material or come back later.
          </p>
        </Card>
      ) : (
        <ReviewCard
          item={queue[idx]}
          revealed={revealed}
          onReveal={() => setRevealed(true)}
          onGrade={grade}
        />
      )}
    </div>
  )
}

function ReviewCard({
  item,
  revealed,
  onReveal,
  onGrade,
}: {
  item: ReviewQueueItem
  revealed: boolean
  onReveal: () => void
  onGrade: (r: Rating) => void
}) {
  const data = item.item
  return (
    <Card className="p-8">
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
        <div>
          <Badge>{data.type}</Badge>
          <div className="mt-2 text-lg font-medium">{data.instructions}</div>
          {revealed && (
            <pre className="mt-3 whitespace-pre-wrap rounded-lg bg-paper p-3 text-xs">
              {JSON.stringify(data.payload, null, 2)}
            </pre>
          )}
        </div>
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
