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
## 🟡 Şef kararı bekleyenler (loop buraya yazar)
- (loop doldurur)
