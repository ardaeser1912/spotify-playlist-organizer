// Yedekler — her uygulanan işlemden önce otomatik yedek alınır; buradan Geri Al.
// Loop bunu gerçek yedek listesine + restore akışına bağlar.
export default function BackupsView() {
  return (
    <div className="p-8 max-w-4xl">
      <header className="reveal mb-7">
        <div className="text-[0.7rem] tracking-[0.18em] uppercase text-[var(--amber)] mb-1">Yedekler</div>
        <h1 className="text-4xl">Güvenlik ağı</h1>
        <p className="text-[var(--dim)] mt-2">Her “Uygula” öncesi playlist otomatik yedeklenir — tek tıkla geri alabilirsin.</p>
      </header>

      <div className="reveal card p-10 text-center">
        <div className="w-14 h-14 mx-auto mb-4 rounded-full border border-[var(--border-strong)] grid place-items-center text-[var(--amber)]">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="4" rx="1" /><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8M10 12h4" />
          </svg>
        </div>
        <h3 className="text-xl mb-1">Henüz yedek yok</h3>
        <p className="text-[var(--dim)] max-w-sm mx-auto">Bir işlem uyguladığında yedek burada görünür ve istediğin an geri yükleyebilirsin.</p>
      </div>
    </div>
  )
}
