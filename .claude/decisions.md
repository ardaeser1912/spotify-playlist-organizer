# Kararlar

## 2026-06-14 — BPM/key kaynağı GetSongBPM
**Bağlam:** Geçişli sıralama BPM+key ister; Spotify Audio Features endpoint'i yeni app'lere Kasım 2024'te kapatıldı.
**Karar:** GetSongBPM (ücretsiz, attribution şartı) kullan, sonuçları cache'le.
**Alternatifler:** AcousticBrainz (donmuş, kapsama düşük), basit sezgisel (gerçek geçiş değil).
**Sonuç:** Şef GetSongBPM'i seçti.

## 2026-06-14 — Güvenlik: dry-run varsayılan
**Bağlam:** Playlist mutasyonları (sil/sırala) geri dönüşü zor.
**Karar:** Varsayılan dry-run; gerçek değişiklik `--apply` + otomatik yedek; orijinal listeye dokunma, hep yeni playlist.
**Sonuç:** Kilitli karar.
