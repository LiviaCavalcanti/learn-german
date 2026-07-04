import { parseYouTubeId, youTubeEmbedUrl, youTubeWatchUrl } from '../lib/importHelpers'
import { cx } from './ui'

/**
 * Inline YouTube player for a material's source link. Renders nothing when the
 * URL isn't a recognizable YouTube video, so the embed is always gated on a real
 * 11-character video id (never an arbitrary iframe src).
 *
 * The iframe fills a fixed 16:9 wrapper (so it can never collapse to zero
 * height), and a "Watch on YouTube" link is always shown as a fallback for
 * videos whose owner has disabled embedding.
 */
export function VideoEmbed({
  url,
  className,
  title = 'Video',
}: {
  url: string | null | undefined
  className?: string
  title?: string
}) {
  const id = parseYouTubeId(url)
  if (!id) return null
  return (
    <div className={cx('overflow-hidden rounded-xl border border-line bg-card shadow-sm', className)}>
      <div className="relative aspect-video w-full bg-black">
        <iframe
          className="absolute inset-0 h-full w-full"
          src={youTubeEmbedUrl(id)}
          title={title}
          loading="lazy"
          referrerPolicy="strict-origin-when-cross-origin"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
        />
      </div>
      <div className="flex items-center justify-between gap-2 px-3 py-1.5 text-xs text-muted">
        <span>Not playing here? The owner may block embedding.</span>
        <a
          href={youTubeWatchUrl(id)}
          target="_blank"
          rel="noreferrer noopener"
          className="whitespace-nowrap font-medium text-accent hover:underline"
        >
          Watch on YouTube ↗
        </a>
      </div>
    </div>
  )
}

