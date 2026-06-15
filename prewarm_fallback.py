"""MusicBrainz sonrası 'Diğer' kapsamını iTunes ile yükselt.

MusicBrainz Türkçe/yerel sanatçıları zayıf etiketler (Ceza/Sagopa → sadece "turkish"
→ Diğer). iTunes bunları daha iyi bilir (Ceza → "Turkish Hip-Hop/Rap"). Bu betik
cache/genres.json'da Diğer/boş kalan sanatçıları iTunes'tan yeniden dener; iTunes
gerçek bir kova verirse cache'i günceller. Throttle'a karşı nazik tempo + backoff.

Çalıştır (prewarm_genres.py'den SONRA):  python prewarm_fallback.py
"""
import random
import time

from spotify_organizer import genre_source

CACHE = "cache/genres.json"


def main():
    cache = genre_source.load_cache(CACHE)
    targets = [k for k, v in cache.items()
               if v is None or genre_source.itunes_to_bucket(v) == genre_source.OTHER]
    print(f"{len(targets)} 'Diğer'/boş sanatçı iTunes ile yeniden deneniyor...", flush=True)
    fixed = miss = done = 0
    for name in targets:
        g = genre_source.fetch_itunes_genre(name)
        done += 1
        if g and genre_source.itunes_to_bucket(g) != genre_source.OTHER:
            cache[name] = g
            fixed += 1
            miss = 0
        else:
            miss += 1
        if miss >= 10:  # throttle şüphesi → soğut
            print("  throttle? 30sn bekleniyor...", flush=True)
            time.sleep(30)
            miss = 0
        time.sleep(1.8 + random.uniform(0, 0.4))  # iTunes'a nazik
        if done % 25 == 0:
            genre_source.save_cache(CACHE, cache)
            print(f"  {done}/{len(targets)} | düzeltilen: {fixed}", flush=True)
    genre_source.save_cache(CACHE, cache)
    print(f"✅ {fixed} sanatçı Diğer'den gerçek türe taşındı. cache güncel.", flush=True)


if __name__ == "__main__":
    main()
