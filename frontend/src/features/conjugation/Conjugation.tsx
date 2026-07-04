import { useCallback, useEffect, useState, useSyncExternalStore, type FormEvent } from 'react'
import { useLanguage } from '../../contexts/LanguageContext'
import type { ConjugationTable, ConjugationTense } from '../../lib/types'
import { Badge, Button, Card, Input, Spinner, cx } from '../../components/ui'
import {
  clearSeen,
  conjugate,
  getSnapshot,
  preloadCommon,
  select,
  subscribe,
  type ConjugationJob,
} from './conjugationStore'

export default function Conjugation() {
  const { target, targetProfile } = useLanguage()
  const languageName = targetProfile?.name ?? 'target-language'
  const lang = target ?? 'de'
  const state = useSyncExternalStore(
    subscribe,
    useCallback(() => getSnapshot(lang), [lang]),
  )
  const activeJob = state.activeId ? (state.jobs[state.activeId] ?? null) : null
  const [verb, setVerb] = useState(() => activeJob?.label ?? '')

  // Warm the cache with the language's most common verbs (fetched once, then cached).
  useEffect(() => {
    preloadCommon(lang)
  }, [lang])

  const loading = activeJob?.status === 'loading'
  const table = activeJob?.status === 'done' ? activeJob.table : null
  const error = activeJob?.status === 'error' ? activeJob.error : null
  const vocabStatus = activeJob?.vocabStatus ?? null

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    conjugate(lang, verb)
  }

  function onSelect(job: ConjugationJob) {
    setVerb(job.label)
    select(lang, job.id)
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl">Verb conjugation</h1>
        <p className="text-muted">
          Type a {languageName} verb in any form — conjugated or not — to see its full table. New
          verbs are added to your vocabulary.
        </p>
      </header>

      <Card className="p-4">
        <form className="flex flex-wrap items-center gap-2" onSubmit={onSubmit}>
          <Input
            className="max-w-xs"
            value={verb}
            placeholder="type any verb form…"
            onChange={(e) => setVerb(e.target.value)}
          />
          <Button type="submit" disabled={loading || !verb.trim()}>
            {loading ? <Spinner /> : 'Conjugate'}
          </Button>
        </form>
      </Card>

      {state.order.length > 0 && (
        <Card className="p-4">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-xs font-medium uppercase tracking-wide text-muted">Seen verbs</div>
            <button
              type="button"
              onClick={() => clearSeen(lang)}
              className="text-xs text-muted hover:text-ink"
            >
              Clear
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {state.order.map((id) => {
              const job = state.jobs[id]
              if (!job) return null
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => onSelect(job)}
                  className={cx(
                    'flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm',
                    id === state.activeId
                      ? 'border-accent bg-accent-soft'
                      : 'border-line bg-paper hover:bg-accent-soft',
                  )}
                >
                  <span>{job.label}</span>
                  {job.status === 'loading' && <ChipSpinner />}
                  {job.status === 'error' && <span className="text-danger">!</span>}
                </button>
              )
            })}
          </div>
        </Card>
      )}

      {error && <Card className="p-4 text-sm text-danger">{error}</Card>}
      {loading && !table && (
        <Card className="flex items-center gap-3 p-4 text-sm text-muted">
          <Spinner />
          <span>Conjugating {activeJob?.label}…</span>
        </Card>
      )}
      {table && (
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

function ChipSpinner() {
  return (
    <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-accent border-t-transparent" />
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
        {table.tenses.map((tense) => (
          <TenseBlock key={tense.name} tense={tense} />
        ))}
      </div>
    </div>
  )
}

function TenseBlock({ tense }: { tense: ConjugationTense }) {
  return (
    <Card className="p-4">
      <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">{tense.name}</div>
      <table className="w-full text-sm">
        <tbody>
          {tense.cells.map((cell, i) => (
            <Row
              key={`${cell.label}-${i}`}
              label={cell.label}
              value={cell.form}
              last={i === tense.cells.length - 1}
            />
          ))}
        </tbody>
      </table>
      {tense.note && <p className="mt-2 text-xs text-muted">{tense.note}</p>}
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
