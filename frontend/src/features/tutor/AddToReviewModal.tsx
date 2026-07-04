import { useState } from 'react'
import { api } from '../../lib/api'
import type { ChatContext } from '../../lib/types'
import { Button, Card, Field, Input, Select, Spinner, Textarea } from '../../components/ui'

const CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1']

/** Modal to turn a teacher message into a review flashcard. Pre-filled with the
 *  teacher's answer as the back; the learner can edit both sides (and optionally
 *  ask the teacher to draft a tidy front/back) before saving to the review deck. */
export function AddToReviewModal({
  sourceText,
  context,
  defaultLevel = 'A2',
  onClose,
  onSaved,
}: {
  sourceText: string
  context?: ChatContext
  defaultLevel?: string
  onClose: () => void
  onSaved: () => void
}) {
  const [front, setFront] = useState('')
  const [back, setBack] = useState(sourceText)
  const [cefr, setCefr] = useState(defaultLevel)
  const [tags, setTags] = useState('')
  const [saving, setSaving] = useState(false)
  const [suggesting, setSuggesting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function suggest() {
    setSuggesting(true)
    setError(null)
    try {
      const s = await api.tutorSuggestCard({ text: sourceText, context })
      setFront(s.front)
      setBack(s.back)
      if (s.cefr) setCefr(s.cefr)
      if (s.tags?.length) setTags(s.tags.join(', '))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not draft a card.')
    } finally {
      setSuggesting(false)
    }
  }

  async function save() {
    if (!front.trim() || !back.trim()) {
      setError('Both the front and back are required.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await api.tutorCreateCard({
        front: front.trim(),
        back: back.trim(),
        cefr,
        tags: tags
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      })
      onSaved()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save the card.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-ink/30 p-4 pt-16"
      onClick={onClose}
    >
      <div className="w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
        <Card className="space-y-4 p-6">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-xl">Add to review deck</h2>
            <Button variant="soft" onClick={suggest} disabled={suggesting || saving}>
              {suggesting ? <Spinner /> : 'Draft with teacher'}
            </Button>
          </div>
          <p className="text-xs text-muted">
            Edit the card before saving. The front is what you'll see; reveal shows the back.
          </p>
          <Field label="Front (prompt / cue)">
            <Textarea
              rows={2}
              value={front}
              placeholder="e.g. Welcher Fall folgt auf „mit“?"
              onChange={(e) => setFront(e.target.value)}
            />
          </Field>
          <Field label="Back (answer)">
            <Textarea rows={4} value={back} onChange={(e) => setBack(e.target.value)} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="CEFR">
              <Select value={cefr} onChange={(e) => setCefr(e.target.value)}>
                {CEFR_LEVELS.map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Tags (comma-separated)">
              <Input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="dativ" />
            </Field>
          </div>
          {error && <p className="text-sm text-danger">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={onClose} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={save} disabled={saving}>
              {saving ? <Spinner /> : 'Save card'}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}
