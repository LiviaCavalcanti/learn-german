import { useRef, useState, type MouseEvent } from 'react'
import { DictionaryPopover } from './HoverDictionary'

const TOKEN_RE = /([A-Za-zÄÖÜäöüß]+)/

type Active = { word: string; x: number; y: number }

export function TokenizedText({ text, className }: { text: string; className?: string }) {
  const [active, setActive] = useState<Active | null>(null)
  const timer = useRef<number | null>(null)
  const parts = text.split(TOKEN_RE)

  function clearTimer() {
    if (timer.current) {
      window.clearTimeout(timer.current)
      timer.current = null
    }
  }

  function show(e: MouseEvent<HTMLSpanElement>, word: string) {
    clearTimer()
    const rect = e.currentTarget.getBoundingClientRect()
    setActive({ word, x: rect.left, y: rect.bottom })
  }

  function hideSoon() {
    clearTimer()
    timer.current = window.setTimeout(() => setActive(null), 160)
  }

  return (
    <span className={className}>
      {parts.map((part, i) =>
        TOKEN_RE.test(part) && part.length > 1 ? (
          <span
            key={i}
            className="cursor-help rounded hover:bg-accent-soft/70"
            onMouseEnter={(e) => show(e, part)}
            onMouseLeave={hideSoon}
          >
            {part}
          </span>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
      {active && (
        <DictionaryPopover
          word={active.word}
          x={active.x}
          y={active.y}
          onEnter={clearTimer}
          onLeave={hideSoon}
        />
      )}
    </span>
  )
}
