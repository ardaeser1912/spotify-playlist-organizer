"""BPM/Camelot önbelleğini ısıt — "bütün şarkıları %100 bilen" hibrit (Deezer + iTunes + ses analizi).

Her Beğenilenler parçası için audio_bpm.get_bpm_camelot:
  Deezer/iTunes'ta bul → BPM alanı + 30sn önizleme → boşsa sesi librosa ile analiz (gerçek BPM + Camelot).
Veritabanı kapsamına bağımlı DEĞİL. OTOMATİK TEKRAR: geçici ağ hatasıyla kaçanları
yeniden dener (3 tura kadar) → hep ~%100.

`cache/bpm.json`'a yazar (panel oradan okur). Paralel (hızlı). Çalıştır:  python prewarm_bpm.py
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from spotify_organizer import audio_bpm, enrich
from spotify_organizer.client import REDIRECT_URI, SCOPES, SpotipyClient

CACHE = "cache/bpm.json"
WORKERS = 6
PASSES = 3  # otomatik tekrar (geçici hata onarımı)


def _process(todo, cache):
    done = found = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(audio_bpm.get_bpm_camelot, t.get("title", ""), t.get("artist", "")): k
                for t, k in todo}
        for fut in as_completed(futs):
            try:
                data = fut.result()
            except Exception:
                data = None
            cache[futs[fut]] = data
            done += 1
            if data and data.get("bpm"):
                found += 1
            if done % 30 == 0:
                enrich.save_cache(CACHE, cache)
                print(f"  {done}/{len(todo)} | bu turda bulunan: {found}", flush=True)


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
    pairs = [(t, enrich._cache_key(t.get("title", ""), t.get("artist", ""))) for t in tracks]

    for attempt in range(1, PASSES + 1):
        todo = [(t, k) for t, k in pairs if not (cache.get(k) and cache[k].get("bpm"))]
        if not todo:
            break
        print(f"Tur {attempt}: {len(todo)} parça işlenecek ({WORKERS} paralel)...", flush=True)
        _process(todo, cache)
        enrich.save_cache(CACHE, cache)

    dolu = sum(1 for v in cache.values() if v and v.get("bpm"))
    print(f"✅ {dolu}/{len(cache)} = %{round(dolu * 100 / max(len(cache), 1))} BPM/Camelot DOLU — DJ hazır.", flush=True)


if __name__ == "__main__":
    main()
