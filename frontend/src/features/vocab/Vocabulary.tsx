import { useEffect, useState } from 'react'
import { api } from '../../lib/api'
import type { VocabItem } from '../../lib/types'
import { Badge, Button, Card, Input, Spinner } from '../../components/ui'

type Topic = { topic: string; count: number; samples: { word: string; meaning_en: string }[] }

export default function Vocabulary() {
  const [q, setQ] = useState('')
  const [semantic, setSemantic] = useState(false)
  const [results, setResults] = useState<VocabItem[] | null>(null)
  const [topics, setTopics] = useState<Topic[]>([])
  const [busy, setBusy] = useState(false)
  const [indexing, setIndexing] = useState(false)

  async function rebuild() {
    setIndexing(true)
    try {
      await api.vocabReindex(true)
    } finally {
      setIndexing(false)
    }
  }

  useEffect(() => {
    api
      .vocabTopics()
      .then((t) => setTopics(t.topics))
      .catch(() => {})
    // Keep the similarity index fresh (cheap with the local embedder).
    api.vocabReindex().catch(() => {})
  }, [])

  async function search() {
    if (!q.trim()) return
    setBusy(true)
    try {
      setResults(await api.vocabSearch(q, semantic))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl">Vocabulary</h1>
        <p className="text-muted">Search and review the words you've learned.</p>
      </header>

      <Card className="space-y-3 p-4">
        <div className="flex gap-2">
          <Input
            value={q}
            placeholder="Search words, meanings, examples..."
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && search()}
          />
          <Button onClick={search} disabled={busy}>
            {busy ? <Spinner /> : 'Search'}
          </Button>
        </div>
        <div className="flex items-center justify-between gap-3">
          <label className="flex items-center gap-2 text-sm text-muted">
            <input
              type="checkbox"
              checked={semantic}
              onChange={(e) => setSemantic(e.target.checked)}
            />
            Semantic (similarity) search
          </label>
          <Button variant="ghost" onClick={rebuild} disabled={indexing}>
            {indexing ? <Spinner /> : 'Rebuild index'}
          </Button>
        </div>
      </Card>

      {results && (
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {results.length === 0 ? (
            <div className="text-muted">No matches.</div>
          ) : (
            results.map((v) => (
              <Card key={v.id} className="p-3">
                <div className="flex items-baseline justify-between">
                  <span className="font-serif">{v.word}</span>
                  {v.cefr && <Badge>{v.cefr}</Badge>}
                </div>
                <div className="text-sm text-muted">{v.meaning_en}</div>
              </Card>
            ))
          )}
        </div>
      )}

      <section className="space-y-3">
        <h2 className="text-xl">By topic</h2>
        {topics.length === 0 ? (
          <div className="text-muted">No vocabulary yet — generate or import some material.</div>
        ) : (
          <div className="grid gap-2 sm:grid-cols-2">
            {topics.map((t) => (
              <Card key={t.topic} className="p-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{t.topic}</span>
                  <Badge>{t.count}</Badge>
                </div>
                <div className="mt-1 text-xs text-muted">
                  {t.samples.map((s) => s.word).join(', ')}
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
