# ROADMAP — Spotify Playlist Organizer (WEB APP)

> Loop'un beyni. Her iterasyonda önce bunu oku. Kilitli kararlara dokunma.

## 🎯 Amaç
Spotify tarzı **görsel web paneli** — Şef playlist'lerini görür, butonla düzenler:
1. **Türe göre ayırma** — karışık liste / Beğenilenler → türe göre YENİ playlist'ler (orijinal dokunulmaz).
2. **Geçişli sıralama** — bir playlist'i harmonic mixing (Camelot çarkı) + BPM rampası ile DJ mantığında sırala.
UI: sol playlist listesi · sağ şarkı listesi + "Türe Ayır" / "Geçişli Sırala" butonları · Önizle → Uygula.

## 🔒 KİLİTLİ KARARLAR (değiştirme = Şef onayı)
1. **Stack:**
   - **Backend:** Python + Flask (`app.py`) + spotipy + requests. Çekirdek mantık saf modüllerde.
   - **Frontend:** React + Vite + Tailwind, **koyu tema** (360SMM "Aydınlık Derinlik" hissi). `web/` klasörü.
2. **DEMO modu (kritik):** `DEMO=1` ile backend, fixture playlist'ler döndürür → **auth OLMADAN** panel tam çalışır. Sabah Şef açar, demo veriyle tıklar, türe-ayır + geçişli-sıra çalışır görür. Gerçek veri auth'tan sonra.
3. **BPM/key kaynağı:** **GetSongBPM** (Şef onayladı). Spotify Audio Features Kasım 2024 kapandı, kullanma. Sonuç `cache/bpm.json`'a cache. README'de attribution ZORUNLU.
4. **Tür kaynağı:** Sanatçı `genres` → ana kovalara normalize. Boş → "Diğer".
5. **GÜVENLİK (en kritik):**
   - Her işlem **önce ÖNİZLE (preview)**, sonra ayrı **Uygula (apply)** — apply'da onay diyaloğu.
   - Apply öncesi kaynak listeyi `backups/<isim>-<ts>.json`'a yedekle.
   - Türe-ayırma orijinali ASLA silmez; hep YENİ playlist.
   - Beğenilenler reorder edilmez; okunup yeni playlist'lere kopyalanır.
6. **Auth:** `auth.py` tek seferlik OAuth (loop ÇALIŞTIRMAZ, yazar). Scope: `playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private user-library-read`. Redirect `http://127.0.0.1:8888/callback` (localhost değil).
7. **Mimari:** Çekirdek saf fonksiyonlar (genre/order/enrich) + Protocol client → mock'la %100 test. Flask sadece ince kabuk.
8. **Git:** branch `loop/v1`, **PUSH YOK**. Sırlar repoya GİRMEZ.
9. **Mod:** CERRAH — gerçek API/auth YOK, her şey mock + DEMO fixture üstünde; backend pytest yeşil, frontend `npm run build` başarılı.

## 📁 Yapı
```
spotify_organizer/
  client.py    # SpotifyClientProtocol + spotipy impl
  fixtures.py  # DEMO veri (sahte playlist/şarkı/sanatçı)
  genre.py     # tür kovalama + normalize
  enrich.py    # GetSongBPM + cache
  order.py     # Camelot harmonic order
  service.py   # split_genre / order_playlist → preview + apply
  app.py       # Flask API (+ build edilmiş frontend'i serve)
web/           # React + Vite + Tailwind (koyu tema)
tests/         # mock_client + pytest
auth.py
```

## 📐 FAZLAR (her fazın BİTTİ ŞARTI var)

### F0 — İskelet ✅ (kuruldu)
requirements/.gitignore/.env.example/README/.claude hazır. **BİTTİ.**

### F1 — Çekirdek motor (saf Python)
client Protocol + `tests/mock_client.py` + `fixtures.py` (DEMO) + `genre.py` (kovala/normalize) + `enrich.py` (GetSongBPM client + cache + mock) + `order.py` (Camelot çark + greedy harmonic sıra). GetSongBPM/spotipy formatını context7/WebFetch ile doğrula.
**BİTTİ:** `pytest` yeşil — kovalama, enrich cache hit/miss, harmonic sıra (eksik-veri dahil) test edilmiş.

### F2 — Flask backend
`service.py` (split_genre/order_playlist → preview+apply, backup) + `app.py` endpoint'leri:
`GET /api/me`, `GET /api/playlists`, `GET /api/playlist/<id>`, `POST /api/split-genre/preview|apply`, `POST /api/order/preview|apply`. DEMO modu fixture döndürür. Gerçek modda spotipy.
**BİTTİ:** backend testleri yeşil; DEMO=1 ile tüm endpoint'ler fixture cevabı veriyor; apply mock'ta doğru çağrı + backup yazıyor.

### F3 — Frontend (React panel, koyu tema)
Vite+Tailwind kur. Sol: playlist listesi. Sağ: seçili playlist şarkıları + "Türe Göre Ayır" / "Geçişli Sırala" butonları. Önizleme paneli (kovalar / yeni sıra) → "Uygula" onay diyaloğu. Loading/empty/error state'leri. `/api`'ye bağlan.
**BİTTİ:** `npm run build` başarılı; DEMO backend'le panel uçtan uca çalışıyor (önizle→uygula akışı demo veride görünür).

### F4 — Güvenlik + apply cilası
Apply onay diyaloğu, backup, "geri dönüşü zor" uyarısı; dry-run/preview varsayılan akış; hata mesajları kullanıcı-dostu.
**BİTTİ:** apply'sız hiçbir mutasyon olmaz; onaysız apply yok; backup test edilmiş.

### F5 — Doğrulama
Backend pytest tam yeşil + frontend build temiz + DEMO uçtan uca. (Opsiyonel: panel screenshot recipe ile görsel kontrol.)
**BİTTİ:** her şey yeşil + DEMO panel açılıp çalışıyor.

### F6 — Cila
README (kurulum + GetSongBPM attribution + ekran akışı) + MORNING güncel + learned-errors dolu.
**BİTTİ:** yabancı kurabilir netlikte; testler yeşil.

## 🧊 BACKLOG (Şef gerekli / loop YAPMAZ)
- Gerçek OAuth (`python auth.py`) — tarayıcı, sadece Şef.
- GetSongBPM gerçek key — Şef alır.
- Deploy (şimdilik lokal çalışır).
- Mood/enerji boyutu (GetSongBPM yetmezse).
- Dev-mode 25-kişi sınırını aşma.

## ✅ "Loop bitti"
F1–F6 BİTTİ; backend pytest yeşil; frontend build temiz; DEMO panel uçtan uca çalışıyor; MORNING güncel; gerçek-auth gerektiren her şey Backlog'da.
