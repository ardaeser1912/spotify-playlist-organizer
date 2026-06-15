"""Tür önbelleğini ısıt — Beğenilenler'deki sanatçıların türünü MusicBrainz'den
(ücretsiz, anahtarsız) `cache/genres.json`'a çeker. Bir kez çalıştır; sonra panel
"Türe Göre Ayır" + tür dağılımı bu önbellekten ANINDA okur.

Spotify dev-mode `/artists`'ı 403 verdiği için tür buradan gelir. MusicBrainz ~1 istek/sn
ister (User-Agent'lı, iTunes gibi bloklamaz). Çalıştır:
    python prewarm_genres.py
"""
import os
import time
from collections import Counter

from dotenv import load_dotenv

from spotify_organizer import genre_source
from spotify_organizer.client import REDIRECT_URI, SCOPES, SpotipyClient

CACHE = "cache/genres.json"


def main():
    load_dotenv()
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=SCOPES, redirect_uri=os.environ.get("SPOTIPY_REDIRECT_URI", REDIRECT_URI),
        cache_path=".spotify_cache", open_browser=False))
    c = SpotipyClient(sp)
    names = {t["artist"] for t in c.liked_tracks() if t.get("artist")}
    print(f"{len(names)} benzersiz sanatçı — iTunes'tan tür çekiliyor (nazik tempo)...", flush=True)
    os.makedirs("cache", exist_ok=True)
    cache = genre_source.load_cache(CACHE)
    done = 0

    def paced(name, http_get=None):
        nonlocal done
        time.sleep(1.1)  # MusicBrainz ~1 istek/sn ister (User-Agent'lı, bloklamaz)
        g = genre_source.fetch_musicbrainz_genre(name)
        done += 1
        if done % 25 == 0:
            genre_source.save_cache(CACHE, cache)
            print(f"  {done}/{len(names)} işlendi (checkpoint)...", flush=True)
        return g

    res = genre_source.buckets_for_artists(names, cache, fetch=paced)
    genre_source.save_cache(CACHE, cache)
    print("✅ Tür dağılımı:", dict(Counter(res.values())), flush=True)
    print(f"cache/genres.json güncel — {len(cache)} sanatçı önbellekte.", flush=True)


if __name__ == "__main__":
    main()
