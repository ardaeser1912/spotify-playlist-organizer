import { useState } from 'react'

// Tüm işlevler tek vitrinde. Loop her aracı kendi akışına (önizle→uygula) bağlar.
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

export default function ToolsView() {
  const [notice, setNotice] = useState(null)
  return (
    <div className="p-8 max-w-5xl">
      <header className="reveal mb-7">
        <div className="text-[0.7rem] tracking-[0.18em] uppercase text-[var(--amber)] mb-1">Araçlar</div>
        <h1 className="text-4xl">Tüm işlevler</h1>
        <p className="text-[var(--dim)] mt-2">Her araç güvenli: önce önizleme, sonra onaylı uygulama + otomatik yedek.</p>
      </header>

      {notice && <div className="reveal surface px-4 py-3 mb-6 text-sm text-[var(--dim)]">{notice}</div>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {TOOLS.map((t, i) => (
          <button
            key={t.key}
            onClick={() => setNotice(`“${t.title}” — loop bu aracı bağlayacak.`)}
            style={{ animationDelay: `${i * 45}ms` }}
            className="reveal card text-left p-5 transition hover:-translate-y-0.5 hover:border-[var(--border-strong)]"
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
    </div>
  )
}
