/**
 * Flag — small rounded language flags drawn as inline SVG.
 *
 * We deliberately avoid emoji flags (🇩🇪, 🇪🇸, …): on Windows browsers they don't
 * render as flags at all (they fall back to two-letter codes). Inline SVGs look
 * identical on every platform and match the app's warm, hand-made aesthetic.
 *
 * Size is set by the caller via `className` (e.g. `h-12 w-16`); the SVG fills the
 * box and is cropped with `slice`, so flags with different ratios stay tidy.
 */
import type { ReactNode } from 'react'
import { cx } from './ui'

const FLAGS: Record<string, ReactNode> = {
  de: (
    <svg viewBox="0 0 5 3" preserveAspectRatio="xMidYMid slice" className="h-full w-full">
      <rect width="5" height="3" fill="#000000" />
      <rect y="1" width="5" height="1" fill="#DD0000" />
      <rect y="2" width="5" height="1" fill="#FFCE00" />
    </svg>
  ),
  es: (
    <svg viewBox="0 0 3 2" preserveAspectRatio="xMidYMid slice" className="h-full w-full">
      <rect width="3" height="2" fill="#AA151B" />
      <rect y="0.5" width="3" height="1" fill="#F1BF00" />
    </svg>
  ),
  fr: (
    <svg viewBox="0 0 3 2" preserveAspectRatio="xMidYMid slice" className="h-full w-full">
      <rect width="3" height="2" fill="#FFFFFF" />
      <rect width="1" height="2" fill="#0055A4" />
      <rect x="2" width="1" height="2" fill="#EF4135" />
    </svg>
  ),
  it: (
    <svg viewBox="0 0 3 2" preserveAspectRatio="xMidYMid slice" className="h-full w-full">
      <rect width="3" height="2" fill="#FFFFFF" />
      <rect width="1" height="2" fill="#009246" />
      <rect x="2" width="1" height="2" fill="#CE2B37" />
    </svg>
  ),
  en: (
    <svg viewBox="0 0 60 30" preserveAspectRatio="xMidYMid slice" className="h-full w-full">
      <clipPath id="flag-uk-clip">
        <path d="M0,0 v30 h60 v-30 z" />
      </clipPath>
      <clipPath id="flag-uk-diagonals">
        <path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z" />
      </clipPath>
      <g clipPath="url(#flag-uk-clip)">
        <path d="M0,0 v30 h60 v-30 z" fill="#012169" />
        <path d="M0,0 L60,30 M60,0 L0,30" stroke="#FFFFFF" strokeWidth="6" />
        <path
          d="M0,0 L60,30 M60,0 L0,30"
          clipPath="url(#flag-uk-diagonals)"
          stroke="#C8102E"
          strokeWidth="4"
        />
        <path d="M30,0 v30 M0,15 h60" stroke="#FFFFFF" strokeWidth="10" />
        <path d="M30,0 v30 M0,15 h60" stroke="#C8102E" strokeWidth="6" />
      </g>
    </svg>
  ),
}

export function Flag({ code, className }: { code: string; className?: string }) {
  const svg = FLAGS[code?.toLowerCase()]
  return (
    <span
      role="img"
      aria-label={`${code} flag`}
      className={cx(
        'inline-flex shrink-0 items-center justify-center overflow-hidden rounded border border-line/70 bg-line/40 shadow-sm',
        className,
      )}
    >
      {svg ?? (
        <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">{code}</span>
      )}
    </span>
  )
}
