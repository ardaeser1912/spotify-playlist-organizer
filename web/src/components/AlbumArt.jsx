import { useState } from 'react'

/**
 * Parça satırlarında küçük albüm kapağı.
 * src varsa kareyi lazy yükler; yoksa veya görsel kırılırsa şık bir
 * "Gece Stüdyosu" fallback (vinil disk glyph + --bg-2 zemin) gösterir.
 *
 * Props: src, alt, size = 40 (px)
 */
export default function AlbumArt({ src, alt = '', size = 40 }) {
  const [imgError, setImgError] = useState(false)
  const box = {
    width: size,
    height: size,
    borderRadius: 8,
  }

  if (!src || imgError) {
    return (
      <div
        className="shrink-0 grid place-items-center border border-[var(--border)]"
        style={{ ...box, background: 'var(--bg-2)' }}
        aria-hidden="true"
      >
        <svg width={Math.round(size * 0.5)} height={Math.round(size * 0.5)} viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="9" stroke="var(--faint)" strokeWidth="1.4" />
          <circle cx="12" cy="12" r="2.2" fill="var(--amber)" />
          <circle cx="12" cy="12" r="5.2" stroke="var(--faint)" strokeWidth="0.8" opacity="0.6" />
        </svg>
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setImgError(true)}
      className="shrink-0 object-cover border border-[var(--border)]"
      style={box}
    />
  )
}
