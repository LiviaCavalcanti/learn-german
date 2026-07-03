import { NavLink, Outlet } from 'react-router-dom'
import { cx } from './ui'

const nav = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/course', label: 'Course' },
  { to: '/library', label: 'Library' },
  { to: '/vocab', label: 'Vocabulary' },
  { to: '/conjugation', label: 'Conjugation' },
  { to: '/review', label: 'Review' },
  { to: '/import', label: 'Import' },
]

export default function Layout() {
  return (
    <div className="flex min-h-screen">
      <aside className="w-60 shrink-0 border-r border-line bg-card/60 px-4 py-6">
        <div className="mb-8 px-2">
          <div className="font-serif text-2xl font-semibold">Sprachheft</div>
          <div className="text-xs text-muted">German learning notebook</div>
        </div>
        <nav className="space-y-1">
          {nav.map((n) => (
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
      </aside>
      <main className="min-w-0 flex-1">
        <div className="mx-auto max-w-5xl px-8 py-10">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
