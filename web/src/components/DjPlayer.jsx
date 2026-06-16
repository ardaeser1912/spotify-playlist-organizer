import { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { camelotColor, camelotCompatible } from '../lib/api'
import AlbumArt from './AlbumArt'

/**
 * DJ Modu — sıralı parçaları (Geçişli Sırala / Akıllı Mix çıktısı) 30sn önizlemelerle
 * art arda çalar, her geçişte iki deck arasında CROSSFADE yapar ve geçiş kalitesini
 * (Camelot uyumu + Δ BPM) CANLI gösterir. Önizleme /api/preview'dan (Deezer→iTunes) gelir;
 * Spotify'a dokunmaz. Önizlemesi olmayan parça otomatik atlanır.
 *
 * Props: open, tracks (sıralı [{id,title,artist,image,bpm,camelot}]), onClose
 */
const CROSSFADE_SEC = 4
const TICK_MS = 50

export default function DjPlayer({ open, tracks = [], onClose }) {
  const [idx, setIdx] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0) // 0..1 (mevcut deck)
  const [status, setStatus] = useState('')
  const [fading, setFading] = useState(false)

  const deckA = useRef(null)
  const deckB = useRef(null)
  const curDeck = useRef(0) // 0=A, 1=B (CURRENT parçayı çalan deck)
  const idxRef = useRef(0)
  const urlCache = useRef(new Map()) // track.id -> url|null
  const fadeTimer = useRef(null)
  const startedRef = useRef(false)

  const deckEl = (n) => (n === 0 ? deckA.current : deckB.current)

  const fetchUrl = useCallback(async (t) => {
    if (!t) return null
    const cache = urlCache.current
    if (cache.has(t.id)) return cache.get(t.id)
    try {
      const qs = new URLSearchParams({ artist: t.artist || '', title: t.title || '' })
      const r = await fetch(`/api/preview?${qs.toString()}`)
      const j = await r.json()
      const url = j?.data?.url || null
      cache.set(t.id, url)
      return url
    } catch {
      cache.set(t.id, null)
      return null
    }
  }, [])

  // Belirli bir parçayı (verili deck'e) yükleyip çal. Önizleme yoksa sonrakine atla.
  const playTrack = useCallback(async (trackIndex, deck) => {
    if (trackIndex >= tracks.length) { setPlaying(false); setStatus('Set bitti 🎧'); return }
    idxRef.current = trackIndex
    setIdx(trackIndex)
    setStatus('Önizleme aranıyor…')
    const url = await fetchUrl(tracks[trackIndex])
    if (idxRef.current !== trackIndex) return // bu sırada ileri sarıldıysa iptal
    if (!url) {
      setStatus(`“${tracks[trackIndex].title}” için önizleme yok — atlanıyor`)
      return playTrack(trackIndex + 1, deck)
    }
    setStatus('')
    const el = deckEl(deck)
    if (!el) return
    el.src = url
    el.volume = 1
    curDeck.current = deck
    try { await el.play(); setPlaying(true) } catch { setPlaying(false) }
    // sonrakini ön-getir (crossfade gecikmesiz olsun)
    if (tracks[trackIndex + 1]) fetchUrl(tracks[trackIndex + 1])
  }, [tracks, fetchUrl])

  // İki deck arası crossfade → sonraki parçaya geç.
  const crossfadeNext = useCallback(async (fadeSec = CROSSFADE_SEC) => {
    if (fadeTimer.current) return // zaten geçişte
    const next = idxRef.current + 1
    if (next >= tracks.length) {
      const el = deckEl(curDeck.current)
      if (el) el.pause()
      setPlaying(false); setStatus('Set bitti 🎧')
      return
    }
    const url = await fetchUrl(tracks[next])
    const from = curDeck.current
    const to = from === 0 ? 1 : 0
    const fromEl = deckEl(from)
    const toEl = deckEl(to)
    if (!url || !toEl) { // önizleme yok → sert atla
      if (fromEl) fromEl.pause()
      return playTrack(next, to)
    }
    toEl.src = url
    toEl.volume = 0
    try { await toEl.play() } catch { /* yok say */ }
    idxRef.current = next
    setIdx(next)
    setFading(true)
    if (tracks[next + 1]) fetchUrl(tracks[next + 1])

    const steps = Math.max(1, Math.round((fadeSec * 1000) / TICK_MS))
    let i = 0
    fadeTimer.current = setInterval(() => {
      i += 1
      const r = Math.min(1, i / steps)
      if (fromEl) fromEl.volume = Math.max(0, 1 - r)
      toEl.volume = Math.min(1, r)
      if (r >= 1) {
        clearInterval(fadeTimer.current); fadeTimer.current = null
        if (fromEl) { fromEl.pause(); fromEl.currentTime = 0 }
        curDeck.current = to
        setFading(false)
      }
    }, TICK_MS)
  }, [tracks, fetchUrl, playTrack])

  // mevcut deck ilerleme + bitişe yakın otomatik crossfade
  useEffect(() => {
    if (!open) return
    const id = setInterval(() => {
      const el = deckEl(curDeck.current)
      if (!el || !el.duration || Number.isNaN(el.duration)) return
      setProgress(el.currentTime / el.duration)
      const remaining = el.duration - el.currentTime
      if (!el.paused && remaining <= CROSSFADE_SEC && !fadeTimer.current) {
        crossfadeNext(Math.min(CROSSFADE_SEC, Math.max(1, remaining)))
      }
    }, 120)
    return () => clearInterval(id)
  }, [open, crossfadeNext])

  // açılışta ilk parçayı başlat; kapanışta her şeyi durdur + sıfırla
  useEffect(() => {
    if (!open) { startedRef.current = false; return }
    if (startedRef.current) return
    startedRef.current = true
    idxRef.current = 0; setIdx(0); setProgress(0); curDeck.current = 0
    playTrack(0, 0)
    return () => {
      if (fadeTimer.current) { clearInterval(fadeTimer.current); fadeTimer.current = null }
      ;[deckA.current, deckB.current].forEach((el) => { if (el) { el.pause(); el.src = '' } })
    }
  }, [open, playTrack])

  function togglePlay() {
    const el = deckEl(curDeck.current)
    if (!el) return
    if (el.paused) { el.play(); if (fadeTimer.current) deckEl(curDeck.current === 0 ? 1 : 0)?.play(); setPlaying(true) }
    else { el.pause(); deckEl(curDeck.current === 0 ? 1 : 0)?.pause(); setPlaying(false) }
  }

  if (!open) return null

  const cur = tracks[idx] || {}
  const next = tracks[idx + 1] || null
  const compatible = next && cur.camelot && next.camelot && camelotCompatible(cur.camelot, next.camelot)
  const bpmDelta = (next && cur.bpm != null && next.bpm != null) ? Math.abs(cur.bpm - next.bpm) : null

  return createPortal(
    <div className="fixed inset-0 z-[60] grid place-items-center p-4"
         style={{ background: 'rgba(4,4,7,0.78)', backdropFilter: 'blur(6px)' }} onClick={onClose}>
      <audio ref={deckA} preload="auto" />
      <audio ref={deckB} preload="auto" />
      <div role="dialog" aria-modal="true" aria-label="DJ Modu"
           className="card reveal w-full max-w-md flex flex-col" style={{ animationDuration: '0.32s' }}
           onClick={(e) => e.stopPropagation()}>
        {/* başlık */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div>
            <div className="text-[0.66rem] tracking-[0.18em] uppercase text-[var(--amber)]">DJ Modu · Geçişli Çal</div>
            <h3 className="text-lg">{idx + 1} / {tracks.length}</h3>
          </div>
          <button className="btn btn-ghost px-3 py-1.5" onClick={onClose} aria-label="Kapat">✕</button>
        </div>

        <div className="px-6 py-5">
          {/* şimdi çalan */}
          <div className="flex items-center gap-4">
            <AlbumArt src={cur.image} alt={cur.title} size={72} />
            <div className="min-w-0 flex-1">
              <div className="truncate text-lg">{cur.title || '—'}</div>
              <div className="truncate text-sm text-[var(--dim)]">{cur.artist || ''}</div>
              <div className="flex items-center gap-2 mt-1.5">
                {cur.camelot && (
                  <span className="chip text-black/85" style={{ background: camelotColor(cur.camelot) }}>{cur.camelot}</span>
                )}
                {cur.bpm != null && <span className="mono text-xs text-[var(--dim)]">{cur.bpm} BPM</span>}
              </div>
            </div>
          </div>

          {/* ilerleme */}
          <div className="mt-4 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-2)' }}>
            <div className="h-full rounded-full transition-[width] duration-150"
                 style={{ width: `${Math.round(progress * 100)}%`, background: 'var(--amber)' }} />
          </div>
          {status && <p className="text-xs text-[var(--faint)] mt-2">{status}</p>}

          {/* geçiş kartı → sıradaki */}
          {next && (
            <div className="mt-5 surface px-4 py-3">
              <div className="flex items-center gap-2 mb-2">
                <span className="chip" style={compatible
                  ? { color: 'var(--teal)', background: 'rgba(52,216,196,0.12)' }
                  : { color: 'var(--faint)', background: 'rgba(255,255,255,0.04)' }}>
                  ⟶ {compatible ? 'uyumlu geçiş' : 'geçiş'}
                </span>
                {bpmDelta != null && <span className="mono text-[0.7rem] text-[var(--faint)]">Δ{bpmDelta} BPM</span>}
                {fading && <span className="mono text-[0.7rem] text-[var(--amber)]">crossfade…</span>}
              </div>
              <div className="flex items-center gap-3 opacity-80">
                <AlbumArt src={next.image} alt={next.title} size={36} />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm">{next.title}</div>
                  <div className="truncate text-xs text-[var(--dim)]">{next.artist}</div>
                </div>
                {next.camelot && (
                  <span className="chip text-black/85" style={{ background: camelotColor(next.camelot) }}>{next.camelot}</span>
                )}
              </div>
            </div>
          )}

          {/* kontroller */}
          <div className="mt-5 flex items-center justify-center gap-3">
            <button className="btn btn-ghost" onClick={togglePlay} aria-label={playing ? 'Duraklat' : 'Çal'}>
              {playing ? '⏸ Duraklat' : '▶ Çal'}
            </button>
            <button className="btn btn-primary" onClick={() => crossfadeNext(1.2)}
                    disabled={!next} aria-label="Sıradakine geç">
              Geç ▶▶
            </button>
          </div>
          <p className="text-[0.66rem] text-[var(--faint)] text-center mt-3">
            30sn önizlemelerle çalar (Deezer/iTunes) — geçişleri duyman için. Tam şarkı için “Dışa Aktar”.
          </p>
        </div>
      </div>
    </div>,
    document.body,
  )
}
