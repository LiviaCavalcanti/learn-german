import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { cx } from './ui'
import { useLanguage } from '../contexts/LanguageContext'

const nav = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/course', label: 'Course' },
  { to: '/library', label: 'Library' },
  { to: '/vocab', label: 'Vocabulary' },
  { to: '/conjugation', label: 'Conjugation' },
  { to: '/tutor', label: 'Teacher' },
  { to: '/review', label: 'Review' },
  { to: '/import', label: 'Import' },
]

export default function Layout() {
  const [navOpen, setNavOpen] = useState(
    () => typeof localStorage === 'undefined' || localStorage.getItem('nav-open') !== 'false',
  )
  const { pathname } = useLocation()
  const { targetProfile, reset } = useLanguage()
  // Hide the Conjugation page for languages that don't have a verb-conjugation feature.
  const items = nav.filter(
    (n) => n.to !== '/conjugation' || (targetProfile?.has_conjugation ?? true),
  )
  // The teacher/chat page spans the full width; reading pages stay in a centered column.
  const wide = pathname.startsWith('/tutor')

  function toggleNav() {
    setNavOpen((v) => {
      const next = !v
      try {
        localStorage.setItem('nav-open', String(next))
      } catch {
        /* ignore unavailable storage */
      }
      return next
    })
  }

  return (
    <div className="flex min-h-screen">
      {navOpen ? (
        <aside className="w-60 shrink-0 border-r border-line bg-card/60 px-4 py-6">
          <div className="mb-8 flex items-start justify-between px-2">
            <div>
              <div className="font-serif text-2xl font-semibold">Sprachheft</div>
              <div className="text-xs text-muted">
                {targetProfile ? `${targetProfile.name} learning notebook` : 'Language notebook'}
              </div>
            </div>
            <button
              onClick={toggleNav}
              title="Collapse sidebar"
              aria-label="Collapse sidebar"
              className="-mr-1 rounded-md p-1 text-muted transition hover:bg-accent-soft hover:text-ink"
            >
              «
            </button>
          </div>
          <nav className="space-y-1">
            {items.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  cx(
                    'block rounded-lg px-3 py-2 text-sm transition',
                    isActive
                      ? 'bg-accent-soft font-medium text-ink'
                      : 'text-muted hover:bg-accent-soft/50',
                  )
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
          {targetProfile && (
            <button
              type="button"
              onClick={reset}
              title="Change language"
              className="mt-6 flex w-full items-center justify-between rounded-lg border border-line px-3 py-2 text-left text-xs text-muted transition hover:bg-accent-soft/50"
            >
              <span>
                Learning <span className="font-medium text-ink">{targetProfile.endonym}</span>
              </span>
              <span aria-hidden>↺</span>
            </button>
          )}
        </aside>
      ) : (
        <div className="fixed left-3 top-3 z-20 flex flex-col gap-2">
          <button
            onClick={toggleNav}
            title="Open sidebar"
            aria-label="Open sidebar"
            className="rounded-md border border-line bg-card p-2 text-muted shadow-sm transition hover:bg-accent-soft hover:text-ink"
          >
            ☰
          </button>
          {targetProfile && (
            <button
              type="button"
              onClick={reset}
              title="Change language"
              aria-label="Change language"
              className="rounded-md border border-line bg-card p-2 text-muted shadow-sm transition hover:bg-accent-soft hover:text-ink"
            >
              ↺
            </button>
          )}
        </div>
      )}
      <main className="min-w-0 flex-1">
        <div
          className={cx(
            'py-10 pr-8',
            wide ? 'max-w-none' : 'mx-auto max-w-5xl',
            navOpen ? 'pl-8' : 'pl-16',
          )}
        >
          <Outlet />
        </div>
      </main>
    </div>
  )
}
