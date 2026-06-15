# Spotify Playlist Organizer 🎧

Karışık playlist'leri / Beğenilenler'i düzenleyen **görsel, çok işlevli web paneli** —
"Gece Stüdyosu" koyu teması. Backend: Python + Flask + spotipy. Frontend: React + Vite + Tailwind.
Çekirdek mantık saf Python modüllerinde (test edilebilir, API'den bağımsız).

## ✨ İşlevler
1. **Türe Göre Ayır** — karışık listeyi türe göre yeni playlist'lere böl (orijinal korunur).
2. **Geçişli Sırala · DJ** — harmonic mixing (Camelot çarkı) + BPM rampasıyla akıcı geçiş.
3. **Tekrarları Temizle** — aynı parçanın kopyalarını bul & kaldır.
4. **Çok-Anahtarlı Sırala** — popülerlik · yıl · BPM · süre · sanatçı · başlık.
5. **Birleştir** — birden çok playlist'i tek listede topla (tekrarsız).
6. **Böl** — büyük listeyi on-yıla / tempo bölgesine / boyuta göre ayır.
7. **İçgörüler** — tür / BPM / on-yıl dağılımı + en çok sanatçılar + ortalama popülerlik.
8. **Keşif** — top şarkılardan ya da katalog aramasından tek tıkla playlist.

## 🔒 Güvenlik (en kritik)
Her işlem önce **Önizle**, sonra onaylı **Uygula** — apply öncesi kaynak otomatik
`backups/<isim>-<ts>.json`'a yedeklenir. Türe-ayır / birleştir / böl orijinali asla silmez
(hep YENİ playlist). **Beğenilenler reorder edilmez** — kopya playlist üretilir. Her yedek
**Yedekler** ekranından tek tıkla geri yüklenir.

## 🖥️ Ekran akışı
Panel dört ekrandan oluşur (sol kenar çubuğundan geçilir):

- **Playlist'ler** — kitaplıktan bir liste seç → parçalar listelenir (Camelot çipi + BPM +
  süre). Üstte 3 hızlı aksiyon: **Türe Ayır · Geçişli Sırala · Tekrar Temizle** — her biri
  Önizle→Uygula modalını açar.
- **Araçlar** — 8 aracın tek vitrini. Bir karta tıkla → konfig paneli açılır (kaynak liste /
  sıralama alanı / bölme ölçütü gibi seçimler) → **Önizle**'ye bas → modal'da onayla.
- **İçgörüler** — bir kaynak seç → tür / BPM / on-yıl dağılımı, en çok dinlenen sanatçılar ve
  ortalama popülerlik gösterilir.
- **Yedekler** — her "Uygula" öncesi alınan yedekler listelenir → tek tıkla **Geri Al**.

**Önizle→Uygula modalı:** her mutasyon önce önizlenir; "uygulama geri dönüşü zordur" uyarısı +
otomatik yedek hatırlatması gösterilir. Esc veya ✕ ile kapanır (odak yönetimli, erişilebilir).

## ▶️ Çalıştırma (DEMO — auth gerekmez)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DEMO=1 python -m spotify_organizer.app        # backend (port 5055)
cd web && npm install && npm run dev          # panel (port 5173)
```
DEMO modu fixture veriyle uçtan uca çalışır — hiçbir gerçek şeye dokunmaz.

## 🔑 Gerçek hesaba bağlama (tek seferlik)
Adımlar `.claude/MORNING.md`'de. Özet: `.env` doldur → `python auth.py` (tarayıcıda onayla)
→ `python -m spotify_organizer.app` (DEMO=1 olmadan).

## 🧪 Test
```bash
.venv/bin/python -m pytest -q     # çekirdek + servis + endpoint testleri
```

## 📊 Veri kaynakları / atıf
BPM ve müzikal anahtar verisi **GetSongBPM** (https://getsongbpm.com) tarafından sağlanır.
(Spotify Audio Features uçları Kasım 2024'te kapandı.) Tür verisi Spotify sanatçı `genres`
alanından ana kovalara normalize edilir.

## 🗂 Mimari
```
spotify_organizer/
  client.py    SpotifyClient sözleşmesi (Protocol) + spotipy implementasyonu
  demo_client.py  fixtures üstü DEMO istemcisi (auth'suz)
  fixtures.py  zengin DEMO verisi
  genre.py     tür kovalama/normalize
  order.py     Camelot harmonic sıralama
  enrich.py    GetSongBPM ile bpm/camelot doldurma + cache
  organize.py  dedupe / sort / merge / split / insights
  service.py   önizle + uygula + backup/restore orkestrasyonu
  app.py       Flask endpoint'leri ({success,data,error} zarfı)
web/src/       React paneli (App + 4 ekran + PreviewModal)
auth.py        tek seferlik OAuth (Şef çalıştırır)
```
