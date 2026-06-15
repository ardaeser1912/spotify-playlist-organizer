// Basit API yardımcısı (Vite /api'yi Flask backend'e proxy'ler)
export async function api(path) {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`${path} → HTTP ${r.status}`)
  return r.json()
}

// POST yardımcısı — body JSON, dönüş {success,data,error} zarfı.
// Backend hata zarfını (success:false) okuyup mesajı fırlatır.
export async function post(path, body) {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  })
  let j = null
  try { j = await r.json() } catch { /* gövdesiz hata */ }
  if (!r.ok || (j && j.success === false)) {
    throw new Error((j && j.error) || `${path} → HTTP ${r.status}`)
  }
  return j
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

// Camelot kodunu ayrıştırır: "8B" → { n: 8, m: 'B' }. Geçersiz → null.
function parseCamelot(code) {
  if (!code) return null
  const match = /^(\d{1,2})([AB])$/.exec(String(code).trim().toUpperCase())
  if (!match) return null
  const n = parseInt(match[1], 10)
  if (n < 1 || n > 12) return null
  return { n, m: match[2] }
}

// İki Camelot kodu harmonic uyumlu mu (DJ geçişi). Kurallar: aynı kod;
// aynı sayı diğer harf (8A↔8B); sayı ±1 aynı harf (wrap 12↔1). Geçersiz/null → false.
export function camelotCompatible(a, b) {
  const x = parseCamelot(a)
  const y = parseCamelot(b)
  if (!x || !y) return false
  if (x.n === y.n && x.m === y.m) return true       // aynı kod
  if (x.n === y.n && x.m !== y.m) return true        // aynı sayı, diğer harf
  if (x.m === y.m) {                                  // aynı harf, sayı ±1 (wrap)
    const diff = Math.abs(x.n - y.n)
    if (diff === 1 || diff === 11) return true
  }
  return false
}
