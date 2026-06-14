# MORNING — Şef'in Elle Yapacakları ☕️

Loop kodu yazdı ve mock'la test etti. Gerçek hesapta çalıştırmak için (tek seferlik):

## 1) Spotify Developer App (~3 dk)
1. https://developer.spotify.com/dashboard → **Create app**
2. Redirect URI: `http://127.0.0.1:8888/callback` (aynen — localhost DEĞİL)
3. **Client ID** + **Client Secret**'i kopyala.

## 2) GetSongBPM key (~1 dk)
1. https://getsongbpm.com/api → ücretsiz key al.
2. Lisans şartı: README'deki attribution linki kalsın.

## 3) Sırları yapıştır
`.env.example`'ı `.env` yap, doldur:
```
SPOTIPY_CLIENT_ID=...
SPOTIPY_CLIENT_SECRET=...
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
GETSONGBPM_API_KEY=...
```

## 4) Tek seferlik giriş
```
cd ~/spotify-playlist-organizer
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python auth.py          # tarayıcı açılır, onayla → token .cache'e yazılır
```

## 5) İlk güvenli deneme (hiçbir şeye dokunmaz)
```
python -m spotify_organizer.cli list
python -m spotify_organizer.cli split-genre liked --dry-run
python -m spotify_organizer.cli order "<playlist adı>" --dry-run
```
Çıktı iyi görünürse `--apply` ekle (otomatik yedek alır).

---
## 🟡 Şef kararı bekleyenler (loop buraya yazar)
- (loop doldurur)
