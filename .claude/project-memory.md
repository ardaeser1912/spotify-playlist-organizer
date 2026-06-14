# Proje Hafızası — Spotify Playlist Organizer

## Ne
Şef'in karışık playlist'leri / Beğenilenler'ini düzenleyen lokal Python aracı.
1. Türe göre yeni playlist'lere ayırma. 2. Geçişli (harmonic mixing) sıralama.

## Tech stack
Python 3 · spotipy · requests · python-dotenv · pytest.

## Mimari kararlar
- BPM/key kaynağı = GetSongBPM (Spotify Audio Features Kasım 2024'te kapandı).
- Tür = sanatçı genres → ana kovalara normalize.
- Saf fonksiyonlar + Protocol client → mock'la tam test.
- Güvenlik: varsayılan dry-run; mutasyon `--apply` + otomatik yedek; orijinal liste korunur.

## Bilinen kısıtlar / tuzaklar
- Dev-mode: sadece Şef + eklediği 25 kişi authorize olabilir (kişisel kullanımda sorun değil).
- Redirect URI 127.0.0.1 olmalı (Spotify localhost'u reddediyor).
- GetSongBPM attribution linki zorunlu.
- Beğenilenler (saved tracks) API'den reorder edilemez → kopya playlist mantığı.

## Durum
İskelet + loop beyni kuruldu (Zenco Baba). Kod loop'ta yazılacak (CERRAH modu).
