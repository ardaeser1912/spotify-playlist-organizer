"""Ücretsiz tür kaynağı — iTunes Search API'den sanatçı türünü çeker.

Spotify dev-mode /artists 403 verdiği için tür buradan gelir. ANAHTARSIZ:
    https://itunes.apple.com/search?term=ARTIST&entity=musicArtist&limit=1
    → {"results":[{"primaryGenreName":"Hip-Hop/Rap", ...}]}

iTunes ham tür adları genre.py kovalarına çevrilir (Pop/Rock/Elektronik/
Hip-Hop/R&B/Arabesk/Diğer). Saf fonksiyonlar; ağ sadece fetch_itunes_genre'da.
"""
from __future__ import annotations

import json
import os
from urllib.parse import quote

import requests

OTHER = "Diğer"

# Öncelik sırasıyla (üstte olan kazanır). iTunes "Dance"/"Alternative" gibi
# kendine özgü adlar kullanır → kova eşlemesi onları da kapsar.
_BUCKETS = [
    ("Arabesk", ("arabesk",)),
    ("Hip-Hop", ("hip-hop", "hip hop", "rap")),
    ("Elektronik", ("dance", "electronic", "house", "techno", "edm", "trance")),
    ("R&B", ("r&b", "rnb", "soul", "funk")),
    ("Rock", ("rock", "metal", "punk", "alternative", "grunge")),
    ("Pop", ("pop",)),
]

_ITUNES_URL = "https://itunes.apple.com/search"
_MB_URL = "https://musicbrainz.org/ws/2/artist"
_MB_UA = "SpotifyPlaylistOrganizer/1.0 (kisisel kullanim)"


def itunes_to_bucket(itunes_genre: str) -> str:
    """iTunes ham tür adını ana kovaya çevirir. Boş/eşleşme yok → 'Diğer'."""
    g = (itunes_genre or "").lower()
    for bucket, keywords in _BUCKETS:
        for kw in keywords:
            if kw in g:
                return bucket
    return OTHER


def fetch_itunes_genre(artist_name: str, http_get=None) -> str | None:
    """iTunes'tan ham primaryGenreName döndürür; bulunamazsa None.

    http_get(url, **kwargs) enjekte edilebilir (test için). None ise modül
    düzeyi requests.get kullanılır (timeout=10). Hata/boş → None.
    """
    if http_get is None:
        http_get = requests.get
    url = f"{_ITUNES_URL}?term={quote(artist_name)}&entity=musicArtist&limit=1"
    try:
        resp = http_get(url, timeout=10)
        data = resp.json()
        results = data.get("results") or []
        if not results:
            return None
        genre = results[0].get("primaryGenreName")
        return genre or None
    except Exception:
        return None


def fetch_musicbrainz_genre(artist_name: str, http_get=None) -> str | None:
    """MusicBrainz'den sanatçı tür etiketlerini boşlukla birleştirip döndürür; yoksa None.

    ANAHTARSIZ ama User-Agent zorunlu. iTunes IP throttle'a takılınca güvenilir
    alternatif (sürekli sorguya dayanıklı, ~1 istek/sn). Dönen string itunes_to_bucket
    ile kovaya çevrilir (etiketler: 'pop rap hip-hop' gibi).
    """
    if http_get is None:
        http_get = requests.get
    url = f"{_MB_URL}?query={quote(f'artist:\"{artist_name}\"')}&fmt=json&limit=1"
    try:
        resp = http_get(url, headers={"User-Agent": _MB_UA}, timeout=10)
        artists = (resp.json().get("artists") or [])
        if not artists:
            return None
        tags = [t.get("name", "") for t in (artists[0].get("tags") or [])]
        joined = " ".join(t for t in tags if t)
        return joined or None
    except Exception:
        return None


def buckets_for_artists(artist_names, cache: dict, fetch=fetch_itunes_genre) -> dict:
    """Benzersiz sanatçı adları için {isim: kova}.

    cache anahtarı isim.lower(); ham tür tutar. Cache'te varsa fetch çağrılmaz.
    fetch None dönerse o isim 'Diğer' kovasına konur.
    """
    out: dict[str, str] = {}
    for name in dict.fromkeys(artist_names):  # benzersiz + sıra korur
        key = name.lower()
        if key in cache:
            raw = cache[key]
        else:
            raw = fetch(name)
            cache[key] = raw
        out[name] = OTHER if raw is None else itunes_to_bucket(raw)
    return out


def load_cache(path) -> dict:
    """cache/genres.json yükler; dosya yoksa {}."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_cache(path, cache: dict) -> None:
    """cache'i JSON olarak yazar."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
