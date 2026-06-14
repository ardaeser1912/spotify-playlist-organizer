# Spotify Playlist Organizer

Karışık playlist'leri / Beğenilenler'i düzenleyen lokal araç:

- **Türe göre ayır** — karışık liste → türe göre yeni playlist'ler (orijinal korunur).
- **Geçişli sırala** — harmonic mixing (Camelot çarkı) + BPM rampasıyla DJ mantığında sıralama.

> Kurulum ve ilk çalıştırma için `.claude/MORNING.md`.

## Güvenlik
Her komut varsayılan **dry-run**. Gerçek değişiklik sadece `--apply` ile ve önce otomatik yedek alınır. Türe-ayırma orijinal listeye asla dokunmaz.

## Kullanım
```
python -m spotify_organizer.cli list
python -m spotify_organizer.cli split-genre liked --dry-run
python -m spotify_organizer.cli order "Playlist Adı" --dry-run
```

## Veri kaynakları / atıf
BPM ve müzikal anahtar verisi **GetSongBPM** (https://getsongbpm.com) tarafından sağlanır.
