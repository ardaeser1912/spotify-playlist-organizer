import { useEffect, useState } from 'react'
import { api, fmtDuration, camelotColor } from '../lib/api'
import PreviewModal from '../components/PreviewModal'

export default function PlaylistsView() {
  const [playlists, setPlaylists] = useState([])
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState(null)
  const [modal, setModal] = useState(null)

  useEffect(() => {
    api('/api/playlists')
      .then((r) => setPlaylists(r.data || []))
      .catch(() => setError('Backend’e ulaşılamıyor — Flask çalışıyor mu? (DEMO=1 python -m spotify_organizer.app)'))
      .finally(() => setLoading(false))
  }, [])

  function open(id) {
    setSelected(id); setDetail(null); setDetailLoading(true); setModal(null); setError(null)
    api(`/api/playlist/${id}`)
      .then((r) => setDetail(r.data))
      .catch(() => setError('Bu liste açılamadı — Spotify, geliştirici-modunda bazı takip-edilen listeleri kısıtlıyor. Beğenilenler ve kendi listelerin çalışır.'))
      .finally(() => setDetailLoading(false))
  }

  return (
    <div className="flex h-full">
      {/* playlist listesi */}
      <div className="w-72 shrink-0 border-r border-[var(--border)] overflow-y-auto p-3">
        <h2 className="px-2 py-2 text-[0.7rem] tracking-[0.16em] uppercase text-[var(--faint)]">Kitaplık</h2>
        {loading && <p className="px-2 text-sm text-[var(--dim)]">Yükleniyor…</p>}
        {error && <p className="px-2 text-sm text-red-300/80">{error}</p>}
        {playlists.map((p, i) => (
          <button
            key={p.id}
            onClick={() => open(p.id)}
            style={{ animationDelay: `${i * 40}ms` }}
            className={`reveal w-full text-left px-3 py-2.5 rounded-[var(--r-sm)] mb-1 transition ${
              selected === p.id ? 'bg-[rgba(255,178,76,0.10)]' : 'hover:bg-white/5'
            }`}
          >
            <div className="truncate font-medium text-[0.95rem]">{p.name}</div>
            <div className="mono text-xs text-[var(--faint)]">{typeof p.track_count === 'number' ? `${p.track_count} parça` : '—'}</div>
          </button>
        ))}
      </div>

      {/* detay */}
      <div className="flex-1 overflow-y-auto">
        {!detail && !detailLoading && (
          <EmptyHint />
        )}

        {detail && (
          <div className="p-8 max-w-4xl">
            <header className="reveal mb-6">
              <div className="text-[0.7rem] tracking-[0.18em] uppercase text-[var(--amber)] mb-1">Playlist</div>
              <h1 className="text-4xl">{detail.name}</h1>
              <p className="mono text-sm text-[var(--dim)] mt-2">{detail.tracks.length} parça</p>
            </header>

            <div className="reveal flex flex-wrap gap-3 mb-6" style={{ animationDelay: '60ms' }}>
              <button className="btn btn-primary" onClick={() => setModal({
                title: 'Türe Göre Ayır',
                previewPath: '/api/split-genre/preview', applyPath: '/api/split-genre/apply',
                kind: 'groups', applyLabel: 'Listeleri Oluştur',
              })}>Türe Göre Ayır</button>
              <button className="btn btn-ghost" onClick={() => setModal({
                title: 'Geçişli Sırala',
                previewPath: '/api/order/preview', applyPath: '/api/order/apply',
                kind: 'tracks', applyLabel: 'Uygula',
              })}>Geçişli Sırala · DJ</button>
              <button className="btn btn-ghost" onClick={() => setModal({
                title: 'Tekrarları Temizle',
                previewPath: '/api/dedupe/preview', applyPath: '/api/dedupe/apply',
                kind: 'dedupe', applyLabel: 'Tekrarları Sil',
              })}>Tekrarları Temizle</button>
            </div>

            <ol className="reveal surface overflow-hidden" style={{ animationDelay: '120ms' }}>
              {detail.tracks.map((t, i) => (
                <li key={t.id} className="flex items-center gap-4 px-4 py-2.5 border-b border-[var(--border)] last:border-0 hover:bg-white/[0.03]">
                  <span className="mono w-6 text-right text-sm text-[var(--faint)]">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="truncate text-[0.95rem]">{t.title}</div>
                    <div className="truncate text-xs text-[var(--dim)]">{t.artist}</div>
                  </div>
                  {t.camelot && (
                    <span className="chip text-black/85" style={{ background: camelotColor(t.camelot) }}>{t.camelot}</span>
                  )}
                  {t.bpm && <span className="mono text-xs text-[var(--dim)] w-16 text-right">{t.bpm} BPM</span>}
                  <span className="mono text-xs text-[var(--faint)] w-12 text-right">{fmtDuration(t.duration_ms)}</span>
                </li>
              ))}
            </ol>

            <PreviewModal
              open={modal !== null}
              title={modal?.title}
              previewPath={modal?.previewPath}
              applyPath={modal?.applyPath}
              kind={modal?.kind}
              applyLabel={modal?.applyLabel}
              body={{ source: detail.id }}
              onClose={() => setModal(null)}
              onApplied={() => { /* modal kendi başarı özetini gösterir; kullanıcı "Bitti" ile kapatır */ }}
            />
          </div>
        )}
      </div>
    </div>
  )
}

function EmptyHint() {
  return (
    <div className="h-full grid place-items-center text-center px-6">
      <div className="reveal">
        <div className="disc mx-auto mb-5" style={{ width: 64, height: 64 }} />
        <h2 className="text-2xl mb-2">Bir playlist seç</h2>
        <p className="text-[var(--dim)] max-w-sm">
          Soldaki kitaplıktan birini aç — türe ayır, geçişli sırala ve tekrarları temizle.
        </p>
      </div>
    </div>
  )
}
