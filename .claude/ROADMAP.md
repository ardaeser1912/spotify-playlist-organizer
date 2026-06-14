# ROADMAP — Spotify Playlist Organizer (ÇOK İŞLEVLİ WEB APP)

> Loop'un beyni. Her iterasyonda önce bunu oku. Kilitli kararlara dokunma.

## 🎯 Amaç
Spotify tarzı **görsel, çok işlevli web paneli** ("Gece Stüdyosu" tasarımı). İşlevler:
1. **Türe göre ayır** — karışık liste / Beğenilenler → türe göre YENİ playlist'ler.
2. **Geçişli sırala (DJ)** — harmonic mixing (Camelot) + BPM rampası.
3. **Tekrarları temizle** — duplicate bul & kaldır.
4. **Çok-anahtarlı sırala** — sanatçı/albüm/eklenme/çıkış tarihi/popülerlik/BPM/süre/alfabetik.
5. **Birleştir & Böl** — playlist'leri birleştir; on-yıla / tempo bölgesine / boyuta göre böl.
6. **Keşif** — top şarkı/sanatçılardan playlist + katalog arama & ekleme.
7. **İçgörüler** — tür/BPM/on-yıl dağılımı, en çok sanatçılar, ort. popülerlik (grafikler).
8. **Yedek & Geri Al** — her apply öncesi otomatik yedek + restore.

## 🔒 KİLİTLİ KARARLAR (değiştirme = Şef onayı)
1. **Stack:** Backend Python+Flask+spotipy+requests. Frontend React+Vite+Tailwind v4. Çekirdek mantık saf modüllerde.
2. **TASARIM DİLİ — "Gece Stüdyosu" (KİLİTLİ, mevcut `web/src/index.css` token'ları):**
   - Renk: derin gece-siyahı (`--bg #08080b`), sıcak amber imza (`--amber #ffb24c`), serin teal ikincil, sahne-ışığı glow + film grain.
   - Tipografi: Display=Bricolage Grotesque, Body=Hanken Grotesk, Mono=JetBrains Mono (BPM/Camelot/süre = mono).
   - İmza: **Camelot renk çipleri** (`camelotColor()` `lib/api.js`), vinil disk logo, staggered `.reveal`.
   - **Loop MEVCUT token + sınıfları (`.card .btn .btn-primary .btn-ghost .chip .nav-item .surface .reveal`) KULLANIR — yeni stil icat etmez.** Yeni AI-slop görünüm YASAK.
3. **DEMO modu (`DEMO=1`):** fixture veriyle panel auth OLMADAN tam çalışır. Tüm yeni özellikler DEMO'da da çalışmalı (fixtures.py'de bpm/camelot/year/popularity var).
4. **BPM/key kaynağı:** GetSongBPM (Spotify Audio Features Kasım 2024 kapandı). Cache `cache/bpm.json`. README attribution ZORUNLU.
5. **Tür kaynağı:** sanatçı `genres` → ana kovalara normalize. Boş → "Diğer".
6. **GÜVENLİK (en kritik):** Her işlem önce **Önizle (preview)**, sonra onaylı **Uygula (apply)**. Apply öncesi kaynak → `backups/<isim>-<ts>.json`. Türe-ayır/birleştir/böl orijinali silmez, hep YENİ playlist. Beğenilenler reorder edilmez (kopya playlist).
7. **Auth:** `auth.py` tek seferlik OAuth (loop ÇALIŞTIRMAZ). Scope: `playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private user-library-read user-top-read`. Redirect `http://127.0.0.1:8888/callback`.
8. **Git:** branch `loop/v1`, **PUSH YOK**. Sırlar repoya GİRMEZ.
9. **Mod:** CERRAH — gerçek API/auth YOK, her şey mock + DEMO fixture; backend pytest yeşil + `npm run build` temiz.

## 📁 Yapı (mevcut + loop ekleyecekleri)
```
spotify_organizer/
  app.py        ✅ Flask (DEMO). Loop: yeni endpoint'ler ekler.
  fixtures.py   ✅ DEMO veri (bpm/camelot/year/popularity).
  client.py     ← Protocol + spotipy impl  (loop)
  genre.py      ← kovalama/normalize        (loop)
  enrich.py     ← GetSongBPM + cache         (loop)
  order.py      ← Camelot harmonic order     (loop)
  organize.py   ← dedupe / sort / merge / split / insights  (loop)
  service.py    ← preview+apply+backup orkestrasyonu  (loop)
web/src/
  index.css     ✅ Gece Stüdyosu token'ları (KİLİTLİ)
  lib/api.js    ✅ api() + camelotColor() + fmtDuration()
  App.jsx       ✅ shell + 4 bölüm navigasyonu
  views/PlaylistsView.jsx  ✅ (butonlar placeholder → loop bağlar)
  views/ToolsView.jsx      ✅ (8 araç kartı → loop bağlar)
  views/InsightsView.jsx   ✅ (grafik iskeleti → loop gerçek veriyle)
  views/BackupsView.jsx    ✅ (restore akışı → loop)
tests/  ← mock_client + pytest (loop)
auth.py ← tek seferlik OAuth (loop yazar, çalıştırmaz)
```

## 📐 FAZLAR (her fazın BİTTİ ŞARTI var)

### F0 — İskelet + ÇALIŞAN TEMEL + TAM TASARLANMIŞ SHELL ✅ (Zenco Baba kurdu + GÖRSEL doğruladı)
- `.venv`+deps; `app.py` DEMO backend (port 5055) curl'le doğrulandı; `fixtures.py` zengin demo.
- `web/` Gece Stüdyosu paneli: 4 ekran (Playlist'ler/İçgörüler/Araçlar/Yedekler), Camelot çipleri, koyu tema. `npm run build` temiz; **4 ekran headless-chromium ile görsel doğrulandı** (loop UI'ı sıfırdan yapmaz, MANTIK doldurur).
**BİTTİ.**

### F1 — Çekirdek motor (saf Python + mock + test)
`client.py` Protocol + spotipy impl + `tests/mock_client.py` (fixtures sarar). `genre.py`, `enrich.py` (GetSongBPM, mock), `order.py` (Camelot greedy). `organize.py`: dedupe, çok-anahtarlı sort, merge, split (on-yıl/tempo/boyut), insights aggregate (tür/bpm/on-yıl/top-sanatçı/ort-pop). API formatlarını context7/WebFetch ile DOĞRULA.
**BİTTİ:** `pytest` yeşil — her işlev happy+edge (boş tür, eksik bpm, tek parça) test edilmiş.

### F2 — Backend endpoint'leri + güvenlik
`service.py` (preview/apply + backup/restore). `app.py`'ye: `/api/split-genre/(preview|apply)`, `/api/order/(preview|apply)`, `/api/dedupe/...`, `/api/sort/...`, `/api/merge|split/...`, `/api/insights/<id>`, `/api/top`, `/api/search`, `/api/backups`, `/api/restore`. DEMO fixture + gerçek client.
**BİTTİ:** backend testleri yeşil; DEMO'da tüm endpoint cevap veriyor; apply mock'ta backup yazıyor; onaysız mutasyon yok.

### F3 — Frontend bağlama (MEVCUT ekranlara — sıfırdan kurma)
- PlaylistsView: 3 buton → preview modal + apply onay.
- ToolsView: 8 kart → ilgili akış (merge/split için playlist seçici, sort için anahtar seçici, search için arama kutusu).
- InsightsView: iskelet → `/api/insights` gerçek veriyle (SVG/CSS çubuk veya recharts).
- BackupsView: `/api/backups` listesi + Geri Al.
Mevcut tasarım token/sınıfları KULLAN.
**BİTTİ:** `npm run build` temiz; DEMO'da her ekran uçtan uca çalışır (önizle→uygula görünür).

### F4 — Güvenlik + UX cilası
Apply onay diyaloğu + "geri dönüşü zor" uyarısı; her ekranda loading/empty/error; backup'tan restore; mikro-motion. Dry-run/preview varsayılan.
**BİTTİ:** apply'sız mutasyon yok; restore çalışıyor (mock); durumlar pürüzsüz.

### F5 — Doğrulama
Backend pytest tam yeşil + `npm run build` temiz + DEMO'da 4 ekran + tüm araçlar uçtan uca. (Ops: headless-chromium screenshot ile görsel kontrol — reçete `/tmp/spo-shot` deseninde.)
**BİTTİ:** her şey yeşil + DEMO panel tam işlevsel.

### F6 — Cila
README (kurulum + GetSongBPM attribution + ekran akışı) + MORNING güncel + learned-errors dolu.
**BİTTİ:** yabancı kurabilir; testler yeşil.

## 🧊 BACKLOG (Şef gerekli / loop YAPMAZ)
Gerçek OAuth (`python auth.py`), gerçek GetSongBPM key, deploy, mood/enerji boyutu, dev-mode 25-kişi aşımı.

## ✅ "Loop bitti"
F1–F6 BİTTİ; backend pytest yeşil; `npm run build` temiz; DEMO'da 8 işlev + 4 ekran uçtan uca; tasarım dili korunmuş; MORNING güncel.
