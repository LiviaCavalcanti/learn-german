import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api, type NewMaterial } from '../../lib/api'
import type { MaterialSummary } from '../../lib/types'
import { Badge, Button, Card, Field, Input, Select, Spinner, Textarea } from '../../components/ui'

const EMPTY = {
  title: '',
  level: 'A2',
  media_type: 'text',
  source_url: '',
  transcript: '',
  translation: '',
}

export default function Library() {
  const [items, setItems] = useState<MaterialSummary[] | null>(null)
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState(EMPTY)
  const [ingestOk, setIngestOk] = useState(false)
  const [transcribing, setTranscribing] = useState(false)

  function load() {
    api.materials().then(setItems).catch(() => setItems([]))
  }
  useEffect(load, [])
  useEffect(() => {
    api
      .ingestStatus()
      .then((s) => setIngestOk(s.transcription_available))
      .catch(() => {})
  }, [])

  async function fetchTranscript() {
    setTranscribing(true)
    try {
      const r = await api.transcribe(form.source_url)
      setForm((f) => ({ ...f, transcript: r.transcript }))
    } catch {
      // ignore — transcription is best-effort
    } finally {
      setTranscribing(false)
    }
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const data: NewMaterial = {
        title: form.title,
        level: form.level,
        media_type: form.media_type,
        source_url: form.source_url || null,
        transcript: form.transcript,
        translation: form.translation || null,
      }
      await api.createMaterial(data)
      setForm(EMPTY)
      setOpen(false)
      load()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl">Library</h1>
          <p className="text-muted">Your collected videos, podcasts, and texts.</p>
        </div>
        <Button onClick={() => setOpen((v) => !v)}>{open ? 'Close' : '+ Add material'}</Button>
      </header>

      {open && (
        <Card className="p-5">
          <form onSubmit={submit} className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Title">
                <Input
                  value={form.title}
                  required
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Level">
                  <Select value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })}>
                    <option>A1</option>
                    <option>A2</option>
                    <option>B1</option>
                    <option>B2</option>
                  </Select>
                </Field>
                <Field label="Type">
                  <Select
                    value={form.media_type}
                    onChange={(e) => setForm({ ...form, media_type: e.target.value })}
                  >
                    <option value="text">text</option>
                    <option value="video">video</option>
                    <option value="podcast">podcast</option>
                  </Select>
                </Field>
              </div>
            </div>
            <Field label="Link (optional)">
              <div className="flex gap-2">
                <Input
                  value={form.source_url}
                  placeholder="https://..."
                  onChange={(e) => setForm({ ...form, source_url: e.target.value })}
                />
                {ingestOk && (
                  <Button
                    type="button"
                    variant="soft"
                    disabled={!form.source_url || transcribing}
                    onClick={fetchTranscript}
                  >
                    {transcribing ? <Spinner /> : 'Fetch transcript'}
                  </Button>
                )}
              </div>
            </Field>
            <Field label="Transcript (German)">
              <Textarea
                rows={5}
                value={form.transcript}
                required
                onChange={(e) => setForm({ ...form, transcript: e.target.value })}
              />
            </Field>
            <Field label="Translation (optional)">
              <Textarea
                rows={3}
                value={form.translation}
                onChange={(e) => setForm({ ...form, translation: e.target.value })}
              />
            </Field>
            <Button type="submit" disabled={saving}>
              {saving ? <Spinner /> : 'Save material'}
            </Button>
          </form>
        </Card>
      )}

      {items === null ? (
        <Spinner />
      ) : items.length === 0 ? (
        <Card className="p-8 text-center text-muted">No materials yet. Add your first one above.</Card>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {items.map((m) => (
            <Link key={m.id} to={`/materials/${m.id}`}>
              <Card className="p-4 transition hover:-translate-y-0.5 hover:shadow-md">
                <div className="flex items-center justify-between">
                  <div className="font-serif text-lg">{m.title}</div>
                  <Badge>{m.level}</Badge>
                </div>
                <div className="mt-2 flex gap-3 text-xs text-muted">
                  <span>{m.media_type}</span>
                  <span>{m.vocab_count} words</span>
                  <span>{m.exercise_count} exercises</span>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
