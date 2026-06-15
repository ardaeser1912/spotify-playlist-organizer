"""Tür (genre) kovalama — ham sanatçı genre listelerini tek ana kovaya indirir.

Saf Python, ağ YOK. Track şekli fixtures.py/client.py ile birebir aynı:
    {id, title, artist, artist_id, uri, duration_ms, bpm, camelot, year, popularity}
"""
from __future__ import annotations

# Öncelik sırasıyla (üstte olan kazanır). Her kova → anahtar kelimeler.
# Genre'lerden herhangi biri anahtar kelimeyi substring olarak (küçük harf) içerirse o kova kazanır.
_BUCKETS = [
    ("Arabesk",  ("arabesk",)),
    ("Hip-Hop",  ("hip hop", "hip-hop", "rap")),
    ("Elektronik", ("electronic", "house", "edm", "techno", "trance")),
    ("R&B",      ("r&b", "rnb", "soul")),
    ("Rock",     ("rock", "metal", "punk")),
    ("Pop",      ("pop",)),
]

OTHER = "Diğer"


def normalize_bucket(genres: list[str]) -> str:
    """Ham genre listesini tek ana kovaya indirir. Eşleşme yoksa 'Diğer'."""
    lowered = [g.lower() for g in genres]
    for bucket, keywords in _BUCKETS:
        for kw in keywords:
            if any(kw in g for g in lowered):
                return bucket
    return OTHER


def split_by_genre(tracks: list[dict], artist_genres: dict) -> dict[str, list[dict]]:
    """Track'leri sanatçı genre'lerine göre kovalara böler.

    artist_genres = {artist_id: [genre,...]}. artist_id sözlükte yoksa 'Diğer'.
    Dönen dict giriş sırasını korur, boş kovaları içermez, track'leri mutasyona uğratmaz.
    """
    out: dict[str, list[dict]] = {}
    for track in tracks:
        genres = artist_genres.get(track["artist_id"], [])
        bucket = normalize_bucket(genres)
        out.setdefault(bucket, []).append(track)
    return out
