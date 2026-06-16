"""BPM/Camelot önbelleğini ısıt — "bütün şarkıları bilen" hibrit (Deezer + ses analizi).

Her Beğenilenler parçası için audio_bpm.get_bpm_camelot:
  Deezer BPM doluysa o, yoksa 30sn önizleme sesini librosa ile analiz → gerçek BPM + Camelot.
Veritabanı kapsamına bağımlı DEĞİL → niş elektronik/rap dahil ~tüm şarkıların BPM'i çıkar.

`cache/bpm.json`'a yazar (panel oradan okur). Paralel (hızlı). Çalıştır:
    python prewarm_bpm.py
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from spotify_organizer import audio_bpm, enrich
from spotify_organizer.client import REDIRECT_URI, SCOPES, SpotipyClient

CACHE = "cache/bpm.json"
WORKERS = 6


def main():
    load_dotenv()
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=SCOPES, redirect_uri=os.environ.get("SPOTIPY_REDIRECT_URI", REDIRECT_URI),
        cache_path=".spotify_cache", open_browser=False),
        retries=0, status_retries=0, requests_timeout=20)
    tracks = SpotipyClient(sp).liked_tracks()
    os.makedirs("cache", exist_ok=True)
    cache = enrich.load_cache(CACHE)
    todo = [(t, enrich._cache_key(t.get("title", ""), t.get("artist", "")))
            for t in tracks]
    todo = [(t, k) for t, k in todo if k not in cache]
    print(f"{len(todo)}/{len(tracks)} parça işlenecek (Deezer + ses analizi, {WORKERS} paralel)...", flush=True)
    done = found = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(audio_bpm.get_bpm_camelot, t.get("title", ""), t.get("artist", "")): k
                for t, k in todo}
        for fut in as_completed(futs):
            data = None
            try:
                data = fut.result()
            except Exception:
                data = None
            cache[futs[fut]] = data
            done += 1
            if data and (data.get("bpm") or data.get("camelot")):
                found += 1
            if done % 30 == 0:
                enrich.save_cache(CACHE, cache)
                print(f"  {done}/{len(todo)} | bulunan: {found}", flush=True)
    enrich.save_cache(CACHE, cache)
    print(f"✅ {found}/{len(todo)} parça BPM/Camelot bulundu. cache/bpm.json güncel — DJ geçişleri hazır.", flush=True)


if __name__ == "__main__":
    main()
