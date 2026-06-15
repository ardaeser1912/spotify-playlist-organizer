"""Akıllı Mix — türe göre kümele + her küme içinde akıcı geçiş.

Saf Python, ağ YOK. Spotify "Akıllı Mix" hissi: benzer şarkılar bir arada,
küme içinde pürüzsüz akış (bpm/camelot varsa Camelot DJ-akışı, yoksa döneme/yıla).

Track şekli fixtures.py ile birebir aynı:
    {id, title, artist, duration_ms, bpm:int|None, camelot:str|None, year, popularity}

Track'ler asla mutasyona uğratılmaz; fonksiyonlar yeni liste/dict döndürür.
"""
from __future__ import annotations

from .order import harmonic_order

SINGLE_BUCKET = "Akıllı Mix"


def _has_harmonic(tracks: list[dict]) -> bool:
    """Track'lerin EN AZ yarısında hem bpm hem camelot dolu mu."""
    if not tracks:
        return False
    full = sum(
        1 for t in tracks if t.get("bpm") is not None and t.get("camelot") is not None
    )
    return full * 2 >= len(tracks)


def _flow(tracks: list[dict]) -> list[dict]:
    """Tek küme içi akış sıralaması.

    Yeterli bpm+camelot varsa harmonic DJ-akışı; yoksa yıla (None sona)
    sonra başlığa göre kararlı sıralama.
    """
    if _has_harmonic(tracks):
        return harmonic_order(tracks)
    return sorted(
        tracks,
        key=lambda t: (t.get("year") is None, t.get("year") or 0, str(t.get("title", ""))),
    )


def _cluster(tracks: list[dict], genre_of) -> list[tuple[str, list[dict]]]:
    """Track'leri kovalara böler, küme sırasını uygular.

    genre_of None -> tek küme (SINGLE_BUCKET).
    Aksi halde: boyut desc, eşitlikte kova adı alfabetik (asc).
    """
    if genre_of is None:
        return [(SINGLE_BUCKET, list(tracks))]

    buckets: dict[str, list[dict]] = {}
    for track in tracks:
        bucket = genre_of.get(track.get("id"))
        buckets.setdefault(bucket, []).append(track)

    return sorted(buckets.items(), key=lambda kv: (-len(kv[1]), str(kv[0])))


def smart_order(tracks: list[dict], genre_of: dict | None = None) -> list[dict]:
    """Akıllı Mix sıralaması: türe göre kümele + küme içi akıcı geçiş.

    Çıkış girişin permütasyonudur; uzunluk korunur, track mutasyonu yoktur.
    """
    ordered: list[dict] = []
    for _bucket, items in _cluster(tracks, genre_of):
        ordered.extend(_flow(items))
    return ordered


def smart_order_groups(tracks: list[dict], genre_of: dict | None = None) -> list[dict]:
    """Önizleme için kümelenmiş + sıralı gruplar.

    [{"bucket": kova, "count": n, "tracks": [...sıralı...]}] (küme sırasıyla).
    """
    return [
        {"bucket": bucket, "count": len(items), "tracks": _flow(items)}
        for bucket, items in _cluster(tracks, genre_of)
    ]
