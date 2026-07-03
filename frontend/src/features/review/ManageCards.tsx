import { useEffect, useMemo, useState } from 'react'
import { api } from '../../lib/api'
import type { ReviewCard } from '../../lib/types'
import { Badge, Button, Card, Input, Select, Spinner } from '../../components/ui'
import { CardEditor } from './CardEditor'

type TypeFilter = 'all' | 'vocab' | 'exercise'

export function ManageCards({ onChanged }: { onChanged?: () => void }) {
  const [cards, setCards] = useState<ReviewCard[] | null>(null)
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('all')
  const [q, setQ] = useState('')
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [editing, setEditing] = useState<ReviewCard | null>(null)
  const [busy, setBusy] = useState(false)

  function load() {
    setCards(null)
    api
      .reviewCards({ item_type: typeFilter === 'all' ? undefined : typeFilter, limit: 1000 })
      .then((c) => {
        setCards(c)
        setSelected(new Set())
      })
      .catch(() => setCards([]))
  }
  useEffect(load, [typeFilter])

  const filtered = useMemo(() => {
    if (!cards) return []
    const needle = q.trim().toLowerCase()
    if (!needle) return cards
    return cards.filter((c) => summaryText(c).toLowerCase().includes(needle))
  }, [cards, q])

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (selected.size === filtered.length) setSelected(new Set())
    else setSelected(new Set(filtered.map((c) => c.srstate_id)))
  }

  async function removeIds(ids: number[]) {
    if (ids.length === 0) return
    setBusy(true)
    try {
      await api.reviewRemoveCards(ids)
      load()
      onChanged?.()
    } finally {
      setBusy(false)
    }
  }

  async function deleteIds(ids: number[]) {
    if (ids.length === 0) return
    const msg =
      ids.length === 1
        ? 'Delete this item entirely? It will be removed from your library.'
        : `Delete ${ids.length} items entirely? They will be removed from your library.`
    if (!window.confirm(msg)) return
    setBusy(true)
    try {
      await api.reviewDeleteCards(ids)
      load()
      onChanged?.()
    } finally {
      setBusy(false)
    }
  }

  if (cards === null) return <Spinner />

  const selectedIds = [...selected]
  const allChecked = filtered.length > 0 && selected.size === filtered.length

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value as TypeFilter)}>
          <option value="all">All cards</option>
          <option value="vocab">Vocab</option>
          <option value="exercise">Exercises</option>
        </Select>
        <Input
          className="max-w-xs"
          placeholder="Filter…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <span className="text-sm text-muted">{filtered.length} card(s)</span>
      </div>

      {selectedIds.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-line bg-paper/60 px-3 py-2">
          <span className="text-sm">{selectedIds.length} selected</span>
          <div className="flex-1" />
          <Button variant="soft" disabled={busy} onClick={() => removeIds(selectedIds)}>
            Remove from review
          </Button>
          <Button variant="danger" disabled={busy} onClick={() => deleteIds(selectedIds)}>
            Delete
          </Button>
        </div>
      )}

      {filtered.length === 0 ? (
        <Card className="p-8 text-center text-muted">No cards.</Card>
      ) : (
        <Card className="divide-y divide-line">
          <label className="flex items-center gap-3 px-4 py-2 text-xs uppercase tracking-wide text-muted">
            <input type="checkbox" checked={allChecked} onChange={toggleAll} />
            Select all
          </label>
          {filtered.map((card) => (
            <div key={card.srstate_id} className="flex items-start gap-3 px-4 py-3">
              <input
                type="checkbox"
                className="mt-1"
                checked={selected.has(card.srstate_id)}
                onChange={() => toggle(card.srstate_id)}
              />
              <div className="min-w-0 flex-1">
                <CardSummary card={card} />
              </div>
              <div className="flex shrink-0 items-center gap-1">
                <Button variant="ghost" onClick={() => setEditing(card)}>
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  disabled={busy}
                  onClick={() => removeIds([card.srstate_id])}
                  title="Remove from review (keeps the item)"
                >
                  Remove
                </Button>
                <Button
                  variant="danger"
                  disabled={busy}
                  onClick={() => deleteIds([card.srstate_id])}
                  title="Delete the item entirely"
                >
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </Card>
      )}

      {editing && (
        <CardEditor
          card={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            load()
            onChanged?.()
          }}
        />
      )}
    </div>
  )
}

function summaryText(card: ReviewCard): string {
  const d = card.item || {}
  if (card.item_type === 'vocab') return `${d.word ?? ''} ${d.meaning_en ?? ''}`
  return `${d.type ?? ''} ${d.instructions ?? ''}`
}

function CardSummary({ card }: { card: ReviewCard }) {
  const d = card.item || {}
  const due = card.is_due ? 'due now' : new Date(card.due).toLocaleDateString()
  return (
    <div>
      {card.item_type === 'vocab' ? (
        <div>
          <span className="font-serif text-lg">{String(d.word ?? '')}</span>
          <span className="text-muted"> · {String(d.meaning_en ?? '')}</span>
        </div>
      ) : (
        <div className="truncate">
          <Badge className="mr-2">{String(d.type ?? 'exercise')}</Badge>
          <span className="text-sm">{String(d.instructions ?? '')}</span>
        </div>
      )}
      <div className="mt-1 flex flex-wrap gap-1 text-xs text-muted">
        {d.cefr && <Badge>{String(d.cefr)}</Badge>}
        <Badge>{card.state}</Badge>
        <Badge>{due}</Badge>
        <Badge>{card.reps} reps</Badge>
      </div>
    </div>
  )
}
