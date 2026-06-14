// İçgörüler — loop, gerçek grafikleri (tür/BPM/on-yıl dağılımı) buraya bağlar.
// Şimdilik tasarlanmış bir önizleme iskeleti (boş ekran değil).
const CARDS = [
  { title: 'Tür Dağılımı', hint: 'Pop · Rock · Elektronik · Rap · Türkçe' },
  { title: 'BPM Yoğunluğu', hint: 'Tempo histogramı' },
  { title: 'On-Yıllar', hint: '90’lar → 2020’ler' },
  { title: 'En Çok Sanatçılar', hint: 'İlk 10' },
]

export default function InsightsView() {
  return (
    <div className="p-8 max-w-5xl">
      <header className="reveal mb-7">
        <div className="text-[0.7rem] tracking-[0.18em] uppercase text-[var(--amber)] mb-1">İçgörüler</div>
        <h1 className="text-4xl">Kütüphanen, sayılarla</h1>
        <p className="text-[var(--dim)] mt-2">Tür, tempo ve dönem dağılımları — yakında canlı grafiklerle.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {CARDS.map((c, i) => (
          <div key={c.title} style={{ animationDelay: `${i * 60}ms` }} className="reveal card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg">{c.title}</h3>
              <span className="chip bg-white/5 text-[var(--faint)]">yakında</span>
            </div>
            {/* iskelet çubukları */}
            <div className="flex items-end gap-2 h-28">
              {[40, 72, 55, 88, 34, 64, 48].map((h, j) => (
                <div
                  key={j}
                  className="flex-1 rounded-t"
                  style={{
                    height: `${h}%`,
                    background: `linear-gradient(180deg, rgba(255,178,76,${0.35 - j * 0.03}), rgba(255,178,76,0.05))`,
                  }}
                />
              ))}
            </div>
            <p className="mono text-xs text-[var(--faint)] mt-3">{c.hint}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
