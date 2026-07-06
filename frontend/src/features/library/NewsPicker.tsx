import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../lib/api'
import type { NewsArticle, NewsSource } from '../../lib/types'
import { Badge, Button, Card, Select, Spinner } from '../../components/ui'

/**
 * Fetch the day's German news from a chosen source and let the learner pick which
 * article to add. Each pick is fetched, translated, and (optionally) turned into
 * vocabulary + exercises via the backend `/news` endpoints.
 */
export default function NewsPicker({ onImported }: { onImported: () => void }) {
  const [sources, setSources] = useState<NewsSource[]>([])
  const [available, setAvailable] = useState(true)
  const [source, setSource] = useState('nachrichtenleicht')
  const [articles, setArticles] = useState<NewsArticle[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generate, setGenerate] = useState(true)
  const [busyUrl, setBusyUrl] = useState<string | null>(null)
  const [added, setAdded] = useState<Record<string, number>>({})

  useEffect(() => {
    api
      .newsSources()
      .then((r) => {
        setSources(r.sources)
        setAvailable(r.available)
        if (r.sources.length && !r.sources.some((s) => s.key === source)) {
          setSource(r.sources[0].key)
        }
      })
      .catch(() => setAvailable(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function fetchNews() {
    setLoading(true)
    setError(null)
    setArticles(null)
    try {
      setArticles(await api.newsLatest(source, 12))
    } catch {
      setError('Could not fetch the news. Is the backend running with the "daily" extra installed?')
    } finally {
      setLoading(false)
    }
  }

  async function add(article: NewsArticle) {
    setBusyUrl(article.url)
    setError(null)
    try {
      const r = await api.newsImport({
        source: article.source,
        url: article.url,
        title: article.title,
        level: article.level,
        generate,
      })
      setAdded((prev) => ({ ...prev, [article.url]: r.material_id }))
      onImported()
    } catch (e) {
      setError(`Could not add “${article.title}”. ${String(e)}`)
    } finally {
      setBusyUrl(null)
    }
  }

  if (!available) {
    return (
      <Card className="p-4 text-sm text-muted">
        Fetching news needs the optional <code>daily</code> extra. Install it and restart the
        backend: <code>cd backend &amp;&amp; uv sync --extra daily</code>.
      </Card>
    )
  }

  return (
    <Card className="space-y-4 p-5">
      <div className="flex flex-wrap items-end gap-3">
        <label className="block space-y-1">
          <span className="block text-xs font-medium text-muted">Source</span>
          <Select value={source} onChange={(e) => setSource(e.target.value)}>
            {sources.map((s) => (
              <option key={s.key} value={s.key}>
                {s.label} · {s.level}
              </option>
            ))}
          </Select>
        </label>
        <Button type="button" onClick={fetchNews} disabled={loading}>
          {loading ? <Spinner /> : `Fetch today\u2019s news`}
        </Button>
        <label className="ml-auto flex items-center gap-2 text-xs text-muted">
          <input
            type="checkbox"
            checked={generate}
            onChange={(e) => setGenerate(e.target.checked)}
          />
          Generate exercises now
        </label>
      </div>

      {error && <p className="text-xs text-danger">{error}</p>}

      {articles && articles.length === 0 && (
        <p className="text-sm text-muted">No articles found right now — try another source.</p>
      )}

      {articles && articles.length > 0 && (
        <ul className="space-y-2">
          {articles.map((a) => {
            const addedId = added[a.url]
            return (
              <li
                key={a.url}
                className="flex items-start justify-between gap-3 rounded-lg border border-line bg-paper/50 p-3"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <Badge>{a.level}</Badge>
                    <span className="font-serif">{a.title}</span>
                  </div>
                  {a.summary && <p className="mt-1 line-clamp-2 text-xs text-muted">{a.summary}</p>}
                  <a
                    href={a.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-accent"
                  >
                    Read original ↗
                  </a>
                </div>
                {addedId ? (
                  <Link to={`/materials/${addedId}`} className="shrink-0">
                    <Button type="button" variant="soft">
                      Added ✓ — open
                    </Button>
                  </Link>
                ) : (
                  <Button
                    type="button"
                    variant="soft"
                    className="shrink-0"
                    disabled={busyUrl === a.url}
                    onClick={() => add(a)}
                  >
                    {busyUrl === a.url ? <Spinner /> : 'Add'}
                  </Button>
                )}
              </li>
            )
          })}
        </ul>
      )}

      <p className="text-xs text-muted">
        The article you pick is fetched, translated, and (optionally) turned into vocabulary and
        exercises — then it appears in your library below.
      </p>
    </Card>
  )
}
