import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, getApiLanguage } from '../../lib/api'
import type { VocabItem } from '../../lib/types'
import { useLanguage } from '../../contexts/LanguageContext'
import { Badge, Button, Card, Field, Input, Select, Spinner, cx } from '../../components/ui'
import { SpeakButton } from '../../components/SpeakButton'

type GroupBy = 'topic' | 'date'
type SortBy = 'recent' | 'oldest' | 'az' | 'za' | 'level'

/** A unique word merged from any duplicate rows (same lemma across materials). */
type WordEntry = {
  id: number // representative row id
  ids: number[] // every underlying row id (for delete/compose)
  material_id: number | null // source material (needed to regenerate easier/harder)
  word: string
  lemma: string
  meaning_en: string
  cefr: string | null
  example_de: string | null
  ipa: string | null
  grammar_tags: string[]
  created_at: string
}

type Group = { key: string; label: string; items: WordEntry[] }

const EMPTY_WORD = { word: '', meaning_en: '', cefr: 'A2', grammar_tags: '', example_de: '' }
const LEVEL_ORDER: Record<string, number> = { A1: 1, A2: 2, B1: 3, B2: 4 }

/** Collapse duplicate rows into one entry per lemma, unioning tags + ids. */
function dedupe(words: VocabItem[]): WordEntry[] {
  const byKey = new Map<string, WordEntry>()
  for (const v of words) {
    const key = (v.lemma || v.word).trim().toLowerCase()
    const existing = byKey.get(key)
    if (existing) {
      existing.ids.push(v.id)
      if (existing.material_id == null && v.material_id != null) {
        existing.material_id = v.material_id
      }
      for (const t of v.grammar_tags || []) {
        if (!existing.grammar_tags.includes(t)) existing.grammar_tags.push(t)
      }
      if (v.created_at > existing.created_at) existing.created_at = v.created_at
      if (!existing.example_de && v.example_de) existing.example_de = v.example_de
    } else {
      byKey.set(key, {
        id: v.id,
        ids: [v.id],
        material_id: v.material_id,
        word: v.word,
        lemma: v.lemma,
        meaning_en: v.meaning_en,
        cefr: v.cefr,
        example_de: v.example_de,
        ipa: v.ipa ?? null,
        grammar_tags: [...(v.grammar_tags || [])],
        created_at: v.created_at,
      })
    }
  }
  return [...byKey.values()]
}

function matches(v: WordEntry, needle: string): boolean {
  const hay = [v.word, v.lemma, v.meaning_en, v.grammar_tags.join(' ')].join(' ').toLowerCase()
  return hay.includes(needle)
}

function sortEntries(entries: WordEntry[], sortBy: SortBy): WordEntry[] {
  const arr = [...entries]
  const locale = getApiLanguage().target
  switch (sortBy) {
    case 'az':
      return arr.sort((a, b) => a.word.localeCompare(b.word, locale))
    case 'za':
      return arr.sort((a, b) => b.word.localeCompare(a.word, locale))
    case 'oldest':
      return arr.sort((a, b) => a.created_at.localeCompare(b.created_at))
    case 'level':
      return arr.sort(
        (a, b) =>
          (LEVEL_ORDER[a.cefr ?? ''] ?? 9) - (LEVEL_ORDER[b.cefr ?? ''] ?? 9) ||
          a.word.localeCompare(b.word, locale),
      )
    default:
      return arr.sort((a, b) => b.created_at.localeCompare(a.created_at))
  }
}

function groupByTopic(words: WordEntry[]): Group[] {
  const buckets = new Map<string, WordEntry[]>()
  for (const v of words) {
    const tags = v.grammar_tags.length ? v.grammar_tags : ['(untagged)']
    for (const tag of tags) {
      const arr = buckets.get(tag) ?? []
      arr.push(v)
      buckets.set(tag, arr)
    }
  }
  return [...buckets.entries()]
    .map(([key, items]) => ({ key, label: key, items }))
    .sort((a, b) => b.items.length - a.items.length || a.key.localeCompare(b.key))
}

function groupByDate(words: WordEntry[]): Group[] {
  const buckets = new Map<string, WordEntry[]>()
  for (const v of words) {
    const key = (v.created_at || '').slice(0, 10) || 'unknown'
    const arr = buckets.get(key) ?? []
    arr.push(v)
    buckets.set(key, arr)
  }
  return [...buckets.entries()]
    .map(([key, items]) => ({
      key,
      label:
        key === 'unknown'
          ? 'Unknown date'
          : new Date(key).toLocaleDateString(undefined, {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
            }),
      items,
    }))
    .sort((a, b) => b.key.localeCompare(a.key))
}

export default function Vocabulary() {
  const navigate = useNavigate()
  const { targetProfile } = useLanguage()
  const langName = targetProfile?.name ?? 'target'
  const [words, setWords] = useState<VocabItem[] | null>(null)
  const [groupBy, setGroupBy] = useState<GroupBy>('topic')
  const [sortBy, setSortBy] = useState<SortBy>('recent')
  const [filter, setFilter] = useState('')
  const [selected, setSelected] = useState<Set<number>>(new Set())

  const [showAdd, setShowAdd] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState(EMPTY_WORD)

  const [title, setTitle] = useState('')
  const [instructions, setInstructions] = useState('')
  const [level, setLevel] = useState('')
  const [composing, setComposing] = useState(false)
  const [composeError, setComposeError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [replacingId, setReplacingId] = useState<number | null>(null)

  function load() {
    api
      .allVocab()
      .then(setWords)
      .catch(() => setWords([]))
  }
  useEffect(load, [])

  const entries = useMemo(() => (words ? dedupe(words) : []), [words])

  const groups = useMemo(() => {
    const needle = filter.trim().toLowerCase()
    const visible = needle ? entries.filter((v) => matches(v, needle)) : entries
    const sorted = sortEntries(visible, sortBy)
    return groupBy === 'topic' ? groupByTopic(sorted) : groupByDate(sorted)
  }, [entries, filter, groupBy, sortBy])

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleGroup(items: WordEntry[], on: boolean) {
    setSelected((prev) => {
      const next = new Set(prev)
      for (const v of items) {
        if (on) next.add(v.id)
        else next.delete(v.id)
      }
      return next
    })
  }

  function selectedIds(): number[] {
    return entries.filter((e) => selected.has(e.id)).flatMap((e) => e.ids)
  }

  async function addWord(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const tags = form.grammar_tags
        .split(/[,\s]+/)
        .map((t) => t.trim())
        .filter(Boolean)
      await api.createVocab({
        word: form.word.trim(),
        meaning_en: form.meaning_en.trim(),
        cefr: form.cefr || null,
        grammar_tags: tags,
        example_de: form.example_de.trim() || null,
      })
      setForm(EMPTY_WORD)
      setShowAdd(false)
      load()
    } finally {
      setSaving(false)
    }
  }

  async function deleteEntry(entry: WordEntry) {
    if (!window.confirm(`Delete “${entry.word}”? This also removes its review progress.`)) return
    await api.deleteVocab(entry.ids)
    setSelected((prev) => {
      const next = new Set(prev)
      next.delete(entry.id)
      return next
    })
    load()
  }

  async function replaceEntry(entry: WordEntry, direction: 'easier' | 'harder') {
    if (entry.material_id == null) return
    setReplacingId(entry.id)
    try {
      await api.replaceVocab(entry.id, direction)
      load()
    } catch (err) {
      window.alert(err instanceof Error ? err.message : 'Could not adjust this word')
    } finally {
      setReplacingId(null)
    }
  }

  async function deleteSelected() {
    const ids = selectedIds()
    if (!ids.length) return
    if (
      !window.confirm(
        `Delete ${selected.size} selected word${selected.size === 1 ? '' : 's'}? ` +
          'This also removes their review progress.',
      )
    )
      return
    setDeleting(true)
    try {
      await api.deleteVocab(ids)
      setSelected(new Set())
      load()
    } finally {
      setDeleting(false)
    }
  }

  async function compose() {
    setComposing(true)
    setComposeError(null)
    try {
      const res = await api.composeFromVocab({
        vocab_ids: [...selected],
        title: title.trim() || undefined,
        instructions: instructions.trim() || undefined,
        level: level || undefined,
      })
      navigate(`/materials/${res.material_id}`)
    } catch (e) {
      setComposeError(
        e instanceof Error ? e.message : 'Generation failed — is the language model running?',
      )
    } finally {
      setComposing(false)
    }
  }

  const total = entries.length

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl">Vocabulary</h1>
          <p className="text-muted">
            {total} word{total === 1 ? '' : 's'} learned so far.
          </p>
        </div>
        <Button onClick={() => setShowAdd((v) => !v)}>{showAdd ? 'Close' : '+ Add word'}</Button>
      </header>

      {showAdd && (
        <Card className="p-5">
          <form onSubmit={addWord} className="space-y-3">
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Word (r/e/s for nouns)">
                <Input
                  value={form.word}
                  required
                  placeholder="e Idee"
                  onChange={(e) => setForm({ ...form, word: e.target.value })}
                />
              </Field>
              <Field label="Meaning (English)">
                <Input
                  value={form.meaning_en}
                  required
                  placeholder="idea"
                  onChange={(e) => setForm({ ...form, meaning_en: e.target.value })}
                />
              </Field>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Level">
                <Select value={form.cefr} onChange={(e) => setForm({ ...form, cefr: e.target.value })}>
                  <option>A1</option>
                  <option>A2</option>
                  <option>B1</option>
                  <option>B2</option>
                </Select>
              </Field>
              <Field label="Topic tags (comma separated)">
                <Input
                  value={form.grammar_tags}
                  placeholder="a2.dative, travel"
                  onChange={(e) => setForm({ ...form, grammar_tags: e.target.value })}
                />
              </Field>
            </div>
            <Field label="Example sentence (optional)">
              <Input
                value={form.example_de}
                placeholder="Ich habe eine gute Idee."
                onChange={(e) => setForm({ ...form, example_de: e.target.value })}
              />
            </Field>
            <Button type="submit" disabled={saving || !form.word.trim() || !form.meaning_en.trim()}>
              {saving ? <Spinner /> : 'Save word'}
            </Button>
          </form>
        </Card>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <Input
          className="max-w-xs"
          value={filter}
          placeholder="Filter words, meanings, tags..."
          onChange={(e) => setFilter(e.target.value)}
        />
        <div className="flex items-center gap-1 text-sm">
          <span className="text-muted">Group by</span>
          <div className="inline-flex overflow-hidden rounded-lg border border-line">
            {(['topic', 'date'] as GroupBy[]).map((g) => (
              <button
                key={g}
                onClick={() => setGroupBy(g)}
                className={cx(
                  'px-3 py-1.5 capitalize transition',
                  groupBy === g
                    ? 'bg-accent text-white'
                    : 'bg-white/70 text-ink hover:bg-accent-soft/50',
                )}
              >
                {g}
              </button>
            ))}
          </div>
        </div>
        <label className="flex items-center gap-1 text-sm text-muted">
          <span>Sort</span>
          <Select value={sortBy} onChange={(e) => setSortBy(e.target.value as SortBy)}>
            <option value="recent">Recent</option>
            <option value="oldest">Oldest</option>
            <option value="az">A–Z</option>
            <option value="za">Z–A</option>
            <option value="level">Level</option>
          </Select>
        </label>
        {selected.size > 0 && (
          <>
            <Button variant="ghost" onClick={() => setSelected(new Set())}>
              Clear ({selected.size})
            </Button>
            <Button variant="danger" onClick={deleteSelected} disabled={deleting}>
              {deleting ? <Spinner /> : `Delete selected (${selected.size})`}
            </Button>
          </>
        )}
      </div>

      {selected.size > 0 && (
        <Card className="space-y-3 p-5">
          <div>
            <h2 className="text-lg font-medium">Generate a practice text</h2>
            <p className="text-sm text-muted">
              Write a {langName} text using your {selected.size} selected word
              {selected.size === 1 ? '' : 's'} and save it with an exercise.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="Title (optional)">
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Mein Text" />
            </Field>
            <Field label="Level (optional)">
              <Select value={level} onChange={(e) => setLevel(e.target.value)}>
                <option value="">Auto</option>
                <option>A1</option>
                <option>A2</option>
                <option>B1</option>
                <option>B2</option>
              </Select>
            </Field>
            <Field label="Instructions (optional)">
              <Input
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder="e.g. write a short dialogue"
              />
            </Field>
          </div>
          {composeError && <div className="text-sm text-danger">{composeError}</div>}
          <Button onClick={compose} disabled={composing}>
            {composing ? <Spinner /> : 'Generate text + exercise'}
          </Button>
        </Card>
      )}

      {words === null ? (
        <Spinner />
      ) : total === 0 ? (
        <Card className="p-8 text-center text-muted">
          No vocabulary yet — add a word above, or generate/import some material.
        </Card>
      ) : groups.length === 0 ? (
        <Card className="p-8 text-center text-muted">No words match your filter.</Card>
      ) : (
        <div className="space-y-5">
          {groups.map((group) => {
            const allSelected = group.items.every((v) => selected.has(v.id))
            return (
              <section key={group.key} className="space-y-2">
                <div className="flex items-center gap-2">
                  <label className="flex cursor-pointer items-center gap-2">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      onChange={(e) => toggleGroup(group.items, e.target.checked)}
                    />
                    <span className="font-medium">{group.label}</span>
                  </label>
                  <Badge>{group.items.length}</Badge>
                </div>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {group.items.map((v) => (
                    <label
                      key={`${group.key}-${v.id}`}
                      className={cx(
                        'group relative flex cursor-pointer gap-2 rounded-xl border bg-card p-3 pr-8 shadow-sm transition',
                        selected.has(v.id)
                          ? 'border-accent'
                          : 'border-line hover:border-accent/40',
                      )}
                    >
                      <input
                        type="checkbox"
                        className="mt-1"
                        checked={selected.has(v.id)}
                        onChange={() => toggle(v.id)}
                      />
                      <div className="min-w-0">
                        <div className="flex items-baseline gap-2">
                          <span className="font-serif">{v.word}</span>
                          <SpeakButton text={v.word} className="self-center" />
                          {v.cefr && <Badge>{v.cefr}</Badge>}
                          {v.ids.length > 1 && <Badge>×{v.ids.length}</Badge>}
                        </div>
                        {v.ipa && <div className="font-mono text-xs text-muted">{v.ipa}</div>}
                        <div className="text-sm text-muted">{v.meaning_en}</div>
                        {v.example_de && (
                          <div className="mt-1 text-xs italic text-muted">{v.example_de}</div>
                        )}
                        {v.material_id != null && (
                          <div className="mt-1.5 flex items-center gap-2">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                                replaceEntry(v, 'easier')
                              }}
                              disabled={replacingId === v.id}
                              className="rounded px-1.5 py-0.5 text-xs text-muted hover:bg-accent-soft/60 disabled:opacity-50"
                              title="Too hard — replace with an easier word"
                            >
                              {replacingId === v.id ? <Spinner /> : 'Too hard'}
                            </button>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                                replaceEntry(v, 'harder')
                              }}
                              disabled={replacingId === v.id}
                              className="rounded px-1.5 py-0.5 text-xs text-muted hover:bg-accent-soft/60 disabled:opacity-50"
                              title="Too easy — replace with a harder word"
                            >
                              Too easy
                            </button>
                          </div>
                        )}
                      </div>
                      <button
                        type="button"
                        aria-label={`Delete ${v.word}`}
                        title="Delete word"
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          deleteEntry(v)
                        }}
                        className="absolute right-1.5 top-1.5 rounded-md px-1.5 text-muted opacity-0 transition hover:bg-danger/10 hover:text-danger group-hover:opacity-100"
                      >
                        ×
                      </button>
                    </label>
                  ))}
                </div>
              </section>
            )
          })}
        </div>
      )}
    </div>
  )
}
