import { useState } from 'react'
import { api } from '../../lib/api'
import { Button, Card, Field, Input, Select, Spinner, Textarea } from '../../components/ui'

export interface EditableCard {
  item_type: 'vocab' | 'exercise'
  item_id: number
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  item: any
}

const CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2']

/** Modal editor for a single review card. Vocab cards edit word/meaning/example/CEFR;
 *  exercise cards edit instructions and the answer key (as JSON). */
export function CardEditor({
  card,
  onClose,
  onSaved,
}: {
  card: EditableCard
  onClose: () => void
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSaved: (patch: Record<string, any>) => void
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-ink/30 p-4 pt-16"
      onClick={onClose}
    >
      <div className="w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
        <Card className="p-6">
          {card.item_type === 'vocab' ? (
            <VocabEditor card={card} onClose={onClose} onSaved={onSaved} />
          ) : (
            <ExerciseEditor card={card} onClose={onClose} onSaved={onSaved} />
          )}
        </Card>
      </div>
    </div>
  )
}

function VocabEditor({
  card,
  onClose,
  onSaved,
}: {
  card: EditableCard
  onClose: () => void
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSaved: (patch: Record<string, any>) => void
}) {
  const data = card.item
  const [word, setWord] = useState<string>(data.word ?? '')
  const [meaning, setMeaning] = useState<string>(data.meaning_en ?? '')
  const [example, setExample] = useState<string>(data.example_de ?? '')
  const [cefr, setCefr] = useState<string>(data.cefr ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function save() {
    if (!word.trim() || !meaning.trim()) {
      setError('Word and meaning are required.')
      return
    }
    setSaving(true)
    setError(null)
    const patch = {
      word: word.trim(),
      meaning_en: meaning.trim(),
      example_de: example.trim(),
      cefr: cefr || null,
    }
    try {
      await api.updateVocab(card.item_id, patch)
      onSaved(patch)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="font-serif text-xl">Edit word</h2>
      <Field label="Word">
        <Input value={word} onChange={(e) => setWord(e.target.value)} />
      </Field>
      <Field label="Meaning (EN)">
        <Input value={meaning} onChange={(e) => setMeaning(e.target.value)} />
      </Field>
      <Field label="Example (DE)">
        <Textarea rows={2} value={example} onChange={(e) => setExample(e.target.value)} />
      </Field>
      <Field label="CEFR">
        <Select value={cefr} onChange={(e) => setCefr(e.target.value)}>
          <option value="">—</option>
          {CEFR_LEVELS.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </Select>
      </Field>
      {error && <p className="text-sm text-danger">{error}</p>}
      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button onClick={save} disabled={saving}>
          {saving ? <Spinner /> : 'Save'}
        </Button>
      </div>
    </div>
  )
}

function ExerciseEditor({
  card,
  onClose,
  onSaved,
}: {
  card: EditableCard
  onClose: () => void
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSaved: (patch: Record<string, any>) => void
}) {
  const data = card.item
  const [instructions, setInstructions] = useState<string>(data.instructions ?? '')
  const [answerKey, setAnswerKey] = useState<string>(
    JSON.stringify(data.answer_key ?? {}, null, 2),
  )
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function save() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let parsed: any
    try {
      parsed = answerKey.trim() ? JSON.parse(answerKey) : {}
    } catch {
      setError('Answer key must be valid JSON.')
      return
    }
    if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
      setError('Answer key must be a JSON object.')
      return
    }
    setSaving(true)
    setError(null)
    const patch = { instructions, answer_key: parsed }
    try {
      await api.updateExercise(card.item_id, patch)
      onSaved(patch)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="font-serif text-xl">Edit exercise</h2>
      <p className="text-xs text-muted">
        {String(data.type)} · edit the instructions and answer key. The answer key is JSON.
      </p>
      <Field label="Instructions">
        <Textarea
          rows={2}
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
        />
      </Field>
      <Field label="Answer key (JSON)">
        <Textarea
          rows={8}
          className="font-mono text-xs"
          value={answerKey}
          onChange={(e) => setAnswerKey(e.target.value)}
        />
      </Field>
      {error && <p className="text-sm text-danger">{error}</p>}
      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button onClick={save} disabled={saving}>
          {saving ? <Spinner /> : 'Save'}
        </Button>
      </div>
    </div>
  )
}
