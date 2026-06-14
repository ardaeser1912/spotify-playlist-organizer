# LOOP-BRIEF — Çalışma Rayları (CERRAH modu)

> Her iterasyonda: 1) ROADMAP.md oku  2) `git log --oneline -5` + `pytest -q` ile durumu gör  3) sıradaki BİTMEMİŞ fazın en küçük anlamlı parçasını yap  4) test yeşil → küçük commit  5) `learned-errors.jsonl`'e öğrenileni yaz.

## Raylar (ihlal etme)
- **CERRAH:** kapsam = güvenli inşa. Gerçek Spotify/GetSongBPM çağrısı YOK, gerçek sır YOK, `auth.py`'yi ÇALIŞTIRMA. Her şey mock üstünde.
- **Küçük adım:** bir iterasyon = bir modül veya bir fonksiyon + testi. 200 satırlık dev commit yok.
- **Yeşil kalsın:** her commit öncesi `pytest -q` yeşil olmalı. Kırmızıysa önce onu düzelt.
- **PUSH YOK.** branch `loop/v1`. Sadece local commit.
- **Sırlara dokunma:** .env, token cache, gerçek key — asla repoya, asla log'a.
- **Kilitli kararları değiştirme** (ROADMAP §KİLİTLİ). Gerekiyorsa MORNING.md'ye "Şef'e sor" notu bırak, devam etme.
- **Varsayım yapma:** GetSongBPM / spotipy API şekillerini context7 veya WebFetch ile doğrula, uydurma.

## Fallback tablosu (takılırsan ne yap)
| Durum | Yapma | Yap |
|---|---|---|
| Gerçek auth gerekiyor | Token üretmeye çalışma | Kodu yaz, mock'la test et, MORNING.md'ye not |
| GetSongBPM key yok | Gerçek istek atma | Mock cevapla test et, gerçek çağrıyı `auth/key` arkasına koy |
| API formatı belirsiz | Tahmin etme | context7/WebFetch ile doğrula, sonra yaz |
| Bir karar Şef'lik | Kendin karar verme | MORNING.md "Şef kararı" bölümüne ekle, sıradaki faza geç |
| Test kırık + çözemiyorsun | Testi silme/atlама | `learned-errors.jsonl`'e yaz, en küçük güvenli düzeltmeyi dene |
| Faz bitti, sıradaki Şef-bağımlı | Boş döngü kurma | Backlog'dan güvenli bir iyileştirme al (test, edge-case, README) |

## Commit mesaj formatı
`F<faz>: <ne yapıldı>` — örn. `F2: genre bucket map + normalize + tests`.
Co-Authored-By satırını ekle.

## "İş bitti" sinyali
ROADMAP §"Loop bitti" sağlandıysa: son bir özet commit at, MORNING.md'yi güncelle, döngüyü durdur.
