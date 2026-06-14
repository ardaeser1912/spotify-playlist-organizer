import { useEffect, useState } from 'react'

const ACCENT = '#1DB954' // Spotify yeşili

function fmt(ms) {
  const s = Math.round(ms / 1000)
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

export default function App() {
  const [me, setMe] = useState(null)
  const [playlists, setPlaylists] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)

  useEffect(() => {
    Promise.all([
      fetch('/api/me').then((r) => r.json()),
      fetch('/api/playlists').then((r) => r.json()),
    ])
      .then(([meRes, plRes]) => {
        setMe(meRes)
        setPlaylists(plRes.data || [])
      })
      .catch(() => setError('Backend’e ulaşılamıyor. Flask çalışıyor mu? (DEMO=1 python -m spotify_organizer.app)'))
      .finally(() => setLoading(false))
  }, [])

  function selectPlaylist(id) {
    setSelectedId(id)
    setDetail(null)
    setDetailLoading(true)
    setNotice(null)
    fetch(`/api/playlist/${id}`)
      .then((r) => r.json())
      .then((res) => setDetail(res.data))
      .catch(() => setError('Playlist yüklenemedi'))
      .finally(() => setDetailLoading(false))
  }

  // F2/F3'te loop bunları /api/split-genre ve /api/order'a bağlayacak (önizle→uygula).
  function comingSoon(label) {
    setNotice(`“${label}” — mantık loop tarafından bağlanacak (önizle → uygula).`)
  }

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <aside className="w-72 shrink-0 border-r border-white/5 bg-[#0d0d14] flex flex-col">
        <div className="px-5 py-4 border-b border-white/5 flex items-center gap-2">
          <span className="text-xl">🎵</span>
          <span className="font-semibold tracking-tight">Playlist Organizer</span>
        </div>
        <div className="px-3 py-2 text-xs uppercase tracking-wider text-white/40">Playlist'ler</div>
        <nav className="flex-1 overflow-y-auto px-2 pb-4">
          {loading && <p className="px-3 py-2 text-sm text-white/40">Yükleniyor…</p>}
          {!loading && playlists.length === 0 && !error && (
            <p className="px-3 py-2 text-sm text-white/40">Playlist yok.</p>
          )}
          {playlists.map((p) => (
            <button
              key={p.id}
              onClick={() => selectPlaylist(p.id)}
              className={`w-full text-left px-3 py-2 rounded-lg mb-1 transition ${
                selectedId === p.id ? 'bg-white/10 text-white' : 'text-white/70 hover:bg-white/5'
              }`}
            >
              <div className="truncate text-sm font-medium">{p.name}</div>
              <div className="text-xs text-white/40">{p.track_count} şarkı</div>
            </button>
          ))}
        </nav>
        <div className="px-5 py-3 border-t border-white/5 text-xs text-white/40">
          {me?.display_name || '—'}
          {me?.demo && (
            <span className="ml-2 rounded px-1.5 py-0.5 bg-yellow-500/15 text-yellow-300">DEMO</span>
          )}
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        {error && (
          <div className="m-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}

        {!error && !detail && (
          <div className="h-full grid place-items-center text-white/40">
            <div className="text-center">
              <div className="text-5xl mb-3">🎚️</div>
              <p>Soldan bir playlist seç.</p>
            </div>
          </div>
        )}

        {detail && (
          <div className="p-6 max-w-4xl">
            <header className="mb-5">
              <h1 className="text-2xl font-bold">{detail.name}</h1>
              <p className="text-sm text-white/40">{detail.tracks.length} şarkı</p>
            </header>

            <div className="flex gap-3 mb-5">
              <button
                onClick={() => comingSoon('Türe Göre Ayır')}
                className="rounded-lg px-4 py-2 text-sm font-medium text-black"
                style={{ background: ACCENT }}
              >
                🎚 Türe Göre Ayır
              </button>
              <button
                onClick={() => comingSoon('Geçişli Sırala')}
                className="rounded-lg px-4 py-2 text-sm font-medium border border-white/15 hover:bg-white/5"
              >
                🎚 Geçişli Sırala (DJ)
              </button>
            </div>

            {notice && (
              <div className="mb-5 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/70">
                {notice}
              </div>
            )}

            {detailLoading ? (
              <p className="text-white/40">Yükleniyor…</p>
            ) : (
              <ol className="divide-y divide-white/5 rounded-xl border border-white/5 overflow-hidden">
                {detail.tracks.map((t, i) => (
                  <li key={t.id} className="flex items-center gap-4 px-4 py-2.5 hover:bg-white/[0.03]">
                    <span className="w-6 text-right text-sm text-white/30">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="truncate text-sm font-medium">{t.title}</div>
                      <div className="truncate text-xs text-white/40">{t.artist}</div>
                    </div>
                    {t.bpm && <span className="text-xs text-white/40 w-16 text-right">{t.bpm} BPM</span>}
                    {t.camelot && <span className="text-xs text-white/40 w-10 text-right">{t.camelot}</span>}
                    <span className="text-xs text-white/30 w-12 text-right">{fmt(t.duration_ms)}</span>
                  </li>
                ))}
              </ol>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
