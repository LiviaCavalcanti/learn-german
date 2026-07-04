/**
 * Helpers for the "add material" import flow: recognizing YouTube links (to
 * embed a player), cleaning pasted captions (dropping timestamps), and handing a
 * transcript off to Google Translate.
 *
 * These are pure functions with no DOM/React dependencies so they can be reused
 * from the library form, the material page, or tests.
 */

/** A YouTube video id is exactly 11 URL-safe characters. */
const YT_ID = /^[A-Za-z0-9_-]{11}$/

/** Google Translate's web UI accepts up to ~5000 characters of input at once. */
export const GOOGLE_TRANSLATE_MAX = 5000

function idFromUrl(u: URL): string | null {
  const host = u.hostname.replace(/^www\./, '').replace(/^m\./, '')
  if (host === 'youtu.be') {
    const id = u.pathname.split('/').filter(Boolean)[0]
    return id && YT_ID.test(id) ? id : null
  }
  const isYouTube =
    host === 'youtube.com' ||
    host.endsWith('.youtube.com') ||
    host === 'youtube-nocookie.com' ||
    host.endsWith('.youtube-nocookie.com')
  if (!isYouTube) return null
  const v = u.searchParams.get('v')
  if (v && YT_ID.test(v)) return v
  // /embed/ID, /shorts/ID, /v/ID, /live/ID
  const parts = u.pathname.split('/').filter(Boolean)
  const marker = parts.findIndex((p) => p === 'embed' || p === 'shorts' || p === 'v' || p === 'live')
  if (marker >= 0 && parts[marker + 1] && YT_ID.test(parts[marker + 1])) return parts[marker + 1]
  return null
}

/**
 * Extract the 11-character YouTube video id from a URL (watch, youtu.be, embed,
 * shorts, live) or a bare id. Returns null for anything that isn't a YouTube
 * video, so callers can safely gate an embed on a real id (never an arbitrary
 * iframe src).
 */
export function parseYouTubeId(url: string | null | undefined): string | null {
  if (!url) return null
  const trimmed = url.trim()
  if (!trimmed) return null
  const candidates = /^https?:\/\//i.test(trimmed) ? [trimmed] : [`https://${trimmed}`, trimmed]
  for (const candidate of candidates) {
    try {
      const id = idFromUrl(new URL(candidate))
      if (id) return id
    } catch {
      /* not a parseable URL — fall through */
    }
  }
  return YT_ID.test(trimmed) ? trimmed : null
}

/** Privacy-friendly embed URL for a YouTube video id. */
export function youTubeEmbedUrl(id: string): string {
  return `https://www.youtube-nocookie.com/embed/${id}`
}

/** Public watch URL for a YouTube video id (fallback when embedding is blocked). */
export function youTubeWatchUrl(id: string): string {
  return `https://www.youtube.com/watch?v=${id}`
}

// A clock time such as 0:00, 00:12, 1:02:03, or 00:00:04,000 (SRT/VTT millis).
const TS = String.raw`\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?`
const TS_ONLY_LINE = new RegExp(`^\\s*[\\[(]?${TS}[\\])]?\\s*$`)
const CUE_LINE = new RegExp(`^\\s*${TS}\\s*--?>\\s*${TS}.*$`)
// A standalone timestamp token anywhere in a line (start, inline, or bracketed):
// preceded by start-of-line or whitespace and followed by whitespace or end, so
// digits embedded in words are left alone. Catches both `0:00 caption` and the
// single-line "0:00 hallo 0:04 heute" shape YouTube produces when copied.
const TS_TOKEN = new RegExp(`(^|\\s)[\\[(]?${TS}[\\])]?(?=\\s|$)`, 'g')

/**
 * Strip timestamps from a pasted transcript so only the words remain.
 *
 * Handles the common shapes: YouTube's "Show transcript" panel (a timestamp on
 * its own line, or `0:00 caption` per line, or everything on one line as
 * `0:00 hallo 0:04 heute …`), inline `[00:12]` / `(1:03)` markers, and SRT/VTT
 * cue lines + sequence numbers. Any `M:SS`, `H:MM:SS`, or millisecond timestamp
 * that stands as its own token is removed; digits inside words are left alone.
 */
export function stripTimestamps(text: string): string {
  if (!text) return ''
  const lines = text.split(/\r?\n/)
  const out: string[] = []
  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim()
    if (/^WEBVTT/i.test(trimmed)) continue
    if (CUE_LINE.test(lines[i])) continue
    if (TS_ONLY_LINE.test(lines[i])) continue
    // SRT sequence number: a lone integer directly before a cue line.
    if (/^\d+$/.test(trimmed) && i + 1 < lines.length && CUE_LINE.test(lines[i + 1])) continue
    const cleaned = lines[i]
      .replace(TS_TOKEN, ' ')
      .replace(/[ \t]{2,}/g, ' ')
      .trim()
    out.push(cleaned)
  }
  return out.join('\n').replace(/\n{3,}/g, '\n\n').trim()
}

/**
 * Build a Google Translate URL that opens with `text` pre-filled as the source.
 * Input longer than {@link GOOGLE_TRANSLATE_MAX} is clipped (the site truncates
 * anyway); the caller can warn the user to translate long transcripts in parts.
 */
export function googleTranslateUrl(text: string, source: string, target: string): string {
  const clipped = text.slice(0, GOOGLE_TRANSLATE_MAX)
  return (
    `https://translate.google.com/?sl=${encodeURIComponent(source)}` +
    `&tl=${encodeURIComponent(target)}&text=${encodeURIComponent(clipped)}&op=translate`
  )
}
