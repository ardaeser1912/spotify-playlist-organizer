# ROADMAP — Spotify Playlist Organizer

> Loop'un beyni. Her iterasyonda önce bunu oku. Kilitli kararlara dokunma.

## 🎯 Amaç
Şef'in karışık playlist'lerini / Beğenilenler'ini düzenleyen bir lokal araç:
1. **Türe göre ayırma** — karışık liste → türe göre YENİ playlist'ler (orijinal dokunulmaz).
2. **Geçişli sıralama** — bir playlist'i harmonic mixing (Camelot çarkı) + BPM rampası ile DJ mantığında sırala.

## 🔒 KİLİTLİ KARARLAR (değiştirme — değişiklik = Şef onayı)
1. **Stack:** Python 3 + `spotipy` (Spotify) + `requests` (GetSongBPM) + `python-dotenv` + `pytest`.
2. **BPM/key kaynağı:** **GetSongBPM** (Şef onayladı). Spotify Audio Features Kasım 2024'te kapatıldı, kullanma. GetSongBPM sonuçlarını `cache/bpm.json`'a cache'le. README'de attribution linki ZORUNLU (lisans şartı).
3. **Tür kaynağı:** Sanatçı `genres` dizisi (Get Artist). Mikro-türleri ana kovalara normalize et. Türü boş → "Diğer".
4. **GÜVENLİK (en kritik):**
   - Her komut **varsayılan `--dry-run`**. Gerçek değişiklik SADECE `--apply` ile.
   - `--apply` öncesi kaynak listeyi `backups/<isim>-<ts>.json`'a yedekle.
   - Türe-ayırma orijinali ASLA silmez/değiştirmez, hep YENİ playlist üretir.
   - Beğenilenler (saved tracks) reorder edilmez; sadece okunup yeni playlist'lere kopyalanır.
5. **Auth:** `auth.py` tek seferlik OAuth (loop bunu ÇALIŞTIRMAZ, sadece yazar). Scope: `playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private user-library-read`. Redirect: `http://127.0.0.1:8888/callback` (localhost değil — Spotify loopback zorunlu).
6. **Mimari:** Saf fonksiyonlar (genre.py / order.py / enrich.py) + Protocol arayüzlü client → mock'la %100 test edilebilir.
7. **Git:** branch `loop/v1`, **PUSH YOK**. Sırlar repoya GİRMEZ (.env, .cache .gitignore'da).
8. **Mod:** CERRAH — sadece güvenli inşa. Gerçek API çağrısı yok, gerçek sır yok, her şey mock üstünde yeşil.

## 📐 FAZLAR (sırayla; her fazın "BİTTİ ŞARTI" var)

### F0 — İskelet  ✅ (Zenco Baba kurdu)
requirements.txt · .gitignore · .env.example · README stub · .claude/* hazır.
**BİTTİ:** dosyalar var, `git status` temiz başlangıç.

### F1 — Client soyutlaması + mock + auth
- `client.py`: `SpotifyClientProtocol` (methodlar: `current_user_playlists`, `playlist_items`, `liked_songs`, `artists`, `create_playlist`, `add_items`, `replace_items`). Gerçek impl spotipy sarar.
- `tests/mock_client.py`: bellekte sahte Spotify (sabit fixture şarkılar + sanatçılar).
- `auth.py`: spotipy SpotifyOAuth tek-seferlik akış.
**BİTTİ:** mock client import edilir, protocol'e uyar; `pytest` F1 testleri yeşil.

### F2 — Tür kovalama (`genre.py`)
- Mikro-tür → ana kova haritası (Pop / Rock / Rap-Hiphop / Elektronik / Türkçe / Arabesk / Jazz-Soul / Klasik / Diğer). Genişletilebilir dict.
- `bucket_tracks(tracks, artist_genres) -> dict[bucket, list[track]]`. Boş tür → "Diğer".
**BİTTİ:** karışık fixture doğru kovalara ayrılıyor; edge (boş tür, çok-türlü sanatçı) test edilmiş.

### F3 — Zenginleştirme (`enrich.py`)
- GetSongBPM client: `get_bpm_key(artist, title) -> {bpm, key, camelot}`. Cache (`cache/bpm.json`), rate-limit nazik (jitter), bulunamayan → None.
- Spotify key/mode YOKsa GetSongBPM'in key'ini Camelot'a çevir.
- Build sırasında GetSongBPM API formatını context7/WebFetch ile DOĞRULA (varsayım yapma).
**BİTTİ:** mock GetSongBPM ile enrich testleri yeşil; cache hit/miss test edilmiş; eşleşmeyen şarkı sayısı loglanıyor.

### F4 — Geçişli sıralama (`order.py`)
- Camelot çarkı haritası (key+mode → "8A/8B" vb.).
- `harmonic_order(enriched_tracks) -> ordered list`: greedy nearest-neighbor; komşu maliyeti = key uyumsuzluğu (Camelot ±1/relative ucuz) + |ΔBPM| normalize. BPM kademeli ramp. BPM/key'i olmayanlar sona, kendi arasında stabil.
**BİTTİ:** bilinen küçük sette beklenen sıra; tüm-veri-eksik durumda çökmez; testler yeşil.

### F5 — Servis + CLI (`organize.py`, `cli.py`)
- `split_genre(source) -> plan/apply`: oku → kovala → her kova için yeni playlist + ekle (batch 100).
- `order_playlist(pid) -> plan/apply`: oku → enrich → harmonic_order → replace_items (batch 100).
- `cli.py`: `list`, `split-genre <kaynak|liked>`, `order <playlist>`; `--dry-run` (vars.), `--apply`, `--backup` (apply'da otomatik).
- dry-run: ne yapılacağını okunur tabloyla yazdır, hiçbir şeye dokunma.
**BİTTİ:** CLI mock client ile uçtan uca çalışır; dry-run hiçbir mutasyon yapmaz; apply mock'ta doğru çağrıları yapar.

### F6 — Cila
README (kurulum + GetSongBPM attribution + örnekler) · MORNING.md güncel · `learned-errors.jsonl` doldu · tüm testler yeşil.
**BİTTİ:** `pytest` tamamen yeşil; README bir yabancının kurabileceği kadar net.

## 🧊 BACKLOG (Şef gerekli / loop YAPMAZ)
- Gerçek OAuth (`python auth.py`) — tarayıcı onayı, sadece Şef.
- GetSongBPM gerçek API key — Şef alır.
- "Mood/enerji" boyutu — GetSongBPM yeterli alan vermezse Backlog.
- Dev-mode 25-kişi sınırını aşma (quota extension) — sadece dağıtım gerekirse.
- Beğenilenler reorder (API saved-tracks sırasını değiştirmez) — gerekirse "Beğenilenler kopyası" playlist'i.

## ✅ TANIM: "Loop bitti"
F1–F6 BİTTİ şartları sağlandı, `pytest` yeşil, çalışma ağacı tutarlı, MORNING.md güncel. Gerçek-auth gerektiren her şey Backlog'da ve MORNING.md'de.
