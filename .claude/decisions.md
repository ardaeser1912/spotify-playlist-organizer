# Kararlar

## 2026-06-14 — BPM/key kaynağı GetSongBPM
**Bağlam:** Geçişli sıralama BPM+key ister; Spotify Audio Features endpoint'i yeni app'lere Kasım 2024'te kapatıldı.
**Karar:** GetSongBPM (ücretsiz, attribution şartı) kullan, sonuçları cache'le.
**Alternatifler:** AcousticBrainz (donmuş, kapsama düşük), basit sezgisel (gerçek geçiş değil).
**Sonuç:** Şef GetSongBPM'i seçti.

## 2026-06-14 — Görsel web uygulaması (CLI değil)
**Bağlam:** Şef "Spotify tarzı uygulama görmek istiyorum" dedi; CLI yeterli değil.
**Karar:** Flask backend + React/Vite/Tailwind koyu tema panel. DEMO modu ile auth olmadan açılıp çalışır.
**Alternatifler:** CLI (hızlı ama görsel yok), no-build tek-sayfa (sağlam ama Şef'in React zevkine uzak).
**Sonuç:** Şef web app'i seçti. Çekirdek mantık değişmedi, üstüne UI eklendi.

## 2026-06-14 — Güvenlik: dry-run varsayılan
**Bağlam:** Playlist mutasyonları (sil/sırala) geri dönüşü zor.
**Karar:** Varsayılan dry-run; gerçek değişiklik `--apply` + otomatik yedek; orijinal listeye dokunma, hep yeni playlist.
**Sonuç:** Kilitli karar.
