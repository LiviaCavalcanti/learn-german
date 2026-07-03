import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../../lib/api'
import type {
  ChatContext,
  ChatMessage,
  ChatSession,
  ChatSessionDetail,
  LearnerProfile,
  MaterialSummary,
} from '../../lib/types'
import { Badge, Button, Card, cx, Select, Spinner, Textarea } from '../../components/ui'
import { TokenizedText } from '../../components/TokenizedText'
import { AddToReviewModal } from './AddToReviewModal'

export default function Tutor() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [sessions, setSessions] = useState<ChatSession[] | null>(null)
  const [activeId, setActiveId] = useState<number | null>(null)
  const [detail, setDetail] = useState<ChatSessionDetail | null>(null)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [materials, setMaterials] = useState<MaterialSummary[]>([])
  const [attach, setAttach] = useState<ChatContext | null>(null)
  const [profile, setProfile] = useState<LearnerProfile | null>(null)
  const [cardFor, setCardFor] = useState<string | null>(null)
  const [savedNote, setSavedNote] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [chatsOpen, setChatsOpen] = useState(
    () =>
      typeof localStorage === 'undefined' || localStorage.getItem('tutor-chats-open') !== 'false',
  )
  const endRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    api
      .tutorSessions()
      .then((s) => {
        setSessions(s)
        if (s.length && activeId == null) setActiveId(s[0].id)
      })
      .catch(() => setSessions([]))
    api.materials().then(setMaterials).catch(() => {})
    api.tutorProfile().then(setProfile).catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Deep-link: /tutor?material=<id> pre-attaches that material as context.
  useEffect(() => {
    const materialId = Number(searchParams.get('material'))
    if (materialId && materials.length) {
      const m = materials.find((x) => x.id === materialId)
      setAttach({ kind: 'material', id: materialId, label: m?.title ?? `Material #${materialId}` })
      searchParams.delete('material')
      setSearchParams(searchParams, { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [materials])

  useEffect(() => {
    if (activeId == null) {
      setDetail(null)
      return
    }
    api.tutorSession(activeId).then(setDetail).catch(() => setDetail(null))
  }, [activeId])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [detail?.messages.length, sending])

  async function newSession() {
    setActiveId(null)
    setDetail(null)
    setInput('')
  }

  async function deleteSession(id: number) {
    if (!window.confirm('Delete this conversation?')) return
    await api.tutorDeleteSession(id)
    const rest = (sessions ?? []).filter((s) => s.id !== id)
    setSessions(rest)
    if (activeId === id) setActiveId(rest[0]?.id ?? null)
  }

  async function send() {
    const text = input.trim()
    if (!text || sending) return
    setSending(true)
    setError(null)
    let id = activeId
    const tempUser: ChatMessage = {
      id: -Date.now(),
      session_id: id ?? 0,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    try {
      if (id == null) {
        const created = await api.tutorCreateSession({
          title: text.slice(0, 40),
          context: attach ?? undefined,
        })
        id = created.id
        setActiveId(id)
        setDetail({ ...created, messages: [] })
      }
      const sessionId = id
      setDetail((d) => (d && d.id === sessionId ? { ...d, messages: [...d.messages, tempUser] } : d))
      setInput('')
      const turn = await api.tutorSend(sessionId, { message: text, context: attach ?? undefined })
      setDetail((d) =>
        d && d.id === sessionId
          ? {
              ...d,
              messages: [...d.messages.filter((m) => m.id !== tempUser.id), turn.user_message, turn.teacher_message],
            }
          : d,
      )
      api.tutorSessions().then(setSessions).catch(() => {})
      api.tutorProfile().then(setProfile).catch(() => {})
    } catch (e) {
      setDetail((d) =>
        d ? { ...d, messages: d.messages.filter((m) => m.id !== tempUser.id) } : d,
      )
      setError(e instanceof Error ? e.message : 'Could not reach the teacher.')
    } finally {
      setSending(false)
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  function toggleChats() {
    setChatsOpen((v) => {
      const next = !v
      try {
        localStorage.setItem('tutor-chats-open', String(next))
      } catch {
        /* ignore unavailable storage */
      }
      return next
    })
  }

  const messages = detail?.messages ?? []

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl">Teacher</h1>
        <p className="text-muted">
          Chat with your language teacher. Attach a material, and save answers to your review deck.
        </p>
      </header>

      <div className={cx('grid gap-6', chatsOpen ? 'grid-cols-[15rem_1fr]' : 'grid-cols-1')}>
        {/* Sessions */}
        {chatsOpen && (
        <div className="space-y-2">
          <div className="flex items-center gap-1">
            <Button variant="soft" className="flex-1" onClick={newSession}>
              + New chat
            </Button>
            <button
              onClick={toggleChats}
              title="Hide chats"
              aria-label="Hide chats"
              className="shrink-0 rounded-lg px-2.5 py-2 text-muted transition hover:bg-accent-soft hover:text-ink"
            >
              «
            </button>
          </div>
          <div className="space-y-1">
            {(sessions ?? []).map((s) => (
              <div
                key={s.id}
                className={
                  'group flex items-center gap-1 rounded-lg px-3 py-2 text-sm transition ' +
                  (s.id === activeId ? 'bg-accent-soft text-ink' : 'text-muted hover:bg-accent-soft/50')
                }
              >
                <button className="min-w-0 flex-1 truncate text-left" onClick={() => setActiveId(s.id)}>
                  {s.title}
                </button>
                <button
                  className="shrink-0 text-muted opacity-0 transition group-hover:opacity-100 hover:text-danger"
                  title="Delete conversation"
                  onClick={() => deleteSession(s.id)}
                >
                  ✕
                </button>
              </div>
            ))}
            {sessions && sessions.length === 0 && (
              <p className="px-3 py-2 text-xs text-muted">No conversations yet.</p>
            )}
          </div>
        </div>
        )}

        {/* Conversation */}
        <div className="space-y-4">
          {!chatsOpen && (
            <div className="flex items-center gap-2">
              <Button variant="soft" onClick={toggleChats}>
                ☰ Chats
              </Button>
              <Button variant="ghost" onClick={newSession}>
                + New chat
              </Button>
            </div>
          )}
          <ProfilePanel profile={profile} />

          <Card className="flex h-[58vh] flex-col">
            <div className="flex-1 space-y-4 overflow-y-auto p-5">
              {messages.length === 0 && !sending && (
                <div className="flex h-full items-center justify-center text-center text-muted">
                  <div>
                    <div className="font-serif text-xl text-ink">Frag deine Lehrerin</div>
                    <p className="mt-1 text-sm">
                      Ask anything about the language you're learning — grammar, a word, a sentence to check.
                    </p>
                  </div>
                </div>
              )}
              {messages.map((m) => (
                <MessageBubble
                  key={m.id}
                  message={m}
                  onAddToReview={() => setCardFor(m.content)}
                />
              ))}
              {sending && (
                <div className="flex items-center gap-2 text-sm text-muted">
                  <Spinner /> Die Lehrerin schreibt…
                </div>
              )}
              <div ref={endRef} />
            </div>

            <div className="border-t border-line p-3">
              <AttachBar
                attach={attach}
                materials={materials}
                onAttachMaterial={(id, label) =>
                  setAttach(id ? { kind: 'material', id, label } : null)
                }
              />
              {error && <p className="px-1 pb-2 text-sm text-danger">{error}</p>}
              <div className="flex items-end gap-2">
                <Textarea
                  rows={2}
                  className="flex-1 resize-none"
                  placeholder="Schreib deine Frage… (Enter zum Senden, Shift+Enter für neue Zeile)"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={onKeyDown}
                />
                <Button onClick={send} disabled={sending || !input.trim()}>
                  {sending ? <Spinner /> : 'Send'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {cardFor !== null && (
        <AddToReviewModal
          sourceText={cardFor}
          context={attach ?? undefined}
          defaultLevel="A2"
          onClose={() => setCardFor(null)}
          onSaved={() => {
            setCardFor(null)
            setSavedNote(true)
            window.setTimeout(() => setSavedNote(false), 2500)
          }}
        />
      )}

      {savedNote && (
        <div className="fixed bottom-6 right-6 rounded-lg border border-success/40 bg-success/10 px-4 py-2 text-sm text-success shadow">
          Saved to your review deck ✓
        </div>
      )}
    </div>
  )
}

function MessageBubble({
  message,
  onAddToReview,
}: {
  message: ChatMessage
  onAddToReview: () => void
}) {
  const isUser = message.role === 'user'
  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-accent px-4 py-2 text-sm text-white">
          {message.content}
        </div>
      </div>
    )
  }
  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-2">
        <div className="rounded-2xl rounded-bl-sm border border-line bg-paper/60 px-4 py-2">
          <TokenizedText text={message.content} className="block whitespace-pre-wrap text-sm leading-7" />
        </div>
        <button
          className="ml-1 text-xs text-muted underline-offset-2 hover:text-accent hover:underline"
          onClick={onAddToReview}
        >
          + Add to review deck
        </button>
      </div>
    </div>
  )
}

function ProfilePanel({ profile }: { profile: LearnerProfile | null }) {
  const [open, setOpen] = useState(false)
  const strengths = profile?.strengths ?? []
  const difficulties = profile?.difficulties ?? []
  const empty = strengths.length === 0 && difficulties.length === 0 && !profile?.focus

  return (
    <Card className="p-4">
      <button
        className="flex w-full items-center justify-between text-left"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="text-sm font-medium">What your teacher knows about you</span>
        <span className="text-xs text-muted">{open ? 'Hide' : 'Show'}</span>
      </button>
      {open && (
        <div className="mt-3 space-y-3 text-sm">
          {empty && (
            <p className="text-muted">
              The teacher will learn your strengths and difficulties as you chat.
            </p>
          )}
          {profile?.focus && (
            <div>
              <span className="text-xs uppercase tracking-wide text-muted">Focus</span>
              <p>{profile.focus}</p>
            </div>
          )}
          {strengths.length > 0 && (
            <div>
              <span className="text-xs uppercase tracking-wide text-muted">Strengths</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {strengths.map((s) => (
                  <span
                    key={s}
                    className="rounded-full bg-success/15 px-2 py-0.5 text-xs text-success"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
          {difficulties.length > 0 && (
            <div>
              <span className="text-xs uppercase tracking-wide text-muted">Working on</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {difficulties.map((d) => (
                  <span key={d} className="rounded-full bg-danger/10 px-2 py-0.5 text-xs text-danger">
                    {d}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

function AttachBar({
  attach,
  materials,
  onAttachMaterial,
}: {
  attach: ChatContext | null
  materials: MaterialSummary[]
  onAttachMaterial: (id: number | null, label: string) => void
}) {
  return (
    <div className="mb-2 flex flex-wrap items-center gap-2">
      {attach ? (
        <span className="inline-flex items-center gap-2 rounded-full border border-accent/40 bg-accent-soft px-3 py-1 text-xs">
          <Badge className="border-none bg-transparent px-0">{attach.kind}</Badge>
          <span className="max-w-[16rem] truncate">{attach.label ?? attach.text ?? ''}</span>
          <button className="text-muted hover:text-danger" onClick={() => onAttachMaterial(null, '')}>
            ✕
          </button>
        </span>
      ) : (
        <>
          <span className="text-xs text-muted">Attach:</span>
          <Select
            className="max-w-[16rem] text-xs"
            value=""
            onChange={(e) => {
              const id = Number(e.target.value)
              const m = materials.find((x) => x.id === id)
              if (id) onAttachMaterial(id, m?.title ?? `Material #${id}`)
            }}
          >
            <option value="">a material…</option>
            {materials.map((m) => (
              <option key={m.id} value={m.id}>
                {m.title} ({m.level})
              </option>
            ))}
          </Select>
        </>
      )}
    </div>
  )
}
