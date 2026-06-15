"""BPM/Camelot zenginleştirme — eksik bpm/camelot alanlarını doldurur.

Spotify Audio Features (BPM/key) Kasım 2024'te kapandı; BPM/key kaynağı artık
GetSongBPM. Bu modül saf mantık + opsiyonel fetcher; testlerde GERÇEK ağ YOK.

Powered by GetSongBPM (https://getsongbpm.com)

Track şekli fixtures.py/client.py ile birebir aynı:
    {id, title, artist, artist_id, uri, duration_ms, bpm, camelot, year, popularity}
"""
from __future__ import annotations

import json
import os


def _cache_key(title: str, artist: str) -> str:
    return f"{title}|{artist}".lower()


def enrich_tracks(tracks: list[dict], fetch=None, cache: dict | None = None) -> list[dict]:
    """Eksik bpm/camelot olan track'leri (kopya üzerinde) doldurur.

    - Girişi MUTASYONA UĞRATMAZ; her track'in kopyasını döndürür, uzunluk korunur.
    - bpm veya camelot None ise: önce cache (anahtar `f"{title}|{artist}".lower()`),
      yoksa `fetch(title, artist)`. fetch None ise track olduğu gibi kalır.
    - fetch/cache dönüşü {"bpm": int, "camelot": str} veya None.
    """
    if cache is None:
        cache = {}
    out: list[dict] = []
    for track in tracks:
        copy = dict(track)
        if copy.get("bpm") is None or copy.get("camelot") is None:
            key = _cache_key(copy.get("title", ""), copy.get("artist", ""))
            if key in cache:
                data = cache[key]
            elif fetch is not None:
                data = fetch(copy.get("title", ""), copy.get("artist", ""))
                cache[key] = data
            else:
                data = None
            if data:
                if copy.get("bpm") is None and data.get("bpm") is not None:
                    copy["bpm"] = data["bpm"]
                if copy.get("camelot") is None and data.get("camelot") is not None:
                    copy["camelot"] = data["camelot"]
        out.append(copy)
    return out


def load_cache(path) -> dict:
    """JSON cache dosyasını okur. Dosya yoksa boş dict döner."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(path, cache: dict) -> None:
    """Cache'i JSON olarak yazar. Gereken dizini oluşturur."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def open_key_to_camelot(open_key: str) -> str | None:
    """GetSongBPM open_key ("1d"/"1m") → Camelot ("8B"/"5A").

    open_key: sayı + harf (d=major, m=minor). Camelot'ta B=major, A=minor.
    OpenKey 1d (C major) = Camelot 8B referans alınır:
        camelot_no = ((open_key_no + 6) % 12) + 1
    """
    if not open_key or len(open_key) < 2:
        return None
    letter = open_key[-1].lower()
    num_part = open_key[:-1]
    if not num_part.isdigit() or letter not in ("d", "m"):
        return None
    n = int(num_part)
    if not 1 <= n <= 12:
        return None
    camelot_no = ((n + 6) % 12) + 1
    suffix = "B" if letter == "d" else "A"
    return f"{camelot_no}{suffix}"


def build_getsongbpm_fetch(api_key: str):
    """Gerçek GetSongBPM HTTP fetcher closure'ı DÖNDÜRÜR (loop çalıştırmaz).

    Powered by GetSongBPM (https://getsongbpm.com).
    api_key boşsa fetch çağrıldığında güvenle None döner (ağ isteği yapılmaz).
    """
    def fetch(title: str, artist: str):
        if not api_key:
            return None
        import requests  # lokal import: ağ-yoksa modül yükü çıkmasın

        url = "https://api.getsongbpm.com/search/"
        params = {
            "api_key": api_key,
            "type": "song",
            "lookup": f"song:{title} artist:{artist}",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("search") or []
        if not results:
            return None
        first = results[0]
        tempo = first.get("tempo")
        bpm = int(tempo) if tempo not in (None, "") else None
        camelot = open_key_to_camelot(first.get("open_key", ""))
        if bpm is None and camelot is None:
            return None
        return {"bpm": bpm, "camelot": camelot}

    return fetch
