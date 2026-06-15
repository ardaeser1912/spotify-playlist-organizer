"""Playlist düzenleme — dedupe, sıralama, birleştirme, bölme, içgörüler.

Saf Python, ağ YOK. Track şekli fixtures.py/client.py ile birebir aynı:
    {id, title, artist, artist_id, uri, duration_ms, bpm, camelot, year, popularity}

Track'ler asla mutasyona uğratılmaz; fonksiyonlar yeni liste/dict döndürür.
"""
from __future__ import annotations

from collections import Counter

# Tempo bantları — split_by_tempo ve insights ortak kullanır.
SLOW = "Yavaş (<100)"
MEDIUM = "Orta (100-128)"
FAST = "Hızlı (>128)"
UNKNOWN = "Bilinmeyen"

# sort_tracks için geçerli alanlar.
_SORT_FIELDS = {"title", "artist", "year", "popularity", "bpm", "duration_ms"}


def _track_key(track: dict) -> tuple:
    """Dedupe kimliği: (title, artist) küçük harf ikilisi."""
    return (str(track.get("title", "")).lower(), str(track.get("artist", "")).lower())


def dedupe(tracks: list[dict]) -> dict:
    """Aynı `id` VEYA aynı (title, artist) tekrarını ayıklar.

    İlk görülen kalır, sonrakiler removed. Sıra korunur.
    """
    kept: list[dict] = []
    removed: list[dict] = []
    seen_ids: set = set()
    seen_pairs: set = set()
    for track in tracks:
        tid = track.get("id")
        pair = _track_key(track)
        if tid in seen_ids or pair in seen_pairs:
            removed.append(track)
            continue
        seen_ids.add(tid)
        seen_pairs.add(pair)
        kept.append(track)
    return {"kept": kept, "removed": removed}


def sort_tracks(tracks: list[dict], keys: list) -> list:
    """Çok-anahtarlı kararlı sıralama.

    keys = [(alan, yön)]; alan in _SORT_FIELDS, yön in {"asc","desc"}.
    None değerler asc/desc fark etmeksizin HER ZAMAN sona gider.
    Kararlı sort: son anahtardan başa doğru uygulanır. Girdi kopyalanır.
    """
    result = list(tracks)
    for field, direction in reversed(keys):
        if field not in _SORT_FIELDS:
            raise ValueError(f"geçersiz sıralama alanı: {field}")
        if direction not in ("asc", "desc"):
            raise ValueError(f"geçersiz yön: {direction}")
        reverse = direction == "desc"

        def sort_key(track, _field=field, _reverse=reverse):
            value = track.get(_field)
            is_missing = value is None
            # None her zaman sona: reverse=True iken sort tersine çevireceği için
            # missing bayrağını da tersine al ki yine sonda kalsın.
            # missing iken karşılaştırılacak değeri 0 yap (tip uyumu için);
            # flag onları zaten ayrı gruba aldığından dolu değerlerle kıyaslanmaz.
            flag = is_missing != _reverse
            return (flag, 0 if is_missing else value)

        result.sort(key=sort_key, reverse=reverse)
    return result


def merge_playlists(track_lists: list) -> list:
    """Birden çok track listesini birleştirir, dedupe (id/title-artist).

    İlk görülen sırada tutulur.
    """
    flat: list[dict] = []
    for lst in track_lists:
        flat.extend(lst)
    return dedupe(flat)["kept"]


def split_by_decade(tracks: list[dict]) -> dict:
    """Track'leri on-yıllık kovalara böler (year//10*10).

    year None -> "Bilinmeyen". Sadece dolu kovalar döner.
    """
    out: dict[str, list[dict]] = {}
    for track in tracks:
        year = track.get("year")
        if year is None:
            label = UNKNOWN
        else:
            label = f"{year // 10 * 10}'lar"
        out.setdefault(label, []).append(track)
    return out


def split_by_tempo(tracks: list[dict]) -> dict:
    """Track'leri BPM bantlarına böler.

    bpm<100 -> Yavaş, 100<=bpm<=128 -> Orta, bpm>128 -> Hızlı, None -> Bilinmeyen.
    Sadece dolu kovalar döner.
    """
    out: dict[str, list[dict]] = {}
    for track in tracks:
        out.setdefault(_tempo_band(track.get("bpm")), []).append(track)
    return out


def _tempo_band(bpm) -> str:
    if bpm is None:
        return UNKNOWN
    if bpm < 100:
        return SLOW
    if bpm <= 128:
        return MEDIUM
    return FAST


def split_by_size(tracks: list[dict], size: int) -> list:
    """Track'leri `size`lik parçalara böler (son parça kısa olabilir).

    size <= 0 -> ValueError.
    """
    if size <= 0:
        raise ValueError("size pozitif olmalı")
    return [tracks[i:i + size] for i in range(0, len(tracks), size)]


def insights(tracks: list[dict], genre_labels: dict | None = None) -> dict:
    """Playlist özeti.

    genre_labels = {track_id: kova} verilirse genre_dist sayılır; yoksa {}.
    genre.py IMPORT EDİLMEZ — tür bilgisi dışarıdan gelir.
    """
    total = len(tracks)

    bpm_dist = {band: len(items) for band, items in split_by_tempo(tracks).items()}
    decade_dist = {dec: len(items) for dec, items in split_by_decade(tracks).items()}

    artist_counter = Counter(t.get("artist") for t in tracks)
    top_artists = [[name, count] for name, count in artist_counter.most_common(5)]

    if total:
        avg_popularity = round(
            sum(t.get("popularity", 0) for t in tracks) / total, 1
        )
    else:
        avg_popularity = 0.0

    if genre_labels:
        genre_dist = dict(
            Counter(
                genre_labels[t["id"]]
                for t in tracks
                if t["id"] in genre_labels
            )
        )
    else:
        genre_dist = {}

    return {
        "total": total,
        "bpm_dist": bpm_dist,
        "decade_dist": decade_dist,
        "top_artists": top_artists,
        "avg_popularity": avg_popularity,
        "genre_dist": genre_dist,
    }
