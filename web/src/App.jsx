import { useEffect, useState } from 'react'
import { api } from './lib/api'
import PlaylistsView from './views/PlaylistsView'
import InsightsView from './views/InsightsView'
import ToolsView from './views/ToolsView'
import BackupsView from './views/BackupsView'

const NAV = [
  { id: 'playlists', label: "Playlist'ler", icon: IconDisc },
  { id: 'insights', label: 'İçgörüler', icon: IconChart },
  { id: 'tools', label: 'Araçlar', icon: IconTool },
  { id: 'backups', label: 'Yedekler', icon: IconArchive },
]

export default function App() {
  const [view, setView] = useState('playlists')
  const [me, setMe] = useState(null)

  useEffect(() => {
    api('/api/me').then(setMe).catch(() => setMe(null))
  }, [])

  const Active = { playlists: PlaylistsView, insights: InsightsView, tools: ToolsView, backups: BackupsView }[view]

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 flex flex-col border-r border-[var(--border)] bg-[var(--bg-1)]/70 backdrop-blur">
        <div className="brand flex items-center gap-3 px-5 pt-6 pb-5">
          <span className="disc" />
          <div className="leading-tight">
            <div className="font-[var(--font-display)] text-[1.05rem] font-semibold">Organizer</div>
            <div className="text-[0.68rem] tracking-[0.18em] uppercase text-[var(--faint)]">Gece Stüdyosu</div>
          </div>
        </div>

        <nav className="flex flex-col gap-1 px-3 mt-2">
          {NAV.map((n) => {
            const Icon = n.icon
            return (
              <button key={n.id} className={`nav-item ${view === n.id ? 'active' : ''}`} onClick={() => setView(n.id)}>
                <Icon active={view === n.id} />
                {n.label}
              </button>
            )
          })}
        </nav>

        <div className="mt-auto px-5 py-4 border-t border-[var(--border)] flex items-center gap-2 text-sm">
          <div className="w-7 h-7 rounded-full bg-[var(--bg-2)] border border-[var(--border)] grid place-items-center text-xs">
            {(me?.display_name || '?').slice(0, 1)}
          </div>
          <span className="text-[var(--dim)] truncate">{me?.display_name || '—'}</span>
          {me?.demo && <span className="chip ml-auto bg-[rgba(255,178,76,0.14)] text-[var(--amber)]">DEMO</span>}
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 overflow-y-auto">
        <Active key={view} />
      </main>
    </div>
  )
}

/* ===== minimal çizgi ikonlar ===== */
function IconDisc({ active }) {
  const c = active ? 'var(--amber)' : 'currentColor'
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.6">
      <circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="2.2" fill={c} stroke="none" />
    </svg>
  )
}
function IconChart({ active }) {
  const c = active ? 'var(--amber)' : 'currentColor'
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.6" strokeLinecap="round">
      <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />
    </svg>
  )
}
function IconTool({ active }) {
  const c = active ? 'var(--amber)' : 'currentColor'
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18v3h3l6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4 2.5-2.5Z" />
    </svg>
  )
}
function IconArchive({ active }) {
  const c = active ? 'var(--amber)' : 'currentColor'
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="4" rx="1" /><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8M10 12h4" />
    </svg>
  )
}
