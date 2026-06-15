import { useEffect, useState } from 'react'
import { api, post, fmtDuration } from '../lib/api'
import PreviewModal from '../components/PreviewModal'

// Tüm işlevler tek vitrinde. Karta tıklayınca o aracın akış paneli açılır.
const TOOLS = [
  { key: 'genre', title: 'Türe Göre Ayır', desc: 'Karışık listeyi türe göre yeni playlist’lere böl.', tag: 'Playlist' },
  { key: 'order', title: 'Geçişli Sırala · DJ', desc: 'Harmonic mixing (Camelot) + BPM rampasıyla akıcı geçiş.', tag: 'Sıralama' },
  { key: 'dedupe', title: 'Tekrarları Temizle', desc: 'Aynı parçanın kopyalarını bul ve kaldır.', tag: 'Temizlik' },
  { key: 'sort', title: 'Çok-Anahtarlı Sırala', desc: 'Sanatçı · albüm · tarih · popülerlik · BPM · süre.', tag: 'Sıralama' },
  { key: 'merge', title: 'Birleştir', desc: 'Birden fazla playlist’i tek listede topla.', tag: 'Playlist' },
  { key: 'split', title: 'Böl', desc: 'Büyük listeyi on-yıla / tempo bölgesine / boyuta göre ayır.', tag: 'Playlist' },
  { key: 'tops', title: 'Top’lardan Playlist', desc: 'En çok dinlediğin şarkı/sanatçılardan tek tıkla liste.', tag: 'Keşif' },
  { key: 'search', title: 'Ara & Ekle', desc: 'Katalogda ara, beğendiğini playlist’e ekle.', tag: 'Keşif' },
]

const SORT_FIELDS = [
  { v: 'popularity', label: 'Popülerlik' },
  { v: 'year', label: 'Yıl' },
  { v: 'bpm', label: 'BPM' },
  { v: 'duration_ms', label: 'Süre' },
  { v: 'title', label: 'Başlık' },
  { v: 'artist', label: 'Sanatçı' },
]

const SPLIT_BY = [
  { v: 'decade', label: 'On-yıla göre' },
  { v: 'tempo', label: 'Tempo bölgesine göre' },
  { v: 'size', label: 'Sabit boyuta göre' },
]

// native <select> için ortak stil — mevcut surface token'larıyla, yeni CSS yok
const selectCls = 'surface px-3 py-2 text-sm text-[var(--text)] rounded-[10px] outline-none focus:border-[var(--border-strong)] cursor-pointer'
const inputCls = 'surface px-3 py-2 text-sm text-[var(--text)] rounded-[10px] outline-none focus:border-[var(--border-strong)] w-full placeholder:text-[var(--faint)]'

export default function ToolsView() {
  const [active, setActive] = useState(null)        // açık araç key'i
  const [playlists, setPlaylists] = useState([])
  const [plLoading, setPlLoading] = useState(true)
  const [plError, setPlError] = useState(null)

  useEffect(() => {
    api('/api/playlists')
      .then((r) => setPlaylists(r.data || []))
      .catch((e) => setPlError(e.message))
      .finally(() => setPlLoading(false))
  }, [])

  return (
    <div className="p-8 max-w-5xl">
      <header className="reveal mb-7">
        <div className="text-[0.7rem] tracking-[0.18em] uppercase text-[var(--amber)] mb-1">Araçlar</div>
        <h1 className="text-4xl">Tüm işlevler</h1>
        <p className="text-[var(--dim)] mt-2">Her araç güvenli: önce önizleme, sonra onaylı uygulama + otomatik yedek.</p>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {TOOLS.map((t, i) => (
          <button
            key={t.key}
            onClick={() => setActive(t.key)}
            style={{ animationDelay: `${i * 45}ms` }}
            className={`reveal card text-left p-5 transition hover:-translate-y-0.5 hover:border-[var(--border-strong)] ${active === t.key ? 'border-[var(--border-strong)]' : ''}`}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="chip bg-white/5 text-[var(--dim)]">{t.tag}</span>
              <span className="text-[var(--faint)]">→</span>
            </div>
            <h3 className="text-lg mb-1.5">{t.title}</h3>
            <p className="text-sm text-[var(--dim)] leading-relaxed">{t.desc}</p>
          </button>
        ))}
      </div>

      {active && (
        <ToolPanel
          key={active}
          tool={TOOLS.find((t) => t.key === active)}
          playlists={playlists}
          plLoading={plLoading}
          plError={plError}
          onClose={() => setActive(null)}
        />
      )}
    </div>
  )
}

/* ── Seçili aracın konfig paneli ── */
function ToolPanel({ tool, playlists, plLoading, plError, onClose }) {
  if (tool.key === 'tops') return <PanelShell tool={tool} onClose={onClose}><TopsFlow /></PanelShell>
  if (tool.key === 'search') return <PanelShell tool={tool} onClose={onClose}><SearchFlow /></PanelShell>
  return (
    <PanelShell tool={tool} onClose={onClose}>
      <MutationFlow tool={tool} playlists={playlists} plLoading={plLoading} plError={plError} />
    </PanelShell>
  )
}

function PanelShell({ tool, onClose, children }) {
  return (
    <div className="reveal card p-6 mt-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="text-[0.66rem] tracking-[0.18em] uppercase text-[var(--amber)]">{tool.tag}</div>
          <h2 className="text-2xl">{tool.title}</h2>
          <p className="text-sm text-[var(--dim)] mt-1">{tool.desc}</p>
        </div>
        <button className="btn btn-ghost px-3 py-1.5" onClick={onClose} aria-label="Kapat">✕</button>
      </div>
      {children}
    </div>
  )
}

/* küçük yardımcı: kaynak <select> (gereken araçlarda) */
function SourceSelect({ value, onChange, playlists, plLoading, plError }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs text-[var(--dim)]">Kaynak liste</span>
      {plError && <span className="text-xs text-red-300/85">⚠ {plError}</span>}
      <select className={selectCls} value={value} onChange={(e) => onChange(e.target.value)} disabled={plLoading}>
        <option value="p_liked">Beğenilenler</option>
        {playlists.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}{typeof p.track_count === 'number' ? ` (${p.track_count})` : ''}
          </option>
        ))}
      </select>
    </label>
  )
}

/* ── 6 mutasyon aracı → PreviewModal ── */
function MutationFlow({ tool, playlists, plLoading, plError }) {
  const [source, setSource] = useState('p_liked')
  // sort
  const [sortField, setSortField] = useState('popularity')
  const [sortDir, setSortDir] = useState('desc')
  // merge
  const [mergeSel, setMergeSel] = useState([])
  const [mergeName, setMergeName] = useState('Birleşik Liste')
  // split
  const [splitBy, setSplitBy] = useState('decade')
  const [splitSize, setSplitSize] = useState(5)
  // modal
  const [open, setOpen] = useState(false)

  function toggleMerge(id) {
    setMergeSel((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  // her araca özel modal konfigürasyonu
  let cfg = null
  if (tool.key === 'genre') {
    cfg = { previewPath: '/api/split-genre/preview', applyPath: '/api/split-genre/apply', body: { source }, kind: 'groups', applyLabel: 'Uygula' }
  } else if (tool.key === 'order') {
    cfg = { previewPath: '/api/order/preview', applyPath: '/api/order/apply', body: { source }, kind: 'tracks', applyLabel: 'Uygula' }
  } else if (tool.key === 'dedupe') {
    cfg = { previewPath: '/api/dedupe/preview', applyPath: '/api/dedupe/apply', body: { source }, kind: 'dedupe', applyLabel: 'Temizle' }
  } else if (tool.key === 'sort') {
    cfg = { previewPath: '/api/sort/preview', applyPath: '/api/sort/apply', body: { source, keys: [[sortField, sortDir]] }, kind: 'tracks', applyLabel: 'Uygula' }
  } else if (tool.key === 'merge') {
    cfg = { previewPath: '/api/merge/preview', applyPath: '/api/merge/apply', body: { sources: mergeSel, name: mergeName }, kind: 'tracks', applyLabel: 'Birleştir' }
  } else if (tool.key === 'split') {
    const body = splitBy === 'size' ? { source, by: splitBy, size: Number(splitSize) || 1 } : { source, by: splitBy }
    cfg = { previewPath: '/api/split/preview', applyPath: '/api/split/apply', body, kind: 'groups', applyLabel: 'Uygula' }
  }

  const mergeReady = mergeSel.length >= 2 && mergeName.trim().length > 0
  const canRun = tool.key === 'merge' ? mergeReady : true

  return (
    <>
      <div className="flex flex-col gap-4">
        {/* merge dışındaki tüm araçlar kaynak ister */}
        {tool.key !== 'merge' && (
          <SourceSelect value={source} onChange={setSource} playlists={playlists} plLoading={plLoading} plError={plError} />
        )}

        {/* sort: alan + yön */}
        {tool.key === 'sort' && (
          <div className="flex flex-wrap gap-3">
            <label className="flex flex-col gap-1.5">
              <span className="text-xs text-[var(--dim)]">Sırala</span>
              <select className={selectCls} value={sortField} onChange={(e) => setSortField(e.target.value)}>
                {SORT_FIELDS.map((f) => <option key={f.v} value={f.v}>{f.label}</option>)}
              </select>
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-xs text-[var(--dim)]">Yön</span>
              <select className={selectCls} value={sortDir} onChange={(e) => setSortDir(e.target.value)}>
                <option value="asc">Artan</option>
                <option value="desc">Azalan</option>
              </select>
            </label>
          </div>
        )}

        {/* merge: çoklu seçim + isim */}
        {tool.key === 'merge' && (
          <div className="flex flex-col gap-3">
            <div>
              <span className="text-xs text-[var(--dim)]">Birleştirilecek listeler (en az 2)</span>
              {plError && <p className="text-xs text-red-300/85 mt-1">⚠ {plError}</p>}
              {plLoading ? (
                <p className="text-sm text-[var(--dim)] mt-2">Listeler yükleniyor…</p>
              ) : playlists.length === 0 ? (
                <p className="text-sm text-[var(--dim)] mt-2">Birleştirilecek playlist bulunamadı.</p>
              ) : (
                <div className="surface mt-1.5 max-h-56 overflow-y-auto">
                  {playlists.map((p) => (
                    <label key={p.id}
                           className="flex items-center gap-3 px-4 py-2 border-b border-[var(--border)] last:border-0 cursor-pointer hover:bg-white/5">
                      <input type="checkbox" checked={mergeSel.includes(p.id)} onChange={() => toggleMerge(p.id)} className="accent-[var(--amber)]" />
                      <span className="flex-1 truncate text-sm">{p.name}</span>
                      {typeof p.track_count === 'number' && (
                        <span className="mono text-xs text-[var(--faint)]">{p.track_count}</span>
                      )}
                    </label>
                  ))}
                </div>
              )}
            </div>
            <label className="flex flex-col gap-1.5">
              <span className="text-xs text-[var(--dim)]">Yeni liste adı</span>
              <input className={inputCls} value={mergeName} onChange={(e) => setMergeName(e.target.value)} placeholder="Birleşik Liste" />
            </label>
            {mergeSel.length > 0 && mergeSel.length < 2 && (
              <p className="text-xs text-[var(--faint)]">En az 2 liste seç.</p>
            )}
          </div>
        )}

        {/* split: by + (size) */}
        {tool.key === 'split' && (
          <div className="flex flex-wrap items-end gap-3">
            <label className="flex flex-col gap-1.5">
              <span className="text-xs text-[var(--dim)]">Bölme ölçütü</span>
              <select className={selectCls} value={splitBy} onChange={(e) => setSplitBy(e.target.value)}>
                {SPLIT_BY.map((b) => <option key={b.v} value={b.v}>{b.label}</option>)}
              </select>
            </label>
            {splitBy === 'size' && (
              <label className="flex flex-col gap-1.5">
                <span className="text-xs text-[var(--dim)]">Parça/liste</span>
                <input type="number" min="1" className={`${inputCls} w-28`} value={splitSize}
                       onChange={(e) => setSplitSize(e.target.value)} />
              </label>
            )}
          </div>
        )}

        <div className="flex justify-end pt-1">
          <button className="btn btn-primary" onClick={() => setOpen(true)} disabled={!canRun}>
            Önizle
          </button>
        </div>
      </div>

      {cfg && (
        <PreviewModal
          open={open}
          title={tool.title}
          previewPath={cfg.previewPath}
          applyPath={cfg.applyPath}
          body={cfg.body}
          kind={cfg.kind}
          applyLabel={cfg.applyLabel}
          onClose={() => setOpen(false)}
          onApplied={() => { /* modal kendi özetini gösterir */ }}
        />
      )}
    </>
  )
}

/* ── Keşif 1: Top’lardan Playlist ── */
function TopsFlow() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)         // {tracks, artists}
  const [name, setName] = useState('Top Şarkılarım')
  const [creating, setCreating] = useState(false)
  const [created, setCreated] = useState(null)

  useEffect(() => {
    api('/api/top')
      .then((r) => setData(r.data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  async function create() {
    setCreating(true); setError(null)
    try {
      const r = await post('/api/discover/apply', { kind: 'top', name })
      setCreated(r.data)
    } catch (e) {
      setError(e.message)
    } finally {
      setCreating(false)
    }
  }

  if (loading) return <p className="text-sm text-[var(--dim)]">Top listen yükleniyor…</p>
  if (error && !created) return <p className="text-sm text-red-300/85">⚠ {error}</p>
  if (created) return <CreatedSummary created={created} />

  const tracks = data?.tracks || []
  const artists = data?.artists || []

  return (
    <div className="flex flex-col gap-5">
      {tracks.length === 0 && artists.length === 0 && (
        <p className="text-sm text-[var(--dim)]">Top verisi bulunamadı.</p>
      )}
      {tracks.length > 0 && (
        <div>
          <div className="text-xs text-[var(--dim)] mb-2">En çok dinlenen şarkılar</div>
          <ol className="surface overflow-hidden">
            {tracks.map((t, i) => (
              <li key={t.id + '-' + i} className="flex items-center gap-3 px-4 py-2 border-b border-[var(--border)] last:border-0">
                <span className="mono w-6 text-right text-xs text-[var(--faint)]">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <div className="truncate text-sm">{t.title}</div>
                  <div className="truncate text-xs text-[var(--dim)]">{t.artist}</div>
                </div>
                {t.duration_ms != null && (
                  <span className="mono text-xs text-[var(--faint)] w-10 text-right">{fmtDuration(t.duration_ms)}</span>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}
      {artists.length > 0 && (
        <div>
          <div className="text-xs text-[var(--dim)] mb-2">En çok dinlenen sanatçılar</div>
          <div className="flex flex-wrap gap-2">
            {artists.map((a, i) => (
              <span key={(a.id || a.name) + '-' + i} className="chip bg-white/5 text-[var(--dim)] px-2.5 py-1">{a.name || a}</span>
            ))}
          </div>
        </div>
      )}
      <CreateBar name={name} setName={setName} onCreate={create} creating={creating}
                 disabled={tracks.length === 0} error={error} />
    </div>
  )
}

/* ── Keşif 2: Ara & Ekle ── */
function SearchFlow() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [tracks, setTracks] = useState(null)     // null = henüz aranmadı
  const [name, setName] = useState('')
  const [creating, setCreating] = useState(false)
  const [created, setCreated] = useState(null)

  async function search(e) {
    e?.preventDefault()
    if (!query.trim()) return
    setLoading(true); setError(null); setCreated(null)
    try {
      const r = await post('/api/search', { query })
      setTracks(r.data?.tracks || [])
      if (!name.trim()) setName(`“${query.trim()}” seçkisi`)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function create() {
    setCreating(true); setError(null)
    try {
      const r = await post('/api/discover/apply', { kind: 'search', query, name })
      setCreated(r.data)
    } catch (err) {
      setError(err.message)
    } finally {
      setCreating(false)
    }
  }

  if (created) return <CreatedSummary created={created} />

  return (
    <div className="flex flex-col gap-5">
      <form onSubmit={search} className="flex gap-2">
        <input className={inputCls} value={query} onChange={(e) => setQuery(e.target.value)}
               placeholder="Şarkı, sanatçı veya albüm ara…" />
        <button type="submit" className="btn btn-ghost" disabled={loading || !query.trim()}>
          {loading ? 'Aranıyor…' : 'Ara'}
        </button>
      </form>

      {error && <p className="text-sm text-red-300/85">⚠ {error}</p>}

      {tracks !== null && !loading && (
        tracks.length === 0 ? (
          <p className="text-sm text-[var(--dim)]">Sonuç bulunamadı.</p>
        ) : (
          <>
            <ol className="surface overflow-hidden">
              {tracks.map((t, i) => (
                <li key={t.id + '-' + i} className="flex items-center gap-3 px-4 py-2 border-b border-[var(--border)] last:border-0">
                  <span className="mono w-6 text-right text-xs text-[var(--faint)]">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="truncate text-sm">{t.title}</div>
                    <div className="truncate text-xs text-[var(--dim)]">{t.artist}</div>
                  </div>
                  {t.duration_ms != null && (
                    <span className="mono text-xs text-[var(--faint)] w-10 text-right">{fmtDuration(t.duration_ms)}</span>
                  )}
                </li>
              ))}
            </ol>
            <CreateBar name={name} setName={setName} onCreate={create} creating={creating}
                       disabled={tracks.length === 0} />
          </>
        )
      )}
    </div>
  )
}

/* keşif akışları için ortak oluştur çubuğu */
function CreateBar({ name, setName, onCreate, creating, disabled, error }) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between pt-1 border-t border-[var(--border)]">
      <label className="flex flex-col gap-1.5 flex-1">
        <span className="text-xs text-[var(--dim)]">Yeni liste adı</span>
        <input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} placeholder="Liste adı" />
      </label>
      <button className="btn btn-primary sm:ml-3" onClick={onCreate}
              disabled={creating || disabled || !name.trim()}>
        {creating ? 'Oluşturuluyor…' : 'Playlist Oluştur'}
      </button>
    </div>
  )
}

/* keşif başarı özeti */
function CreatedSummary({ created }) {
  const list = created.created || (created.id ? [created] : [])
  return (
    <div className="text-center py-4">
      <div className="w-12 h-12 mx-auto mb-3 rounded-full grid place-items-center text-[var(--amber)]"
           style={{ border: '1px solid var(--border-strong)' }}>✓</div>
      <h4 className="text-lg mb-1">Playlist oluşturuldu</h4>
      {list.length > 0 ? (
        <div className="mt-3 flex flex-col gap-1.5 max-w-sm mx-auto text-left">
          {list.map((c, i) => (
            <div key={(c.id || c.name) + '-' + i} className="surface px-3 py-2 flex items-center justify-between">
              <span className="truncate text-sm">{c.name}</span>
              {c.count != null && <span className="mono text-xs text-[var(--faint)]">{c.count} parça</span>}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-[var(--dim)] mt-1">Yedeklerden ve kütüphanenden ulaşabilirsin.</p>
      )}
    </div>
  )
}
