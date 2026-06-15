"""smartmix.py testleri — Akıllı Mix kümeleme + küme içi akış (happy + edge)."""

import copy

from spotify_organizer import smartmix, fixtures, order


def _all():
    return list(fixtures.TRACKS.values())


def _ids(tracks):
    return sorted(t["id"] for t in tracks)


# ---------- _has_harmonic ----------

def test_has_harmonic_full_data_true():
    # t17 hariç tüm fixture'larda bpm+camelot dolu -> yarıdan fazlası
    assert smartmix._has_harmonic(_all()) is True


def test_has_harmonic_empty_false():
    assert smartmix._has_harmonic([]) is False


def test_has_harmonic_no_data_false():
    bare = [{"id": "x", "title": "X", "bpm": None, "camelot": None, "year": 2000}]
    assert smartmix._has_harmonic(bare) is False


# ---------- smart_order: permütasyon / mutasyon ----------

def test_smart_order_is_permutation_no_genre():
    src = _all()
    before = copy.deepcopy(src)
    out = smartmix.smart_order(src)
    assert _ids(out) == _ids(src)
    assert len(out) == len(src)
    # mutasyon yok: giriş track'leri değişmedi
    assert src == before


def test_smart_order_is_permutation_with_genre():
    src = _all()
    genre_of = {t["id"]: t["artist"] for t in src}
    out = smartmix.smart_order(src, genre_of)
    assert _ids(out) == _ids(src)
    assert len(out) == len(src)


def test_smart_order_empty():
    assert smartmix.smart_order([]) == []
    assert smartmix.smart_order([], {}) == []


def test_smart_order_single_track():
    one = [fixtures.TRACKS["t07"]]
    out = smartmix.smart_order(one)
    assert _ids(out) == _ids(one)


# ---------- smart_order: kümeleme ----------

def test_smart_order_dominant_bucket_first():
    # 3 rock, 2 pop, 1 rap -> rock kümesi en başta gelmeli
    g = {
        "r1": "rock", "r2": "rock", "r3": "rock",
        "p1": "pop", "p2": "pop",
        "h1": "rap",
    }
    tracks = [
        {"id": "p1", "title": "P1", "bpm": None, "camelot": None, "year": 2010},
        {"id": "r1", "title": "R1", "bpm": None, "camelot": None, "year": 2000},
        {"id": "h1", "title": "H1", "bpm": None, "camelot": None, "year": 2005},
        {"id": "r2", "title": "R2", "bpm": None, "camelot": None, "year": 2001},
        {"id": "p2", "title": "P2", "bpm": None, "camelot": None, "year": 2011},
        {"id": "r3", "title": "R3", "bpm": None, "camelot": None, "year": 2002},
    ]
    out = smartmix.smart_order(tracks, g)
    ids = [t["id"] for t in out]
    # ilk 3 rock olmalı
    assert set(ids[:3]) == {"r1", "r2", "r3"}
    # aynı türdekiler bitişik (pop'lar ardışık)
    assert ids[3:5] == ["p1", "p2"] or set(ids[3:5]) == {"p1", "p2"}
    assert ids[5] == "h1"


def test_smart_order_same_bucket_contiguous():
    src = _all()
    genre_of = {t["id"]: t["artist"] for t in src}
    out = smartmix.smart_order(src, genre_of)
    # her kova için çıkıştaki indeksler bitişik bir aralık olmalı
    seen_buckets = []
    for t in out:
        b = genre_of[t["id"]]
        if not seen_buckets or seen_buckets[-1] != b:
            assert b not in seen_buckets, f"kova {b} bitişik değil"
            seen_buckets.append(b)


def test_smart_order_equal_size_alphabetical():
    # iki kova eşit boyutlu -> alfabetik (alpha önce zeta)
    g = {"a1": "zeta", "a2": "alpha"}
    tracks = [
        {"id": "a1", "title": "A1", "bpm": None, "camelot": None, "year": 2000},
        {"id": "a2", "title": "A2", "bpm": None, "camelot": None, "year": 2001},
    ]
    out = smartmix.smart_order(tracks, g)
    assert [t["id"] for t in out] == ["a2", "a1"]


# ---------- küme içi akış ----------

def test_cluster_with_bpm_camelot_uses_harmonic():
    # bpm+camelot dolu küme harmonic_order ile aynı sonucu vermeli
    src = _all()
    expected = order.harmonic_order(src)
    out = smartmix.smart_order(src)  # genre_of None -> tek küme
    assert [t["id"] for t in out] == [t["id"] for t in expected]


def test_cluster_without_data_falls_back_to_year():
    # bpm/camelot None -> yıl sırasına düş, kırılmadan
    tracks = [
        {"id": "y3", "title": "C", "bpm": None, "camelot": None, "year": 2015},
        {"id": "y1", "title": "A", "bpm": None, "camelot": None, "year": 1990},
        {"id": "y2", "title": "B", "bpm": None, "camelot": None, "year": 2000},
        {"id": "y0", "title": "D", "bpm": None, "camelot": None, "year": None},
    ]
    out = smartmix.smart_order(tracks)
    ids = [t["id"] for t in out]
    assert ids == ["y1", "y2", "y3", "y0"]  # yıl asc, None sona


def test_cluster_same_year_falls_back_to_title():
    tracks = [
        {"id": "s2", "title": "Bravo", "bpm": None, "camelot": None, "year": 2000},
        {"id": "s1", "title": "Alpha", "bpm": None, "camelot": None, "year": 2000},
    ]
    out = smartmix.smart_order(tracks)
    assert [t["id"] for t in out] == ["s1", "s2"]


def test_smart_order_none_single_cluster_sorted():
    src = _all()
    out = smartmix.smart_order(src, None)
    assert _ids(out) == _ids(src)
    # tek küme = harmonic akış (fixture dolu)
    assert [t["id"] for t in out] == [t["id"] for t in order.harmonic_order(src)]


# ---------- smart_order_groups ----------

def test_groups_structure_and_total():
    src = _all()
    genre_of = {t["id"]: t["artist"] for t in src}
    groups = smartmix.smart_order_groups(src, genre_of)
    assert all({"bucket", "count", "tracks"} <= set(g) for g in groups)
    # toplam sayı korunur
    assert sum(g["count"] for g in groups) == len(src)
    assert sum(len(g["tracks"]) for g in groups) == len(src)
    # her grupta count == len(tracks)
    assert all(g["count"] == len(g["tracks"]) for g in groups)


def test_groups_none_single_bucket():
    src = _all()
    groups = smartmix.smart_order_groups(src, None)
    assert len(groups) == 1
    assert groups[0]["bucket"] == smartmix.SINGLE_BUCKET
    assert groups[0]["count"] == len(src)


def test_groups_order_matches_smart_order():
    # grup tracks'lerinin ardışık birleşimi smart_order ile aynı olmalı
    src = _all()
    genre_of = {t["id"]: t["artist"] for t in src}
    groups = smartmix.smart_order_groups(src, genre_of)
    flat = [t["id"] for g in groups for t in g["tracks"]]
    assert flat == [t["id"] for t in smartmix.smart_order(src, genre_of)]
