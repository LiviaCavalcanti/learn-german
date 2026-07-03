import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { DictLookup } from '../lib/types'
import { Badge, Button, Spinner } from './ui'
import { SpeakButton } from './SpeakButton'

export function DictionaryPopover({
  word,
  x,
  y,
  onEnter,
  onLeave,
}: {
  word: string
  x: number
  y: number
  onEnter: () => void
  onLeave: () => void
}) {
  const [data, setData] = useState<DictLookup | null>(null)
  const [loading, setLoading] = useState(true)
  const [added, setAdded] = useState(false)

  useEffect(() => {
    let alive = true
    setLoading(true)
    setAdded(false)
    api
      .dictLookup(word)
      .then((d) => {
        if (alive) {
          setData(d)
          setLoading(false)
        }
      })
      .catch(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [word])

  const entry = data?.entries?.[0]

  async function addVocab() {
    if (!data) return
    const meaning = entry?.translations?.slice(0, 3).join(', ') || word
    await api.createVocab({
      word,
      lemma: data.lemma || word,
      meaning_en: meaning,
      pos: entry?.pos ?? null,
    })
    setAdded(true)
  }

  const left = Math.max(8, Math.min(x, window.innerWidth - 300))

  return (
    <div
      className="fixed z-50 w-72 rounded-xl border border-line bg-card p-3 shadow-lg"
      style={{ left, top: y + 6 }}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
    >
      <div className="flex items-baseline justify-between gap-2">
        <div className="flex items-baseline gap-1">
          <span className="font-serif text-lg">{word}</span>
          <SpeakButton text={word} className="self-center" />
        </div>
        {data?.lemma && data.lemma.toLowerCase() !== word.toLowerCase() && (
          <Badge>→ {data.lemma}</Badge>
        )}
      </div>

      {loading ? (
        <div className="py-3">
          <Spinner />
        </div>
      ) : entry ? (
        <div className="mt-1 space-y-1.5">
          {(entry.pos || entry.ipa) && (
            <div className="flex items-center gap-2 text-xs text-muted">
              {entry.pos && <span>{entry.pos}</span>}
              {entry.ipa && <span className="font-mono">{entry.ipa}</span>}
            </div>
          )}
          <div className="text-sm">{entry.translations.slice(0, 6).join(', ')}</div>
          {entry.senses?.[0] && (
            <div className="line-clamp-3 text-xs text-muted">{entry.senses[0]}</div>
          )}
        </div>
      ) : (
        <div className="mt-2 text-xs text-muted">
          No entry{data && !data.available ? ' — run the dictionary loader' : ''}.
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Button variant="soft" onClick={() => navigator.clipboard.writeText(word)}>
          Copy
        </Button>
        {data && (
          <a
            className="inline-flex items-center rounded-lg bg-accent-soft px-3 py-2 text-sm text-ink hover:brightness-95"
            href={data.google_translate_url}
            target="_blank"
            rel="noreferrer"
          >
            Google Translate
          </a>
        )}
        <Button variant="ghost" onClick={addVocab} disabled={added}>
          {added ? 'Added ✓' : '+ Vocab'}
        </Button>
      </div>
    </div>
  )
}
