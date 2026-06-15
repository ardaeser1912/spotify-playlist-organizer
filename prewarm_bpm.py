"""BPM/Camelot önbelleğini ısıt — Beğenilenler'in tempo + Camelot'unu GetSongBPM'den
(api.getsong.co) `cache/bpm.json`'a çeker. Sonra panel DJ geçişlerini bu önbellekten
ANINDA okur (istek-yolunda GetSongBPM çağrısı YOK).

GetSongBPM ücretsiz, attribution şart (README'de var). Spotify rate-limiti aktifken
liked_tracks çekilemez → bu betiği Spotify limiti kalkınca çalıştır. Çalıştır:
    python prewarm_bpm.py

Powered by GetSongBPM (https://getsongbpm.com)
"""
import os
import time

from dotenv import load_dotenv

from spotify_organizer import enrich
from spotify_organizer.client import REDIRECT_URI, SCOPES, SpotipyClient

CACHE = "cache/bpm.json"


def main():
    load_dotenv()
    key = os.environ.get("GETSONGBPM_API_KEY", "")
    if not key:
        raise SystemExit("GETSONGBPM_API_KEY .env'de yok — önce GetSongBPM key'i al.")
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=SCOPES, redirect_uri=os.environ.get("SPOTIPY_REDIRECT_URI", REDIRECT_URI),
        cache_path=".spotify_cache", open_browser=False),
        retries=0, status_retries=0, requests_timeout=20)
    tracks = SpotipyClient(sp).liked_tracks()
    print(f"{len(tracks)} parça — GetSongBPM'den BPM/Camelot çekiliyor (nazik tempo)...", flush=True)
    os.makedirs("cache", exist_ok=True)
    cache = enrich.load_cache(CACHE)
    fetch = enrich.build_getsongbpm_fetch(key)
    found = done = 0
    for t in tracks:
        k = enrich._cache_key(t.get("title", ""), t.get("artist", ""))
        if k in cache:
            done += 1
            continue
        data = fetch(t.get("title", ""), t.get("artist", ""))
        cache[k] = data
        found += 1 if data else 0
        done += 1
        if done % 25 == 0:
            enrich.save_cache(CACHE, cache)
            print(f"  {done}/{len(tracks)} | bulunan: {found}", flush=True)
        time.sleep(1.2)  # GetSongBPM'e nazik
    enrich.save_cache(CACHE, cache)
    print(f"✅ {found} parça BPM/Camelot bulundu. cache/bpm.json güncel — DJ geçişleri hazır.", flush=True)


if __name__ == "__main__":
    main()
