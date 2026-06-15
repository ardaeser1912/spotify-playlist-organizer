"""organize.py testleri — dedupe, sort, merge, split, insights (happy + edge)."""

import pytest

from spotify_organizer import organize, fixtures


def _all_tracks():
    return list(fixtures.TRACKS.values())


# ---------- dedupe ----------

def test_dedupe_with_duplicates():
    tracks = _all_tracks()
    # aynı id tekrarı + aynı (title, artist) tekrarı (farklı id ile)
    same_id = dict(tracks[0])
    same_pair = dict(tracks[1])
    same_pair["id"] = "dup_x"  # id farklı ama title+artist aynı
    dirty = tracks + [same_id, same_pair]
    out = organize.dedupe(dirty)

    assert len(out["removed"]) == 2
    kept_ids = [t["id"] for t in out["kept"]]
    assert len(kept_ids) == len(set(kept_ids))  # kept'te id tekrarı yok
    kept_pairs = [(t["title"].lower(), t["artist"].lower()) for t in out["kept"]]
    assert len(kept_pairs) == len(set(kept_pairs))  # kept'te (title,artist) tekrarı yok


def test_dedupe_clean_list_empty_removed():
    tracks = _all_tracks()
    out = organize.dedupe(tracks)
    assert out["removed"] == []
    assert len(out["kept"]) == len(tracks)


def test_dedupe_keeps_first_seen_order():
    tracks = _all_tracks()
    dirty = tracks + [dict(tracks[0])]
    out = organize.dedupe(dirty)
    assert [t["id"] for t in out["kept"]] == [t["id"] for t in tracks]


# ---------- sort_tracks ----------

def test_sort_popularity_desc():
    result = organize.sort_tracks(_all_tracks(), [("popularity", "desc")])
    pops = [t["popularity"] for t in result]
    assert pops == sorted(pops, reverse=True)
    assert result[0]["popularity"] == max(pops)


def test_sort_year_asc():
    result = organize.sort_tracks(_all_tracks(), [("year", "asc")])
    years = [t["year"] for t in result]
    assert years == sorted(years)


def test_sort_bpm_asc_none_last():
    result = organize.sort_tracks(_all_tracks(), [("bpm", "asc")])
    # t17 bpm=None -> sonda
    assert result[-1]["id"] == "t17"
    assert result[-1]["bpm"] is None
    bpms = [t["bpm"] for t in result if t["bpm"] is not None]
    assert bpms == sorted(bpms)


def test_sort_bpm_desc_none_still_last():
    result = organize.sort_tracks(_all_tracks(), [("bpm", "desc")])
    assert result[-1]["id"] == "t17"
    bpms = [t["bpm"] for t in result if t["bpm"] is not None]
    assert bpms == sorted(bpms, reverse=True)


def test_sort_multi_key_artist_then_year():
    result = organize.sort_tracks(
        _all_tracks(), [("artist", "asc"), ("year", "asc")]
    )
    # birincil anahtar artist asc
    artists = [t["artist"] for t in result]
    assert artists == sorted(artists)
    # aynı artist içinde year artan olmalı (Tarkan: t02=1997, t01=2001)
    tarkan = [t for t in result if t["artist"] == "Tarkan"]
    assert [t["id"] for t in tarkan] == ["t02", "t01"]


def test_sort_does_not_mutate_input():
    tracks = _all_tracks()
    snapshot = [dict(t) for t in tracks]
    organize.sort_tracks(tracks, [("popularity", "desc")])
    assert tracks == snapshot


# ---------- merge_playlists ----------

def test_merge_playlists_dedupes_common():
    pl1 = fixtures.get_playlist("p_yaz")["tracks"]
    pl2 = fixtures.get_playlist("p_spor")["tracks"]
    merged = organize.merge_playlists([pl1, pl2])
    ids = [t["id"] for t in merged]
    assert len(ids) == len(set(ids))  # ortak track (t12) tek kez
    # birleşim kümesi eksiksiz
    assert set(ids) == {t["id"] for t in pl1} | {t["id"] for t in pl2}


def test_merge_playlists_empty():
    assert organize.merge_playlists([]) == []


# ---------- split_by_decade ----------

def test_split_by_decade_buckets():
    out = organize.split_by_decade(_all_tracks())
    for label in ("1990'lar", "2000'lar", "2010'lar", "2020'lar"):
        assert label in out
    total = sum(len(v) for v in out.values())
    assert total == len(_all_tracks())


def test_split_by_decade_unknown_year():
    track = dict(fixtures.TRACKS["t01"])
    track["year"] = None
    out = organize.split_by_decade([track])
    assert out == {"Bilinmeyen": [track]}


# ---------- split_by_tempo ----------

def test_split_by_tempo_unknown_bpm():
    out = organize.split_by_tempo(_all_tracks())
    unknown_ids = [t["id"] for t in out.get("Bilinmeyen", [])]
    assert "t17" in unknown_ids


def test_split_by_tempo_boundaries():
    # bpm 100 ve 128 sınır -> "Orta"; 99 -> Yavaş, 129 -> Hızlı
    base = dict(fixtures.TRACKS["t01"])
    def mk(bpm):
        t = dict(base)
        t["bpm"] = bpm
        return t
    out = organize.split_by_tempo([mk(99), mk(100), mk(128), mk(129)])
    assert len(out["Yavaş (<100)"]) == 1
    assert len(out["Orta (100-128)"]) == 2  # 100 ve 128 dahil
    assert len(out["Hızlı (>128)"]) == 1


# ---------- split_by_size ----------

def test_split_by_size_chunks():
    parts = organize.split_by_size([1, 2, 3, 4, 5], 2)
    assert [len(p) for p in parts] == [2, 2, 1]
    assert parts == [[1, 2], [3, 4], [5]]


def test_split_by_size_zero_raises():
    with pytest.raises(ValueError):
        organize.split_by_size([1, 2, 3], 0)


# ---------- insights ----------

def test_insights_basic():
    tracks = _all_tracks()
    out = organize.insights(tracks)
    assert out["total"] == len(tracks)
    assert 0.0 <= out["avg_popularity"] <= 100.0
    # top_artists azalan
    counts = [c for _, c in out["top_artists"]]
    assert counts == sorted(counts, reverse=True)
    assert len(out["top_artists"]) <= 5
    # genre_labels yokken genre_dist boş
    assert out["genre_dist"] == {}
    # bpm_dist & decade_dist split fonksiyonlarıyla tutarlı
    assert out["bpm_dist"] == {
        b: len(v) for b, v in organize.split_by_tempo(tracks).items()
    }


def test_insights_genre_dist_counted():
    tracks = _all_tracks()
    labels = {"t01": "Pop", "t02": "Pop", "t14": "Hip-Hop"}
    out = organize.insights(tracks, genre_labels=labels)
    assert out["genre_dist"] == {"Pop": 2, "Hip-Hop": 1}


def test_insights_empty():
    out = organize.insights([])
    assert out["total"] == 0
    assert out["avg_popularity"] == 0.0
    assert out["top_artists"] == []
    assert out["genre_dist"] == {}


def test_insights_does_not_mutate_input():
    tracks = _all_tracks()
    snapshot = [dict(t) for t in tracks]
    organize.insights(tracks, genre_labels={"t01": "Pop"})
    assert tracks == snapshot
