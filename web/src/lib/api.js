// Basit API yardımcısı (Vite /api'yi Flask backend'e proxy'ler)
export async function api(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`${path} → HTTP ${r.status}`)
  return r.json()
}

export function fmtDuration(ms) {
  const s = Math.round(ms / 1000)
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

// Camelot kodu (örn "8B") → çark üzerindeki renk. İmza data-viz dokunuşu.
export function camelotColor(code) {
  if (!code) return null
  const n = parseInt(code, 10) // 1..12
  if (Number.isNaN(n)) return null
  const isMajor = code.slice(-1).toUpperCase() === 'B'
  const hue = ((n - 1) / 12) * 360
  return `hsl(${hue} 68% ${isMajor ? 56 : 44}%)`
}
