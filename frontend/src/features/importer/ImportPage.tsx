import { useState } from 'react'
import { api } from '../../lib/api'
import { useLanguage } from '../../contexts/LanguageContext'
import { Button, Card, Field, Input, Select, Spinner, Textarea, cx } from '../../components/ui'

export default function ImportPage() {
  const { targetProfile } = useLanguage()
  const langName = targetProfile?.name ?? 'target language'
  const [tab, setTab] = useState<'json' | 'text'>('json')
  const [raw, setRaw] = useState('')
  const [title, setTitle] = useState('')
  const [level, setLevel] = useState('A2')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)

  async function submit() {
    setBusy(true)
    setMsg(null)
    setErr(null)
    try {
      if (tab === 'json') {
        const data = JSON.parse(raw)
        const r = await api.importJson(data)
        setMsg(`Imported ${r.vocab_added} words and ${r.exercises_added} exercises.`)
      } else {
        const r = await api.importText({
          raw_text: raw,
          level,
          title: title.trim() || undefined,
        })
        setMsg(`Imported ${r.vocab_added} words and ${r.exercises_added} exercises.`)
      }
      setRaw('')
      setTitle('')
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Import failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl">Import</h1>
        <p className="text-muted">Paste prompt-pack JSON, or raw {langName} material to normalize.</p>
      </header>

      <div className="flex gap-2">
        {(['json', 'text'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cx(
              'rounded-lg px-3 py-1.5 text-sm',
              tab === t ? 'bg-accent text-white' : 'bg-accent-soft text-ink',
            )}
          >
            {t === 'json' ? 'Prompt-pack JSON' : 'Raw text (AI)'}
          </button>
        ))}
      </div>

      <Card className="space-y-3 p-5">
        {tab === 'text' && (
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Title (optional)">
              <Input
                value={title}
                placeholder="e.g. Wechselpräpositionen"
                onChange={(e) => setTitle(e.target.value)}
              />
            </Field>
            <Field label="Level">
              <Select value={level} onChange={(e) => setLevel(e.target.value)}>
                <option>A1</option>
                <option>A2</option>
                <option>B1</option>
                <option>B2</option>
              </Select>
            </Field>
          </div>
        )}
        <Field
          label={
            tab === 'json'
              ? 'JSON (MODE: JSON output from the generate-exercises prompt)'
              : `${langName} grammar / content to normalize`
          }
        >
          <Textarea
            rows={12}
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            placeholder={
              tab === 'json'
                ? '{ "material": {...}, "vocabulary": [...], "exercises": [...] }'
                : 'Paste grammar notes or exercises...'
            }
          />
        </Field>
        <Button onClick={submit} disabled={busy || !raw.trim()}>
          {busy ? <Spinner /> : 'Import'}
        </Button>
        {busy && (
          <div className="flex items-start gap-3 rounded-lg border border-line bg-accent-soft/40 p-3 text-sm text-ink">
            <Spinner />
            <div>
              <div className="font-medium">
                {tab === 'json' ? 'Importing…' : 'Analyzing your text…'}
              </div>
              <div className="text-muted">
                {tab === 'json'
                  ? 'Saving vocabulary and exercises to your library.'
                  : `Extracting vocabulary and building exercises from your ${langName} text. On a local model this can take a moment — please keep this tab open.`}
              </div>
            </div>
          </div>
        )}
        {msg && <div className="text-sm text-success">{msg}</div>}
        {err && <div className="text-sm text-danger">{err}</div>}
      </Card>
    </div>
  )
}
