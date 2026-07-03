import { getSpeech, getSpeechLang } from '../lib/pronunciation'
import { cx } from './ui'

/** Small speaker button that reads a word aloud via the Web Speech API. */
export function SpeakButton({
  text,
  lang,
  className,
  title = 'Hear pronunciation',
}: {
  text: string
  lang?: string
  className?: string
  title?: string
}) {
  const speech = getSpeech()
  if (!speech.available) return null
  return (
    <button
      type="button"
      aria-label={`Hear ${text}`}
      title={title}
      onClick={(e) => {
        e.preventDefault()
        e.stopPropagation()
        // Resolve the target language at click time so it always reflects the
        // current selection (a render-time default can be stale after switching).
        speech.speak(text, lang ?? getSpeechLang())
      }}
      className={cx(
        'inline-flex shrink-0 items-center rounded-md px-1 py-0.5 text-muted transition hover:bg-accent-soft/60 hover:text-ink',
        className,
      )}
    >
      <SpeakerIcon />
    </button>
  )
}

function SpeakerIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      width="15"
      height="15"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M11 5 6 9H2v6h4l5 4V5z" />
      <path d="M15.5 8.5a5 5 0 0 1 0 7" />
      <path d="M18.5 5.5a9 9 0 0 1 0 13" />
    </svg>
  )
}
