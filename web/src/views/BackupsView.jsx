// Yedekler — her uygulanan işlemden önce otomatik yedek alınır; buradan Geri Al.
// Canlı: /api/backups listesini çeker, /api/restore ile geri yükler.
import { useEffect, useState } from 'react'
import { api, post } from '../lib/api'

// "20260615-024512-123456" gibi ham damgayı "2026-06-15 02:45"e çevirir;
// tanımadığı biçimi olduğu gibi geri verir (parse patlamasın).
function fmtTs(ts) {
  if (!ts) return ''
  const m = String(ts).match(/^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})/)
  if (m) return `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]}`
  return String(ts)
}

export default function BackupsView() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(null) // geri-alınan dosyanın file'ı
  const [notice, setNotice] = useState(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const res = await api('/api/backups')
      const data = (res && res.data) ?? res ?? []
      setItems(Array.isArray(data) ? data : [])
    } catch (e) {
      setError(e.message || 'Yedekler alınamadı')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function restore(b) {
    setBusy(b.file)
    setNotice(null)
    setError(null)
    try {
      await post('/api/restore', { file: b.file })
      setNotice(`“${b.label || b.file}” geri yüklendi → yeni playlist oluşturuldu.`)
      await load()
    } catch (e) {
      setError(e.message || 'Geri yükleme başarısız')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="p-8 max-w-4xl">
      <header className="reveal mb-7">
        <div className="text-[0.7rem] tracking-[0.18em] uppercase text-[var(--amber)] mb-1">Yedekler</div>
        <h1 className="text-4xl">Güvenlik ağı</h1>
        <p className="text-[var(--dim)] mt-2">Her “Uygula” öncesi playlist otomatik yedeklenir — tek tıkla geri alabilirsin.</p>
      </header>

      {notice && (
        <div className="reveal surface p-4 mb-5 flex items-start gap-3" style={{ borderColor: 'var(--border-strong)' }}>
          <span className="text-[var(--teal)] mt-0.5">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 6 9 17l-5-5" />
            </svg>
          </span>
          <p className="text-sm">{notice}</p>
        </div>
      )}

      {error && (
        <div className="reveal surface p-4 mb-5 text-sm" style={{ borderColor: 'rgba(255,120,120,0.4)', color: '#ffb4b4' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div className="reveal card p-10 text-center text-[var(--dim)]">Yedekler yükleniyor…</div>
      ) : items.length === 0 ? (
        <div className="reveal card p-10 text-center">
          <div className="w-14 h-14 mx-auto mb-4 rounded-full border border-[var(--border-strong)] grid place-items-center text-[var(--amber)]">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="4" width="18" height="4" rx="1" /><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8M10 12h4" />
            </svg>
          </div>
          <h3 className="text-xl mb-1">Henüz yedek yok</h3>
          <p className="text-[var(--dim)] max-w-sm mx-auto">Bir işlem uyguladığında yedek burada görünür ve istediğin an geri yükleyebilirsin.</p>
        </div>
      ) : (
        <div className="reveal flex flex-col gap-2.5">
          {items.map((b) => (
            <div key={b.file} className="surface p-4 flex items-center gap-4">
              <div className="min-w-0 flex-1">
                <div className="font-medium truncate">{b.label || b.file}</div>
                <div className="text-[var(--dim)] text-sm mono mt-0.5">{fmtTs(b.ts)}</div>
              </div>
              <span className="chip text-[var(--amber)]" style={{ background: 'rgba(255,178,76,0.10)' }}>
                {b.count} parça
              </span>
              <button
                className="btn btn-ghost"
                onClick={() => restore(b)}
                disabled={busy === b.file}
              >
                {busy === b.file ? 'Geri alınıyor…' : 'Geri Al'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
