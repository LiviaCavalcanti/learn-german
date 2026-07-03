import { useState, type FormEvent } from 'react'
import { api } from '../../lib/api'
import type { ConjugationForms, ConjugationTable } from '../../lib/types'
import { Badge, Button, Card, Input, Spinner } from '../../components/ui'

const PERSONS: { key: keyof ConjugationForms; label: string }[] = [
  { key: 'ich', label: 'ich' },
  { key: 'du', label: 'du' },
  { key: 'er_sie_es', label: 'er/sie/es' },
  { key: 'wir', label: 'wir' },
  { key: 'ihr', label: 'ihr' },
  { key: 'sie_Sie', label: 'sie/Sie' },
]

const SEEN_KEY = 'sprachheft.conjugation.seen'

function loadSeen(): string[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(SEEN_KEY) || '[]')
    return Array.isArray(parsed) ? parsed.filter((v) => typeof v === 'string') : []
  } catch {
    return []
  }
}

function saveSeen(verbs: string[]) {
  try {
    localStorage.setItem(SEEN_KEY, JSON.stringify(verbs))
  } catch {
    /* ignore storage errors */
  }
}

export default function Conjugation() {
  const [verb, setVerb] = useState('')
  const [table, setTable] = useState<ConjugationTable | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [seen, setSeen] = useState<string[]>(loadSeen)
  const [vocabStatus, setVocabStatus] = useState<'added' | 'exists' | null>(null)

  async function run(input: string) {
    const q = input.trim()
    if (!q) return
    setLoading(true)
    setError(null)
    setVocabStatus(null)
    try {
      const result = await api.conjugate(q)
      setTable(result)
      setVerb(result.infinitive)
      setSeen((prev) => {
        const next = [
          result.infinitive,
          ...prev.filter((v) => v.toLowerCase() !== result.infinitive.toLowerCase()),
        ].slice(0, 40)
        saveSeen(next)
        return next
      })
      try {
        const saved = await api.addVerb({
          infinitive: result.infinitive,
          english: result.english,
          partizip_ii: result.partizip_ii,
          auxiliary: result.auxiliary,
        })
        setVocabStatus(saved.created ? 'added' : 'exists')
      } catch {
        setVocabStatus(null)
      }
    } catch {
      setError('Could not conjugate that verb. Check the spelling and try again.')
      setTable(null)
    } finally {
      setLoading(false)
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    run(verb)
  }

  function clearSeen() {
    setSeen([])
    saveSeen([])
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl">Verb conjugation</h1>
        <p className="text-muted">
          Type a German verb in any form — conjugated or not — to see its full table. New verbs
          are added to your vocabulary.
        </p>
      </header>

      <Card className="p-4">
        <form className="flex flex-wrap items-center gap-2" onSubmit={onSubmit}>
          <Input
            className="max-w-xs"
            value={verb}
            placeholder="e.g. habe, ging, arbeiten"
            onChange={(e) => setVerb(e.target.value)}
          />
          <Button type="submit" disabled={loading || !verb.trim()}>
            {loading ? <Spinner /> : 'Conjugate'}
          </Button>
        </form>
      </Card>

      {!table && seen.length > 0 && (
        <Card className="p-4">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-xs font-medium uppercase tracking-wide text-muted">Seen verbs</div>
            <button type="button" onClick={clearSeen} className="text-xs text-muted hover:text-ink">
              Clear
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {seen.map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => run(v)}
                className="rounded-full border border-line bg-paper px-3 py-1 text-sm hover:bg-accent-soft"
              >
                {v}
              </button>
            ))}
          </div>
        </Card>
      )}

      {error && <Card className="p-4 text-sm text-danger">{error}</Card>}
      {table && !loading && (
        <div className="space-y-3">
          {vocabStatus && (
            <div className={vocabStatus === 'added' ? 'text-sm text-success' : 'text-sm text-muted'}>
              {vocabStatus === 'added' ? 'Added to your vocabulary.' : 'Already in your vocabulary.'}
            </div>
          )}
          <ConjugationResult table={table} />
        </div>
      )}
    </div>
  )
}

function ConjugationResult({ table }: { table: ConjugationTable }) {
  return (
    <div className="space-y-4">
      <Card className="p-5">
        <div className="flex flex-wrap items-baseline gap-3">
          <span className="font-serif text-3xl">{table.infinitive}</span>
          {table.english && <span className="text-muted">{table.english}</span>}
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge>{table.regular ? 'regular' : 'irregular'}</Badge>
          {table.auxiliary && <Badge>aux: {table.auxiliary}</Badge>}
          {table.partizip_ii && <Badge>Partizip II: {table.partizip_ii}</Badge>}
        </div>
        {table.notes && <p className="mt-2 text-sm text-muted">{table.notes}</p>}
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <TenseBlock title="Präsens" forms={table.present} />
        <TenseBlock title="Präteritum" forms={table.praeteritum} />
        <TenseBlock title="Perfekt" forms={table.perfekt} />
        <TenseBlock title="Futur I" forms={table.futur1} />
        <TenseBlock title="Konjunktiv II" forms={table.konjunktiv2} />
        <Card className="p-4">
          <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
            Imperativ
          </div>
          <table className="w-full text-sm">
            <tbody>
              <Row label="du" value={table.imperative.du} />
              <Row label="ihr" value={table.imperative.ihr} />
              <Row label="Sie" value={table.imperative.Sie} last />
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  )
}

function TenseBlock({ title, forms }: { title: string; forms: ConjugationForms }) {
  return (
    <Card className="p-4">
      <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">{title}</div>
      <table className="w-full text-sm">
        <tbody>
          {PERSONS.map((p, i) => (
            <Row key={p.key} label={p.label} value={forms[p.key]} last={i === PERSONS.length - 1} />
          ))}
        </tbody>
      </table>
    </Card>
  )
}

function Row({ label, value, last }: { label: string; value: string; last?: boolean }) {
  return (
    <tr className={last ? '' : 'border-b border-line/50'}>
      <td className="whitespace-nowrap py-1 pr-3 text-muted">{label}</td>
      <td className="py-1 font-medium">{value || '—'}</td>
    </tr>
  )
}
