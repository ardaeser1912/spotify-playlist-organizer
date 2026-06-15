# Spotify Extended Quota Başvurusu (yazma iznini açmak için)

## Neden gerekli?
Spotify, **Development-mode** uygulamaların playlist **OLUŞTURMA / DEĞİŞTİRME** (yazma)
işlemlerini engelliyor → "Uygula" 403 veriyor (kendi hesabına bile, izinler doğru olsa da).
Bu, panelin türe-ayır/akıllı-mix sonucunu **doğrudan Spotify'a yazabilmesi** için kaldırılmalı.

> Şu an alternatif çalışıyor: panel sonucu **"Dışa Aktar (CSV)"** ile veriyor; ücretsiz bir
> içe-aktarma aracıyla ya da elle Spotify'a koyabilirsin. Extended quota onaylanırsa "Uygula"
> doğrudan yazar.

## Nasıl başvurulur
1. https://developer.spotify.com/dashboard → uygulamana ("Playlist Organizer") gir.
2. **Settings** → en altta **"Extended Quota Mode"** / **"Request Extension"** bölümünü ara
   (Spotify zaman zaman akışı değiştiriyor; yoksa Documentation → "Quota modes" sayfasındaki
   başvuru formu linkini kullan).
3. Formu aşağıdaki taslakla doldur.

## Form taslağı (kopyala-yapıştır)
**App name:** Playlist Organizer

**What does your app do? (açıklama):**
> Kişisel bir araç. Kullanıcının kendi Spotify kütüphanesini (Beğenilenler + playlist'ler)
> analiz edip türe göre ayıran, "akıllı mix" ile akıcı sıraya dizen, tekrarları temizleyen,
> çok-anahtarlı sıralayan ve her işlemden önce otomatik yedek alan bir web paneli. Tür verisi
> ücretsiz açık kaynaklardan (MusicBrainz/iTunes) zenginleştirilir. Yazma işlemleri yalnızca
> kullanıcının KENDİ onayıyla ve önizleme sonrası yapılır.

**Commercial or non-commercial?:** Non-commercial (kişisel kullanım)

**Which endpoints / why:**
> playlist-read-private, user-library-read, user-top-read (okuma/analiz);
> playlist-modify-public/private (düzenlenmiş playlist'leri kullanıcının onayıyla oluşturmak).

**Expected number of users:** 1 (kişisel) — yalnız uygulama sahibi.

**Platform:** Web (yerel, localhost).

## Dürüst beklenti
Spotify 2025 "Platform Security" değişikliğinden sonra **kişisel/non-commercial** araçlara
extended quota nadiren veriliyor; ticari kullanım + iş/kimlik doğrulaması + belirli kullanıcı
sayısı isteyebilir. Onay gelmezse panel **Dışa Aktar** moduyla tam değerli kalır.

## Onay gelirse (kod hazır)
Kodda hiçbir değişiklik gerekmez — `OrganizerService` zaten `client.create_playlist` /
`replace_tracks` çağırıyor; quota açılınca 403 kaybolur, "Uygula" doğrudan yazar. Sadece
`python auth.py` ile token'ı bir kez tazele.
