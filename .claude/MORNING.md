# MORNING — Şef'in Sabah Adımları ☕️

Loop, **görsel web panelini** yazıp DEMO veriyle test etti. İki aşama var:

## A) HEMEN — paneli demo veriyle aç (auth GEREKMEZ, 1 dk)
```
cd ~/spotify-playlist-organizer
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DEMO=1 python -m spotify_organizer.app        # backend (demo modu)
# yeni terminal:
cd web && npm install && npm run dev           # panel açılır
```
→ Tarayıcıda demo playlist'lerle "Türe Ayır" / "Geçişli Sırala" → Önizle → Uygula akışını görürsün. Hiçbir gerçek şeye dokunmaz.

## B) GERÇEK hesabına bağla (tek seferlik, ~5 dk)
### 1) Spotify Developer App
https://developer.spotify.com/dashboard → **Create app** → Redirect URI: `http://127.0.0.1:8888/callback` (localhost DEĞİL) → **Client ID** + **Secret** kopyala.
### 2) GetSongBPM key
https://getsongbpm.com/api → ücretsiz key (README'deki attribution linki kalsın).
### 3) `.env` doldur
`.env.example` → `.env`:
```
SPOTIPY_CLIENT_ID=...
SPOTIPY_CLIENT_SECRET=...
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
GETSONGBPM_API_KEY=...
```
### 4) Tek seferlik giriş
```
python auth.py        # tarayıcı açılır, onayla → token .cache'e yazılır
```
### 5) Paneli gerçek modda aç
```
python -m spotify_organizer.app      # DEMO=1 olmadan → gerçek playlist'lerin
cd web && npm run dev
```
İlk denemede **Önizle** ile bak, iyiyse **Uygula** (otomatik yedek alır).

---
## ✅ Loop ne yaptı (F1–F6 BİTTİ, 15 Haz gece)
- **F1** çekirdek motor: genre / order(Camelot) / enrich(GetSongBPM) / organize — saf Python + mock.
- **F2** servis (önizle/uygula + backup/restore) + 21 Flask endpoint + DemoClient.
- **F3+F4** 4 ekran canlı bağlandı (PreviewModal önizle→uygula, güvenlik uyarısı, yedek özeti); İçgörüler canlı grafikler; Yedekler + Geri Al.
- **F5** doğrulama: **97 pytest yeşil** + `npm run build` temiz + **7 ekran headless-chromium ile görsel doğrulandı, konsol hatası yok**.
- **F6** README + bu dosya + `auth.py` (tek seferlik OAuth) yazıldı.
- Tümü branch `loop/v1`'de küçük commit'lerle (PUSH YOK). Gerçek API/auth ÇAĞRILMADI (CERRAH).

## 🛡️ Sertleştirme loop'u (Şef "güvenli hardening" seçti, paralel ajanlar)
- **Tur 1:** +33 edge-case testi (boş/tek/None/sınır/eksik-dosya → toplam **130 test**, crash bulunmadı) · PreviewModal a11y (role=dialog/aria-modal, Escape ile kapat, focus-trap + odak iadesi) · shell/nav a11y (aria-label, aria-current, ikon aria-hidden). Build temiz.
- **Tur 2:** (c) frontend durumları DENETLENDİ → 4 view'da loading/error/empty ZATEN tam (F3'te yapılmış), gold-plating yapılmadı · (d) PERFORMANS ölçüldü: organize işlemleri 5000 track'te <3ms; `harmonic_order` O(n²) ama 5000'de **407ms (<1.5s)** → kod değişmedi, **7 perf guard testi** eklendi · (e) README'ye "🖥️ Ekran akışı" bölümü · **BONUS bug fix:** `organize.insights()` `popularity=None` olunca TypeError atıyordu (Hızlı Zenco buldu) → `(t.get('popularity') or 0)` + regresyon testi. **Toplam 138 test yeşil.**
- **Genişletilmiş Tur 1 (Şef "baştan sona hazır olsun, loop dursun mu?" deyince yeniden başlatıldı):** (f) **GERÇEK İSTEMCİ TESTLERİ** — SpotipyClient şimdiye dek SIFIR test'liydi (en kritik eksik); sahte spotipy ile +36 test (normalize/pagination/batch'leme/create-replace). (g) **ENTEGRASYON round-trip** — apply→backups→restore tam döngü, her aracın apply'ı + preview-yedek-yazmaz güvencesi, +12 senaryo. (h) **GetSongBPM fetcher dayanıklılığı** — try/except + timeout + tip-güvenli tempo + key_of fallback, +16 ağsız test. **Toplam 202 test yeşil, build temiz.**
- **Genişletilmiş Tur 2:** (i) **GÖRSEL QA** — apply akışı uçtan uca çekildi (önizle→Listeleri Oluştur→başarı özeti→dolu Yedekler→Geri Al) + sort/merge araç panelleri; konsol hatası YOK. **1 GERÇEK UX bug bulundu+düzeltildi (j):** PlaylistsView'da apply sonrası modal anında kapanıyordu (`onApplied`→`setModal(null)`), başarı özeti ("Uygulandı + yedek alındı ✓") görünmüyordu; ToolsView ile tutarsızdı → no-op yapıldı, artık özet görünüyor + "Bitti" ile kapanıyor. 8 ekran `/tmp/spo-shot/`'ta.
- **🏁 LOOP DURDU (end-to-end hazır):** sertleştirme+tamamlama backlog'unun (a–j) HEPSİ tamam — **202 test yeşil, build temiz, 8 ekran görsel doğrulandı, gerçek-istemci yolu test'li, uçtan uca akış (apply→yedek→restore) kanıtlı.** Geriye SADECE Şef'e bağlı işler kaldı (aşağıdaki 3 karar + GitHub push). Gereksiz gold-plating yapılmadı.

## 🟡 Şef kararı / doğrulama bekleyenler
- **GetSongBPM `open_key`→Camelot eşlemesi BELGELENMİŞ VARSAYIM.** Gerçek key ile (`enrich.build_getsongbpm_fetch`) bir-iki şarkıda tempo+key dönüşünü teyit et; alan adı (`open_key`/`key_of`) farklıysa `enrich.open_key_to_camelot`'u ayarla. Mock testler şekilden bağımsız geçiyor.
- **Tür kova önceliği:** Arabesk > Hip-Hop > Elektronik > R&B > Rock > Pop (ilk eşleşen kazanır). DEMO'da doğru görünüyor; gerçek kütüphanende tuhaf bir eşleme olursa `genre.py` tablosuna kova/anahtar ekleriz.
- **Beğenilenler'i gerçekten silme/azaltma** istemiyoruz: dedupe/sort/order Beğenilenler'de hep KOPYA üretir (kilitli karar #6). Normal playlist'lerde `replace` ile yerinde günceller (önce yedek). Bu davranışı onaylıyor musun?
- (Backlog — loop YAPMADI: gerçek deploy, mood/enerji boyutu, dev-mode 25-kişi aşımı.)
