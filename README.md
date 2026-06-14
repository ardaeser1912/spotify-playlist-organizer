# Spotify Playlist Organizer

Karışık playlist'leri / Beğenilenler'i düzenleyen **görsel web paneli** (koyu tema):

- **Türe göre ayır** — karışık liste → türe göre yeni playlist'ler (orijinal korunur).
- **Geçişli sırala** — harmonic mixing (Camelot çarkı) + BPM rampasıyla DJ mantığında sıralama.

Backend: Flask + spotipy. Frontend: React + Vite + Tailwind.

> Kurulum ve ilk çalıştırma için `.claude/MORNING.md`.

## Güvenlik
Her işlem önce **Önizle**, sonra onaylı **Uygula** — apply öncesi otomatik yedek alınır. Türe-ayırma orijinal listeye asla dokunmaz.

## Çalıştırma
```
# Demo (auth gerekmez):
DEMO=1 python -m spotify_organizer.app
cd web && npm install && npm run dev
```

## Veri kaynakları / atıf
BPM ve müzikal anahtar verisi **GetSongBPM** (https://getsongbpm.com) tarafından sağlanır.
