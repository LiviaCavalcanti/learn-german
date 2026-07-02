import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../../lib/api'
import type { Exercise, Material, VocabItem } from '../../lib/types'
import { Badge, Button, Card, Input, Select, Spinner, cx } from '../../components/ui'
import { TokenizedText } from '../../components/TokenizedText'

const GRADABLE = ['fill-in-blank', 'conjugation', 'translation', 'multiple-choice', 'reorder']

export default function MaterialDetail() {
  const { id } = useParams()
  const materialId = Number(id)
  const [material, setMaterial] = useState<Material | null>(null)
  const [vocab, setVocab] = useState<VocabItem[]>([])
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [stage, setStage] = useState(2)
  const [generating, setGenerating] = useState(false)

  function reload() {
    api.material(materialId).then(setMaterial).catch(() => {})
    api.vocab(materialId).then(setVocab).catch(() => {})
    api.exercises(materialId).then(setExercises).catch(() => {})
  }
  useEffect(reload, [materialId])

  async function generate() {
    setGenerating(true)
    try {
      await api.generate(materialId, stage)
      reload()
    } finally {
      setGenerating(false)
    }
  }

  if (!material) return <Spinner />

  return (
    <div className="space-y-6">
      <div>
        <Link to="/library" className="text-sm text-muted hover:text-ink">
          ← Library
        </Link>
        <div className="mt-1 flex items-center gap-3">
          <h1 className="text-3xl">{material.title}</h1>
          <Badge>{material.level}</Badge>
        </div>
        {material.source_url && (
          <a className="text-sm text-accent" href={material.source_url} target="_blank" rel="noreferrer">
            {material.source_url}
          </a>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
            Transcript · hover any word
          </div>
          <div className="notebook-lines">
            <TokenizedText text={material.transcript} className="block text-[15px] leading-7" />
          </div>
        </Card>
        {material.translation && (
          <Card className="p-5">
            <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">Translation</div>
            <p className="text-[15px] leading-7 text-muted">{material.translation}</p>
          </Card>
        )}
      </div>

      <Card className="flex flex-wrap items-center justify-between gap-3 p-4">
        <div>
          <div className="font-medium">Generate study material</div>
          <div className="text-sm text-muted">Vocabulary + exercises with adaptive scaffolding.</div>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-muted">Stage</label>
          <Select value={stage} onChange={(e) => setStage(Number(e.target.value))}>
            <option value={1}>1 · most hints</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
            <option value={4}>4 · no hints</option>
          </Select>
          <Button onClick={generate} disabled={generating}>
            {generating ? <Spinner /> : 'Generate'}
          </Button>
        </div>
      </Card>

      {vocab.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-xl">Vocabulary</h2>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {vocab.map((v) => (
              <Card key={v.id} className="p-3">
                <div className="flex items-baseline justify-between">
                  <span className="font-serif">{v.word}</span>
                  {v.cefr && <Badge>{v.cefr}</Badge>}
                </div>
                <div className="text-sm text-muted">{v.meaning_en}</div>
                {v.example_de && <div className="mt-1 text-xs italic text-muted">{v.example_de}</div>}
              </Card>
            ))}
          </div>
        </section>
      )}

      {exercises.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-xl">Exercises</h2>
          <div className="space-y-3">
            {exercises.map((ex) => (
              <ExerciseCard key={ex.id} ex={ex} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

function ExerciseCard({ ex }: { ex: Exercise }) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const items: any[] = Array.isArray(ex.payload?.items) ? ex.payload.items : []
  const [responses, setResponses] = useState<string[]>(items.map(() => ''))
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any>(null)
  const [revealed, setRevealed] = useState(false)
  const gradable = GRADABLE.includes(ex.type)

  function setResp(i: number, val: string) {
    setResponses((prev) => {
      const copy = [...prev]
      copy[i] = val
      return copy
    })
  }

  async function check() {
    const r = await api.practiceAnswer({ exercise_id: ex.id, responses })
    setResult(r.check)
  }

  return (
    <Card className="space-y-3 p-4">
      <div className="flex items-center justify-between">
        <Badge>{ex.type}</Badge>
        <div className="flex gap-2 text-xs text-muted">
          {ex.grammar_tags?.map((t) => <span key={t}>#{t}</span>)}
          {ex.cefr && <span>{ex.cefr}</span>}
        </div>
      </div>
      <div className="text-sm font-medium">{ex.instructions}</div>

      {ex.payload?.text && (
        <div className="notebook-lines rounded-lg bg-paper/60 p-3">
          <TokenizedText text={String(ex.payload.text)} className="block text-sm leading-7" />
        </div>
      )}

      {gradable ? (
        <div className="space-y-3">
          {items.map((it, i) => (
            <div key={i} className="space-y-1">
              {it.prompt && (
                <div className="text-sm">
                  <TokenizedText text={String(it.prompt)} />
                </div>
              )}
              {it.person && <div className="text-sm text-muted">{String(it.person)}</div>}
              {ex.type === 'multiple-choice' && Array.isArray(it.options) ? (
                <div className="flex flex-wrap gap-2">
                  {it.options.map((opt: string) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => setResp(i, opt)}
                      className={cx(
                        'rounded-lg border px-3 py-1.5 text-sm',
                        responses[i] === opt
                          ? 'border-accent bg-accent-soft'
                          : 'border-line hover:bg-accent-soft/50',
                      )}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              ) : ex.type === 'reorder' && Array.isArray(it.tokens) ? (
                <div className="space-y-1">
                  <div className="flex flex-wrap gap-1">
                    {it.tokens.map((t: string, ti: number) => (
                      <span key={ti} className="rounded bg-accent-soft px-2 py-0.5 text-sm">
                        {t}
                      </span>
                    ))}
                  </div>
                  <Input
                    value={responses[i]}
                    placeholder="Type the ordered sentence"
                    onChange={(e) => setResp(i, e.target.value)}
                  />
                </div>
              ) : (
                <Input value={responses[i]} onChange={(e) => setResp(i, e.target.value)} />
              )}
              {result?.items?.[i] && (
                <div
                  className={cx(
                    'text-xs',
                    result.items[i].correct ? 'text-success' : 'text-danger',
                  )}
                >
                  {result.items[i].correct ? '✓ Correct' : `Expected: ${result.items[i].expected}`}
                </div>
              )}
            </div>
          ))}
          <div className="flex items-center gap-3">
            <Button onClick={check}>Check</Button>
            {result && (
              <span className="text-sm text-muted">
                {result.correct}/{result.total}
              </span>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <OpenPayload ex={ex} />
          <Button variant="soft" onClick={() => setRevealed((v) => !v)}>
            {revealed ? 'Hide' : 'Show'} model answer
          </Button>
          {revealed && (
            <div className="space-y-2 rounded-lg bg-paper p-3 text-sm">
              {ex.answer_key?.model_answer && <p>{ex.answer_key.model_answer}</p>}
              {ex.answer_key?.sample_answer && <p>{ex.answer_key.sample_answer}</p>}
              {Array.isArray(ex.answer_key?.rubric) && (
                <ul className="list-disc pl-5 text-xs text-muted">
                  {ex.answer_key.rubric.map((r: string, i: number) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              )}
              {Array.isArray(ex.answer_key?.questions) && (
                <ul className="list-disc pl-5 text-xs text-muted">
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {ex.answer_key.questions.map((q: any, i: number) => (
                    <li key={i}>{q.answer}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

function OpenPayload({ ex }: { ex: Exercise }) {
  const p = ex.payload || {}
  if (ex.type === 'writing') {
    return (
      <div className="space-y-1 text-sm">
        {p.theme && (
          <div>
            <span className="text-muted">Theme: </span>
            {p.theme}
          </div>
        )}
        {p.task && <div>{p.task}</div>}
        {p.target_length && <div className="text-xs text-muted">Length: {p.target_length}</div>}
        {Array.isArray(p.useful_phrases) && p.useful_phrases.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {p.useful_phrases.map((w: string) => (
              <span key={w} className="rounded bg-accent-soft px-2 py-0.5 text-xs">
                {w}
              </span>
            ))}
          </div>
        )}
        {Array.isArray(p.checklist) && (
          <ul className="list-disc pl-5 text-xs text-muted">
            {p.checklist.map((c: string, i: number) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        )}
      </div>
    )
  }
  if (ex.type === 'interpretation') {
    return (
      <div className="space-y-1 text-sm">
        {p.prompt && <div>{p.prompt}</div>}
        {Array.isArray(p.guiding_points) && (
          <ul className="list-disc pl-5 text-xs text-muted">
            {p.guiding_points.map((g: string, i: number) => (
              <li key={i}>{g}</li>
            ))}
          </ul>
        )}
      </div>
    )
  }
  return (
    <div className="space-y-1 text-sm">
      {Array.isArray(p.questions) && (
        <ul className="list-decimal space-y-1 pl-5">
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          {p.questions.map((q: any, i: number) => (
            <li key={i}>{q.prompt}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
