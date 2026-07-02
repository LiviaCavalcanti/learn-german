import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../lib/api'
import type { ReviewStats } from '../../lib/types'
import { Card } from '../../components/ui'

export default function Dashboard() {
  const [stats, setStats] = useState<ReviewStats | null>(null)
  const [dict, setDict] = useState<{ available: boolean; entry_count: number } | null>(null)

  useEffect(() => {
    api.reviewStats().then(setStats).catch(() => {})
    api.dictStatus().then(setDict).catch(() => {})
  }, [])

  const cards = [
    { label: 'Due now', value: stats?.due_now ?? '—' },
    { label: 'Reviews today', value: stats?.reviews_today ?? '—' },
    { label: 'Streak', value: stats ? `${stats.streak} d` : '—' },
    { label: 'Vocabulary', value: stats?.total_vocab ?? '—' },
  ]

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl">Willkommen zurück</h1>
        <p className="text-muted">Your German learning notebook.</p>
      </header>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {cards.map((c) => (
          <Card key={c.label} className="p-4">
            <div className="font-serif text-3xl">{c.value}</div>
            <div className="mt-1 text-xs text-muted">{c.label}</div>
          </Card>
        ))}
      </div>

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
            ? `${dict.entry_count.toLocaleString()} entries loaded (WikDict). Hover any German word in a material.`
            : 'Not loaded — run the dictionary loader in the backend.'}
        </div>
      </Card>
    </div>
  )
}
