import { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { camelotColor, camelotCompatible } from '../lib/api'
import AlbumArt from './AlbumArt'

/**
 * DJ Modu — GERÇEK beatmatch + crossfade (Web Audio API).
 * Geçişte: giden parça tempo'sunu (playbackRate) sonrakinin BPM'ine RAMPLA yavaşlatır/hızlandırır
 * (vinil pitch-fader gibi) + iki parça ÜST ÜSTE binerek gain ile crossfade olur → "ilk şarkı
 * yavaşlar, BPM uyar, diğeri yavaşça gelir". Ham ses /api/preview-audio'dan aynı-origin gelir
 * (decodeAudioData CORS ister). Önizlemesi olmayan parça atlanır, sonraki ön-decode edilir.
 *
 * Props: open, tracks (sıralı [{id,title,artist,image,bpm,camelot}]), onClose
 */
const BLEND_SEC = 7       // geçiş süresi (crossfade + beatmatch)
const SKIP_BLEND = 2.5    // "Geç" ile hızlı ama yine de yumuşak

// BPM oranını müzikal aralığa katla (yarı/çift tempo) → aşırı pitch bozulması olmasın.
function beatmatchRatio(fromBpm, toBpm) {
  if (!fromBpm || !toBpm) return 1
  let r = toBpm / fromBpm
  while (r < 0.7) r *= 2
  while (r > 1.43) r /= 2
  return r
}

export default function DjPlayer({ open, tracks = [], onClose }) {
  const [idx, setIdx] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('')
  const [blending, setBlending] = useState(false)

  const ctxRef = useRef(null)
  const bufRef = useRef(new Map())   // id -> AudioBuffer | null (decode cache)
  const pendRef = useRef(new Map())  // id -> Promise (uçuşan decode)
  const curRef = useRef(null)        // {source, gain, bpm, duration, startedAt}
  const idxRef = useRef(0)
  const blendingRef = useRef(false)
  const blendUntilRef = useRef(0)
  const startedRef = useRef(false)

  const getCtx = useCallback(() => {
    if (!ctxRef.current) {
      const AC = window.AudioContext || window.webkitAudioContext
      ctxRef.current = new AC()
    }
    if (ctxRef.current.state === 'suspended') ctxRef.current.resume()
    return ctxRef.current
  }, [])

  // Önizleme sesini indir + decode (cache'li). Yoksa null.
  const getBuffer = useCallback((track) => {
    if (!track) return Promise.resolve(null)
    const id = track.id
    if (bufRef.current.has(id)) return Promise.resolve(bufRef.current.get(id))
    if (pendRef.current.has(id)) return pendRef.current.get(id)
    const ctx = getCtx()
    const promise = (async () => {
      try {
        const qs = new URLSearchParams({ artist: track.artist || '', title: track.title || '' })
        const r = await fetch(`/api/preview-audio?${qs.toString()}`)
        if (!r.ok) throw new Error('no preview')
        const ab = await r.arrayBuffer()
        const buf = await ctx.decodeAudioData(ab)
        bufRef.current.set(id, buf)
        return buf
      } catch {
        bufRef.current.set(id, null)
        return null
      } finally {
        pendRef.current.delete(id)
      }
    })()
    pendRef.current.set(id, promise)
    return promise
  }, [getCtx])

  // Bir parçayı yeni deck olarak baştan çal (gain fade-in).
  const startTrack = useCallback(async (trackIndex, fadeIn = 0.5) => {
    if (trackIndex >= tracks.length) { setPlaying(false); setStatus('Set bitti 🎧'); return }
    idxRef.current = trackIndex; setIdx(trackIndex)
    setStatus('Önizleme yükleniyor…')
    const track = tracks[trackIndex]
    const buf = await getBuffer(track)
    if (idxRef.current !== trackIndex) return
    if (!buf) { setStatus(`“${track.title}” için önizleme yok — atlanıyor`); return startTrack(trackIndex + 1, fadeIn) }
    setStatus('')
    const ctx = getCtx()
    const source = ctx.createBufferSource(); source.buffer = buf
    const gain = ctx.createGain()
    source.connect(gain); gain.connect(ctx.destination)
    const now = ctx.currentTime
    gain.gain.setValueAtTime(0.0001, now)
    gain.gain.linearRampToValueAtTime(1, now + fadeIn)
    source.start(now)
    curRef.current = { source, gain, bpm: track.bpm, duration: buf.duration, startedAt: now }
    setPlaying(true)
    if (tracks[trackIndex + 1]) getBuffer(tracks[trackIndex + 1])  // ön-decode
  }, [tracks, getBuffer, getCtx])

  // GERÇEK geçiş: beatmatch (tempo rampası) + crossfade (gain) → sonraki parça.
  const blendNext = useCallback(async (blendSec = BLEND_SEC) => {
    if (blendingRef.current) return
    const cur = curRef.current
    const nextIndex = idxRef.current + 1
    if (!cur || nextIndex >= tracks.length) return
    blendingRef.current = true; setBlending(true)
    const nextTrack = tracks[nextIndex]
    const buf = await getBuffer(nextTrack)
    const ctx = getCtx()
    if (!buf) { // önizleme yok → sert geç (nadiren)
      try { cur.source.stop() } catch { /* yok say */ }
      blendingRef.current = false; setBlending(false)
      return startTrack(nextIndex)
    }
    const now = ctx.currentTime
    const nextSource = ctx.createBufferSource(); nextSource.buffer = buf
    const nextGain = ctx.createGain()
    nextSource.connect(nextGain); nextGain.connect(ctx.destination)
    // gelen: 0 → 1 (yavaşça gelir)
    nextGain.gain.setValueAtTime(0.0001, now)
    nextGain.gain.linearRampToValueAtTime(1, now + blendSec)
    // giden: gain 1 → 0  +  tempo 1 → beatmatch oranı (yavaşlar/hızlanır, BPM uyar)
    cur.gain.gain.cancelScheduledValues(now)
    cur.gain.gain.setValueAtTime(cur.gain.gain.value, now)
    cur.gain.gain.linearRampToValueAtTime(0.0001, now + blendSec)
    const ratio = beatmatchRatio(cur.bpm, nextTrack.bpm)
    cur.source.playbackRate.cancelScheduledValues(now)
    cur.source.playbackRate.setValueAtTime(cur.source.playbackRate.value, now)
    cur.source.playbackRate.linearRampToValueAtTime(ratio, now + blendSec)
    nextSource.start(now)
    try { cur.source.stop(now + blendSec + 0.15) } catch { /* yok say */ }
    // promote: yeni deck artık "current"
    curRef.current = { source: nextSource, gain: nextGain, bpm: nextTrack.bpm, duration: buf.duration, startedAt: now }
    idxRef.current = nextIndex; setIdx(nextIndex)
    blendUntilRef.current = now + blendSec
    if (tracks[nextIndex + 1]) getBuffer(tracks[nextIndex + 1])  // bir sonrakini ön-decode
  }, [tracks, getBuffer, getCtx, startTrack])

  // ilerleme + bitişe yakın otomatik geçiş + blend bayrağını indir (ctx saatiyle → pause-güvenli)
  useEffect(() => {
    if (!open) return
    const iv = setInterval(() => {
      const ctx = ctxRef.current, cur = curRef.current
      if (!ctx || !cur) return
      const elapsed = ctx.currentTime - cur.startedAt
      setProgress(Math.max(0, Math.min(1, elapsed / cur.duration)))
      if (blendingRef.current && ctx.currentTime >= blendUntilRef.current) {
        blendingRef.current = false; setBlending(false)
      }
      if (ctx.state === 'running' && !blendingRef.current
          && idxRef.current + 1 < tracks.length
          && cur.duration - elapsed <= BLEND_SEC) {
        blendNext(Math.min(BLEND_SEC, Math.max(2, cur.duration - elapsed)))
      }
    }, 100)
    return () => clearInterval(iv)
  }, [open, blendNext, tracks.length])

  // açılışta başlat; kapanışta sesi durdur + context'i kapat
  useEffect(() => {
    if (!open) { startedRef.current = false; return }
    if (startedRef.current) return
    startedRef.current = true
    idxRef.current = 0; setIdx(0); setProgress(0); blendingRef.current = false
    startTrack(0, 0.6)
    return () => {
      try { curRef.current?.source?.stop() } catch { /* yok say */ }
      curRef.current = null
      if (ctxRef.current) { try { ctxRef.current.close() } catch { /* yok say */ } ctxRef.current = null }
      bufRef.current.clear(); pendRef.current.clear()
    }
  }, [open, startTrack])

  function togglePlay() {
    const ctx = ctxRef.current
    if (!ctx) return
    if (ctx.state === 'running') { ctx.suspend(); setPlaying(false) }
    else { ctx.resume(); setPlaying(true) }
  }

  if (!open) return null

  const cur = tracks[idx] || {}
  const next = tracks[idx + 1] || null
  const compatible = next && cur.camelot && next.camelot && camelotCompatible(cur.camelot, next.camelot)
  const bpmDelta = (next && cur.bpm != null && next.bpm != null) ? Math.abs(cur.bpm - next.bpm) : null

  return createPortal(
    <div className="fixed inset-0 z-[60] grid place-items-center p-4"
         style={{ background: 'rgba(4,4,7,0.78)', backdropFilter: 'blur(6px)' }} onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-label="DJ Modu"
           className="card reveal w-full max-w-md flex flex-col" style={{ animationDuration: '0.32s' }}
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div>
            <div className="text-[0.66rem] tracking-[0.18em] uppercase text-[var(--amber)]">DJ Modu · Beatmatch Geçiş</div>
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
            <div className="h-full rounded-full" style={{ width: `${Math.round(progress * 100)}%`, background: 'var(--amber)' }} />
          </div>
          {status && <p className="text-xs text-[var(--faint)] mt-2">{status}</p>}

          {/* geçiş kartı → sıradaki */}
          {next && (
            <div className="mt-5 surface px-4 py-3" style={blending ? { boxShadow: '0 0 0 1px var(--amber) inset' } : undefined}>
              <div className="flex items-center gap-2 mb-2">
                <span className="chip" style={compatible
                  ? { color: 'var(--teal)', background: 'rgba(52,216,196,0.12)' }
                  : { color: 'var(--faint)', background: 'rgba(255,255,255,0.04)' }}>
                  ⟶ {compatible ? 'uyumlu geçiş' : 'geçiş'}
                </span>
                {bpmDelta != null && <span className="mono text-[0.7rem] text-[var(--faint)]">Δ{bpmDelta} BPM</span>}
                {blending && <span className="mono text-[0.7rem] text-[var(--amber)]">⟳ beatmatch + crossfade…</span>}
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
            <button className="btn btn-primary" onClick={() => blendNext(SKIP_BLEND)} disabled={!next} aria-label="Sıradakine geç">
              Geç ▶▶
            </button>
          </div>
          <p className="text-[0.66rem] text-[var(--faint)] text-center mt-3">
            30sn önizlemelerle gerçek beatmatch geçiş — giden parça yavaşlar, BPM uyar, sonraki üstüne biner. Tam şarkı için “Dışa Aktar”.
          </p>
        </div>
      </div>
    </div>,
    document.body,
  )
}
