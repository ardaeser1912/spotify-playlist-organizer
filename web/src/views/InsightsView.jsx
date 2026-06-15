// İçgörüler — kaynak seçilen çalma listesinin tür/BPM/on-yıl/sanatçı dağılımları.
import { useEffect, useState } from 'react'
import { api } from '../lib/api'

// Yatay çubuklu dağılım satırı — etiket + oranlı bar + mono sayı.
function BarRow({ label, value, max }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div className="flex items-center gap-3">
      <div className="w-28 shrink-0 text-sm text-[var(--dim)] truncate">{label}</div>
      <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
        <div
          className="h-2 rounded-full"
          style={{ width: pct + '%', background: 'linear-gradient(90deg,var(--amber),var(--amber-deep))' }}
        />
      </div>
      <div className="mono text-sm text-[var(--faint)] w-8 text-right">{value}</div>
    </div>
  )
}

// Bir dağılım sözlüğünü ({etiket: sayı}) çubuklara dönüştüren kart gövdesi.
function DistBars({ dist, order }) {
  const entries = order
    ? order.filter((k) => k in dist).map((k) => [k, dist[k]])
    : Object.entries(dist)
  const max = entries.reduce((m, [, v]) => Math.max(m, v), 0)
  if (entries.length === 0) return <p className="text-sm text-[var(--faint)]">Veri yok</p>
  return (
    <div className="flex flex-col gap-2.5">
      {entries.map(([label, value]) => (
        <BarRow key={label} label={label} value={value} max={max} />
      ))}
    </div>
  )
}

// On-yıl etiketlerini ("1990'lar") artan yıl sırasına dizer; "Bilinmeyen" sona.
function decadeOrder(dist) {
  return Object.keys(dist).sort((a, b) => {
    const na = parseInt(a, 10)
    const nb = parseInt(b, 10)
    if (Number.isNaN(na)) return 1
    if (Number.isNaN(nb)) return -1
    return na - nb
  })
}

const BPM_ORDER = ['Yavaş (<100)', 'Orta (100-128)', 'Hızlı (>128)', 'Bilinmeyen']

export default function InsightsView() {
  const [playlists, setPlaylists] = useState([])
  const [source, setSource] = useState('p_liked')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Kaynak listesini bir kez çek.
  useEffect(() => {
    api('/api/playlists')
      .then((r) => setPlaylists(r.data || []))
      .catch(() => { /* seçici boş kalır, varsayılan yine de çalışır */ })
  }, [])

  // Kaynak değişince içgörüleri çek.
  useEffect(() => {
    let alive = true
    setLoading(true)
    setError(null)
    api('/api/insights/' + source)
      .then((r) => { if (alive) setData(r.data) })
      .catch((e) => { if (alive) setError(e.message || 'İçgörüler alınamadı') })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [source])

  const empty = data && data.total === 0

  return (
    <div className="p-8 max-w-5xl">
      <header className="reveal mb-7">
        <div className="text-[0.7rem] tracking-[0.18em] uppercase text-[var(--amber)] mb-1">İçgörüler</div>
        <h1 className="text-4xl">Kütüphanen, sayılarla</h1>
        <p className="text-[var(--dim)] mt-2">Tür, tempo ve dönem dağılımları — seçtiğin kaynak için.</p>
        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="surface mono mt-4 px-3 py-2 text-sm text-[var(--text)] outline-none focus:border-[var(--border-strong)]"
        >
          <option value="p_liked">Beğenilen Şarkılar</option>
          {playlists.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} ({p.track_count})
            </option>
          ))}
        </select>
      </header>

      {loading && <p className="reveal text-[var(--dim)]">Hesaplanıyor…</p>}

      {!loading && error && (
        <div className="reveal card p-5 border-[var(--border-strong)]">
          <p className="text-[var(--text)]">İçgörüler yüklenemedi.</p>
          <p className="mono text-xs text-[var(--faint)] mt-1">{error}</p>
        </div>
      )}

      {!loading && !error && empty && (
        <div className="reveal card p-8 text-center">
          <p className="text-[var(--dim)]">Bu kaynakta gösterilecek parça yok.</p>
        </div>
      )}

      {!loading && !error && data && !empty && (
        <>
          {/* özet istatistikler */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div style={{ animationDelay: '0ms' }} className="reveal card p-5">
              <div className="text-[0.7rem] tracking-[0.18em] uppercase text-[var(--faint)] mb-2">Toplam parça</div>
              <div className="mono text-4xl text-[var(--text)]">{data.total}</div>
            </div>
            <div style={{ animationDelay: '60ms' }} className="reveal card p-5">
              <div className="text-[0.7rem] tracking-[0.18em] uppercase text-[var(--faint)] mb-2">Ortalama popülerlik</div>
              <div className="mono text-4xl text-[var(--text)]">{Math.round(data.avg_popularity)}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div style={{ animationDelay: '120ms' }} className="reveal card p-5">
              <h3 className="text-lg mb-4">Tür Dağılımı</h3>
              <DistBars dist={data.genre_dist || {}} />
            </div>

            <div style={{ animationDelay: '180ms' }} className="reveal card p-5">
              <h3 className="text-lg mb-4">BPM Yoğunluğu</h3>
              <DistBars dist={data.bpm_dist || {}} order={BPM_ORDER} />
            </div>

            <div style={{ animationDelay: '240ms' }} className="reveal card p-5">
              <h3 className="text-lg mb-4">On-Yıllar</h3>
              <DistBars dist={data.decade_dist || {}} order={decadeOrder(data.decade_dist || {})} />
            </div>

            <div style={{ animationDelay: '300ms' }} className="reveal card p-5">
              <h3 className="text-lg mb-4">En Çok Sanatçılar</h3>
              {(data.top_artists || []).length === 0 ? (
                <p className="text-sm text-[var(--faint)]">Veri yok</p>
              ) : (
                <ol className="flex flex-col gap-2.5">
                  {data.top_artists.map(([name, count], i) => (
                    <li key={name} className="flex items-center gap-3">
                      <span className="mono text-xs text-[var(--faint)] w-6">{i + 1}.</span>
                      <span className="flex-1 text-sm text-[var(--text)] truncate">{name}</span>
                      <span className="mono text-sm text-[var(--faint)]">{count}</span>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
