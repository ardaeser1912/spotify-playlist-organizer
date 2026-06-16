import { Fragment, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { api, post, fmtDuration, camelotColor, camelotCompatible } from '../lib/api'
import AlbumArt from './AlbumArt'
import DjPlayer from './DjPlayer'

/**
 * Paylaşılan Önizle → Uygula akışı (güvenlik çekirdeği).
 * Açılınca previewPath'i POST'lar, sonucu kind'e göre gösterir; "Uygula" applyPath'i
 * POST'lar (backend ÖNCE yedek alır), sonra onApplied(result) ile özet gösterir.
 *
 * Portal ile <body>'ye basılır → ata elemanlardaki transform (.reveal) fixed overlay'i bozmaz.
 *
 * Props: open, title, previewPath, applyPath, body, kind('tracks'|'groups'|'dedupe'),
 *        applyLabel, onClose, onApplied(result)
 */
export default function PreviewModal({ open, title, previewPath, applyPath, body,
                                       kind = 'tracks', applyLabel = 'Uygula',
                                       onClose, onApplied }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)
  const [applying, setApplying] = useState(false)
  const [done, setDone] = useState(null)
  const [copied, setCopied] = useState(false)
  const [djOpen, setDjOpen] = useState(false)
  const [isDemo, setIsDemo] = useState(true) // güvenli varsayım: DEMO (Uygula birincil)

  const dialogRef = useRef(null)
  const titleId = useRef('preview-modal-title-' + Math.random().toString(36).slice(2)).current
  const opener = useRef(null)

  useEffect(() => {
    if (!open) return
    setData(null); setError(null); setDone(null); setLoading(true)
    post(previewPath, body)
      .then((r) => setData(r.data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [open, previewPath, JSON.stringify(body)])

  // Mod bayrağı: gerçek hesapta Spotify yazmayı engeller → export birincil olmalı.
  // Hata olursa DEMO varsay (güvenli: Uygula birincil kalır).
  useEffect(() => {
    if (!open) return
    api('/api/me')
      .then((r) => setIsDemo(r?.data?.demo !== false))
      .catch(() => setIsDemo(true))
  }, [open])

  // Erişilebilirlik: Escape ile kapat + basit focus-trap (Tab/Shift+Tab sarması)
  useEffect(() => {
    if (!open) return
    function onKeyDown(e) {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose?.()
        return
      }
      if (e.key === 'Tab') {
        const root = dialogRef.current
        if (!root) return
        const focusables = root.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        )
        if (focusables.length === 0) return
        const first = focusables[0]
        const last = focusables[focusables.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, onClose])

  // Erişilebilirlik: açılışta odağı modal içine al, kapanışta açan öğeye geri ver
  useEffect(() => {
    if (!open) return
    opener.current = document.activeElement
    const root = dialogRef.current
    const focusables = root?.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    )
    focusables?.[0]?.focus()
    return () => {
      opener.current?.focus?.()
    }
  }, [open])

  if (!open) return null

  const nothingToApply = kind === 'dedupe' && data && data.removed_count === 0
  const isForbidden = !!error && /403|forbidden/i.test(error)
  const canExport = !!data
  // DJ Modu yalnızca akış sıralamalarında (Geçişli Sırala / Akıllı Mix) anlamlı.
  const canDj = kind === 'tracks' && Array.isArray(data?.tracks) && data.tracks.length > 0

  async function apply() {
    setApplying(true); setError(null)
    try {
      const r = await post(applyPath, body)
      setDone(r.data)
      onApplied?.(r.data)
    } catch (e) {
      setError(e.message)
    } finally {
      setApplying(false)
    }
  }

  // Önizleme verisini düz satırlara çevirir: { group, title, artist, uri }
  function exportRows() {
    const rows = []
    if (kind === 'groups') {
      for (const g of data.groups || []) {
        const grp = g.bucket || g.label || ''
        for (const t of g.tracks || []) rows.push({ group: grp, ...t })
      }
    } else if (kind === 'dedupe') {
      for (const t of data.kept || []) rows.push({ group: '', ...t })
    } else {
      ;(data.tracks || []).forEach((t, i) => rows.push({ group: String(i + 1), ...t }))
    }
    return rows
  }

  function trackLink(uri) {
    if (!uri) return ''
    const id = String(uri).split(':').pop()
    return id ? `https://open.spotify.com/track/${id}` : ''
  }

  function csvCell(v) {
    const s = v == null ? '' : String(v)
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s
  }

  function exportCsv() {
    if (!data) return
    const rows = exportRows()
    const head = ['Grup', 'Başlık', 'Sanatçı', 'Spotify Linki']
    const lines = [head.map(csvCell).join(',')]
    for (const r of rows) {
      lines.push([r.group, r.title, r.artist, trackLink(r.uri)].map(csvCell).join(','))
    }
    const csv = '﻿' + lines.join('\r\n')
    const safeTitle = (title || 'liste')
      .normalize('NFKD').replace(/[̀-ͯ]/g, '')
      .replace(/[^a-zA-Z0-9]+/g, '-').replace(/^-+|-+$/g, '').toLowerCase() || 'liste'
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${safeTitle}-${Date.now()}.csv`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  async function copyLinks() {
    if (!data) return
    const links = exportRows().map((r) => trackLink(r.uri)).filter(Boolean).join('\n')
    try {
      await navigator.clipboard.writeText(links)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch {
      setError('Panoya kopyalanamadı — tarayıcı izin vermedi.')
    }
  }

  return (
    <>
    {createPortal(
    <div className="fixed inset-0 z-50 grid place-items-center p-4"
         style={{ background: 'rgba(4,4,7,0.66)', backdropFilter: 'blur(4px)' }}
         onClick={onClose}>
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby={titleId}
           className="card reveal w-full max-w-2xl max-h-[85vh] flex flex-col"
           style={{ animationDuration: '0.32s' }}
           onClick={(e) => e.stopPropagation()}>
        {/* başlık */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div>
            <div className="text-[0.66rem] tracking-[0.18em] uppercase text-[var(--amber)]">Önizleme</div>
            <h3 id={titleId} className="text-xl">{title}</h3>
          </div>
          <button className="btn btn-ghost px-3 py-1.5" onClick={onClose} aria-label="Kapat">✕</button>
        </div>

        {/* gövde */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading && (
            <p className="text-sm text-[var(--dim)]">
              Önizleme hazırlanıyor…{' '}
              <span className="text-[var(--faint)]">(büyük kütüphanelerde Spotify’dan çekmek birkaç saniye sürebilir)</span>
            </p>
          )}
          {error && (isForbidden
            ? (
              <div className="surface px-4 py-3 text-sm text-[var(--dim)]">
                <span className="text-[var(--amber)]">⬡</span>{' '}
                Spotify, geliştirici-modu uygulamaların playlist <b>oluşturmasına</b> izin vermiyor.
                Sonucu “⬇ Dışa Aktar” ile indir, ücretsiz bir içe-aktarma aracıyla (ya da elle) Spotify’a koy.
              </div>
            )
            : <p className="text-sm text-red-300/85">⚠ {error}</p>
          )}
          {done && <AppliedSummary data={done} />}
          {!loading && !error && !done && data && <Preview kind={kind} data={data} />}
        </div>

        {/* alt çubuk */}
        {!done && (
          <div className="px-6 py-4 border-t border-[var(--border)]">
            <p className="text-xs text-[var(--faint)] mb-3 flex items-center gap-1.5">
              <span className="text-[var(--amber)]">⬡</span>
              Uygulama geri dönüşü zordur — ama her şey önce otomatik yedeklenir, Yedekler’den geri alabilirsin.
            </p>
            {/* Buton hiyerarşisi moda göre: gerçek hesapta Spotify yazmayı
                engellediği için Dışa Aktar birincil, Uygula ikincil + ipucu. */}
            <div className="flex justify-end gap-3 flex-wrap">
              <button className="btn btn-ghost" onClick={onClose}>İptal</button>
              {canDj && (
                <button className="btn btn-primary" onClick={() => setDjOpen(true)}>
                  ▶ DJ Çal
                </button>
              )}
              {!isForbidden && (isDemo ? (
                <button className={`btn ${canDj ? 'btn-ghost' : 'btn-primary'}`} onClick={apply}
                        disabled={loading || applying || !!error || nothingToApply}>
                  {applying ? 'Uygulanıyor…' : nothingToApply ? 'Uygulanacak bir şey yok' : applyLabel}
                </button>
              ) : (
                <div className="flex flex-col items-end gap-1">
                  <button className="btn btn-ghost" onClick={apply}
                          disabled={loading || applying || !!error || nothingToApply}>
                    {applying ? 'Uygulanıyor…' : nothingToApply ? 'Uygulanacak bir şey yok' : applyLabel}
                  </button>
                  <span className="text-[0.66rem] text-[var(--faint)] text-right max-w-[16rem]">
                    Spotify geliştirici-modunda yazmayı engelliyor — sonucu Dışa Aktar.
                  </span>
                </div>
              ))}
              <button className={`btn btn-ghost ${isForbidden ? 'btn-primary' : ''}`}
                      onClick={copyLinks} disabled={!canExport}>
                {copied ? '✓ Kopyalandı' : '🔗 Linkleri Kopyala'}
              </button>
              <button className={`btn ${(!canDj && (isForbidden || !isDemo)) ? 'btn-primary' : 'btn-ghost'}`}
                      onClick={exportCsv} disabled={!canExport}>
                ⬇ Dışa Aktar (CSV)
              </button>
            </div>
            {canDj && !isDemo && (
              <p className="text-[0.66rem] text-[var(--faint)] mt-2 text-right">
                Spotify’da tam şarkı: “Dışa Aktar (CSV)” → ücretsiz TuneMyMusic / Soundiiz ile içe aktar (sıra korunur).
              </p>
            )}
          </div>
        )}
        {done && (
          <div className="px-6 py-4 border-t border-[var(--border)] flex justify-end gap-3 flex-wrap">
            <button className="btn btn-ghost" onClick={copyLinks} disabled={!canExport}>
              {copied ? '✓ Kopyalandı' : '🔗 Linkleri Kopyala'}
            </button>
            <button className={`btn ${isDemo ? 'btn-ghost' : 'btn-primary'}`}
                    onClick={exportCsv} disabled={!canExport}>
              ⬇ Dışa Aktar (CSV)
            </button>
            <button className={`btn ${isDemo ? 'btn-primary' : 'btn-ghost'}`} onClick={onClose}>Bitti</button>
          </div>
        )}
      </div>
    </div>,
    document.body,
    )}
    <DjPlayer open={djOpen} tracks={data?.tracks || []} onClose={() => setDjOpen(false)} />
    </>
  )
}

function Preview({ kind, data }) {
  if (kind === 'groups') {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-sm text-[var(--dim)]">{data.groups.length} yeni liste oluşturulacak:</p>
        {data.groups.map((g) => (
          <div key={g.bucket || g.label} className="surface px-4 py-3">
            <div className="flex items-center justify-between mb-1">
              <span className="font-medium">{g.bucket || g.label}</span>
              <span className="mono text-xs text-[var(--faint)]">{g.count} parça</span>
            </div>
            <div className="text-xs text-[var(--dim)] truncate">
              {g.tracks.slice(0, 4).map((t) => t.title).join(' · ')}{g.tracks.length > 4 ? ' …' : ''}
            </div>
          </div>
        ))}
      </div>
    )
  }
  if (kind === 'dedupe') {
    return (
      <div>
        <p className="text-sm text-[var(--dim)] mb-3">
          <span className="mono text-[var(--amber)]">{data.removed_count}</span> tekrar bulundu ·
          <span className="mono"> {data.kept.length}</span> parça kalacak.
        </p>
        {data.removed_count === 0
          ? <p className="text-sm text-[var(--dim)]">Tekrar yok — liste zaten temiz. 🎧</p>
          : <TrackList tracks={data.removed} muted />}
      </div>
    )
  }
  // 'tracks'
  // Akıllı Mix: data.groups varsa türe-göre küme özetini parça listesinin üstünde göster.
  const groups = Array.isArray(data.groups)
    ? [...data.groups].sort((a, b) => (b.count || 0) - (a.count || 0))
    : null
  return (
    <>
      {groups && groups.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {groups.map((g) => (
            <span key={g.bucket || g.label} className="chip">
              {g.bucket || g.label} <span className="mono text-[var(--faint)]">{g.count}</span>
            </span>
          ))}
        </div>
      )}
      <p className="text-sm text-[var(--dim)] mb-3">{data.tracks.length} parça · yeni sıra:</p>
      <TrackList tracks={data.tracks} kind="tracks" />
    </>
  )
}

function TrackList({ tracks, muted, kind }) {
  // Geçiş göstergesi yalnızca akış sıralamasında (Geçişli Sırala / Akıllı Mix) ve
  // listede en az bir camelot/bpm varken — dedupe/groups'ta gösterme.
  const showTransitions = kind === 'tracks'
    && tracks.some((t) => t.camelot || t.bpm)
  return (
    <ol className="surface overflow-hidden">
      {tracks.map((t, i) => (
        <Fragment key={t.id + '-' + i}>
          {showTransitions && i > 0 && <TransitionRow a={tracks[i - 1]} b={t} />}
          <li className={`flex items-center gap-3 px-4 py-2 border-b border-[var(--border)] last:border-0 ${muted ? 'opacity-60' : ''}`}>
            <span className="mono w-6 text-right text-xs text-[var(--faint)]">{i + 1}</span>
            <AlbumArt src={t.image} alt={t.title} size={40} />
            <div className="flex-1 min-w-0">
              <div className="truncate text-sm">{t.title}</div>
              <div className="truncate text-xs text-[var(--dim)]">{t.artist}</div>
            </div>
            {t.camelot && (
              <span className="chip text-black/85" style={{ background: camelotColor(t.camelot) }}>{t.camelot}</span>
            )}
            {t.bpm && <span className="mono text-xs text-[var(--dim)] w-14 text-right">{t.bpm} BPM</span>}
            <span className="mono text-xs text-[var(--faint)] w-10 text-right">{fmtDuration(t.duration_ms)}</span>
          </li>
        </Fragment>
      ))}
    </ol>
  )
}

// İki ardışık parça arasındaki DJ geçiş kalitesi — diskret, satır akışını bozmayan ince rozet.
function TransitionRow({ a, b }) {
  const hasKeys = a.camelot && b.camelot
  const compatible = hasKeys && camelotCompatible(a.camelot, b.camelot)
  const bpmDelta = (a.bpm != null && b.bpm != null) ? Math.abs(a.bpm - b.bpm) : null
  if (!hasKeys && bpmDelta == null) return null // gösterilecek bilgi yok
  return (
    <li className="flex items-center gap-2 pl-12 pr-4 py-0.5 border-b border-[var(--border)] select-none"
        aria-hidden="true">
      {hasKeys && (
        <span className="chip"
              style={compatible
                ? { color: 'var(--teal)', background: 'rgba(52,216,196,0.10)' }
                : { color: 'var(--faint)', background: 'rgba(255,255,255,0.03)' }}>
          ⟶ {compatible ? 'uyumlu' : 'geçiş'}
        </span>
      )}
      {bpmDelta != null && (
        <span className="mono text-[0.66rem] text-[var(--faint)]">Δ{bpmDelta} BPM</span>
      )}
    </li>
  )
}

function AppliedSummary({ data }) {
  const created = data.created || []
  return (
    <div className="text-center py-4">
      <div className="w-12 h-12 mx-auto mb-3 rounded-full grid place-items-center text-[var(--amber)]"
           style={{ border: '1px solid var(--border-strong)' }}>✓</div>
      <h4 className="text-lg mb-1">Uygulandı</h4>
      {created.length > 0 && (
        <div className="mt-3 flex flex-col gap-1.5 max-w-sm mx-auto text-left">
          {created.map((c) => (
            <div key={c.id} className="surface px-3 py-2 flex items-center justify-between">
              <span className="truncate text-sm">{c.name}</span>
              <span className="mono text-xs text-[var(--faint)]">{c.count} parça</span>
            </div>
          ))}
        </div>
      )}
      {data.updated && (
        <p className="text-sm text-[var(--dim)] mt-2">Liste güncellendi · {data.updated.count} parça</p>
      )}
      {data.backup && <p className="mono text-xs text-[var(--faint)] mt-3">yedek alındı ✓</p>}
    </div>
  )
}
