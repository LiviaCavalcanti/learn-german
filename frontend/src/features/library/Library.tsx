import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api, type NewMaterial } from '../../lib/api'
import type { MaterialSummary } from '../../lib/types'
import { useLanguage } from '../../contexts/LanguageContext'
import { Badge, Button, Card, Field, Input, Select, Spinner, Textarea } from '../../components/ui'
import { VideoEmbed } from '../../components/VideoEmbed'
import {
  GOOGLE_TRANSLATE_MAX,
  googleTranslateUrl,
  parseYouTubeId,
  stripTimestamps,
} from '../../lib/importHelpers'

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
  const [clipMsg, setClipMsg] = useState<string | null>(null)
  const { targetProfile, target, native } = useLanguage()
  const langName = targetProfile?.name ?? 'target language'
  const ytId = parseYouTubeId(form.source_url)

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

  /** Replace the transcript with a copy that has all timestamps removed. */
  function cleanTranscript() {
    setClipMsg(null)
    setForm((f) => ({ ...f, transcript: stripTimestamps(f.transcript) }))
  }

  /** Read the clipboard, strip timestamps, and drop it into the transcript box. */
  async function pasteCleanTranscript() {
    setClipMsg(null)
    try {
      const text = await navigator.clipboard.readText()
      if (!text.trim()) {
        setClipMsg('Clipboard is empty — copy the transcript first, then try again.')
        return
      }
      setForm((f) => ({ ...f, transcript: stripTimestamps(text) }))
    } catch {
      setClipMsg('Couldn\u2019t read the clipboard. Paste into the box, then click "Remove timestamps".')
    }
  }

  /** Open Google Translate in a new tab with the transcript pre-filled. */
  function openGoogleTranslate() {
    if (!form.transcript.trim()) return
    const url = googleTranslateUrl(form.transcript, target || 'de', native || 'en')
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  /** Paste the copied Google Translate output into the translation box. */
  async function pasteTranslation() {
    setClipMsg(null)
    try {
      const text = await navigator.clipboard.readText()
      if (!text.trim()) {
        setClipMsg('Clipboard is empty — copy the translation on Google Translate first.')
        return
      }
      setForm((f) => ({ ...f, translation: text.trim() }))
      setClipMsg('Translation pasted \u2713')
    } catch {
      setClipMsg('Couldn\u2019t read the clipboard. Paste it into the Translation box manually.')
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
            {ytId && (
              <div className="space-y-1">
                <VideoEmbed url={form.source_url} title={form.title || 'Video preview'} />
                <p className="text-xs text-muted">
                  Video detected — it will be embedded on the material page.
                </p>
              </div>
            )}
            <div className="space-y-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-medium text-muted">Transcript ({langName})</span>
                <div className="flex flex-wrap gap-1.5">
                  <Button
                    type="button"
                    variant="soft"
                    className="px-2.5 py-1 text-xs"
                    onClick={pasteCleanTranscript}
                  >
                    Paste + remove timestamps
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    className="px-2.5 py-1 text-xs"
                    disabled={!form.transcript.trim()}
                    onClick={cleanTranscript}
                  >
                    Remove timestamps
                  </Button>
                </div>
              </div>
              <Textarea
                rows={6}
                value={form.transcript}
                required
                onChange={(e) => setForm({ ...form, transcript: e.target.value })}
              />
              <p className="text-xs text-muted">
                On YouTube open the video, then <b>… more → Show transcript</b> (some channels
                also post it in the description or a pinned comment). Copy it and click{' '}
                <b>Paste + remove timestamps</b> — the times are stripped for you.
              </p>
            </div>
            <div className="space-y-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-xs font-medium text-muted">Translation (optional)</span>
                <div className="flex flex-wrap gap-1.5">
                  <Button
                    type="button"
                    variant="soft"
                    className="px-2.5 py-1 text-xs"
                    disabled={!form.transcript.trim()}
                    onClick={openGoogleTranslate}
                  >
                    Translate with Google ↗
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    className="px-2.5 py-1 text-xs"
                    onClick={pasteTranslation}
                  >
                    Paste translation
                  </Button>
                </div>
              </div>
              <Textarea
                rows={4}
                value={form.translation}
                onChange={(e) => setForm({ ...form, translation: e.target.value })}
              />
              <ol className="ml-4 list-decimal space-y-0.5 text-xs text-muted">
                <li>
                  Click <b>Translate with Google</b> — a new tab opens with your transcript ready.
                </li>
                <li>
                  On Google Translate, copy the result (the copy icon under the translation), then
                  close that tab.
                </li>
                <li>
                  Back here, click <b>Paste translation</b> to drop it into the box above.
                </li>
              </ol>
              {form.transcript.length > GOOGLE_TRANSLATE_MAX && (
                <p className="text-xs text-muted">
                  Note: Google Translate takes up to {GOOGLE_TRANSLATE_MAX.toLocaleString()}{' '}
                  characters at once — your transcript is longer, so translate it in parts.
                </p>
              )}
              {clipMsg && <p className="text-xs text-accent">{clipMsg}</p>}
            </div>
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
