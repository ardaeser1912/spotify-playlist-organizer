"""order.py testleri — Camelot harmonic mixing + BPM rampası (happy + edge)."""

from spotify_organizer import order, fixtures


# ---------- camelot_neighbors ----------

def test_neighbors_8B():
    assert order.camelot_neighbors("8B") == {"8B", "8A", "9B", "7B"}


def test_neighbors_wrap_12B_includes_1B():
    assert "1B" in order.camelot_neighbors("12B")


def test_neighbors_wrap_1B_includes_12B():
    assert "12B" in order.camelot_neighbors("1B")


def test_neighbors_relative_minor_major():
    # aynı sayı, diğer harf
    assert "8A" in order.camelot_neighbors("8B")
    assert "8B" in order.camelot_neighbors("8A")


def test_neighbors_none_is_empty():
    assert order.camelot_neighbors(None) == set()


def test_neighbors_empty_string_is_empty():
    assert order.camelot_neighbors("") == set()


def test_neighbors_invalid_code_is_empty():
    assert order.camelot_neighbors("13B") == set()
    assert order.camelot_neighbors("8C") == set()
    assert order.camelot_neighbors("XX") == set()


# ---------- harmonic_order ----------

def _all_tracks():
    return list(fixtures.TRACKS.values())


def test_order_is_permutation():
    tracks = _all_tracks()
    result = order.harmonic_order(tracks)
    assert len(result) == len(tracks)
    assert sorted(t["id"] for t in result) == sorted(t["id"] for t in tracks)


def test_order_does_not_mutate_input():
    tracks = _all_tracks()
    snapshot = [dict(t) for t in tracks]
    order.harmonic_order(tracks)
    assert tracks == snapshot


def test_camelot_none_track_is_last():
    tracks = _all_tracks()
    result = order.harmonic_order(tracks)
    # t17 "Adsız Parça" camelot=None -> en sonda
    assert result[-1]["id"] == "t17"
    assert result[-1]["camelot"] is None


def test_consecutive_pairs_mostly_harmonic():
    # camelot'lu kısımda ardışık çiftlerin ÇOĞU gerçekten uyumlu olmalı.
    tracks = _all_tracks()
    result = order.harmonic_order(tracks)
    cam = [t for t in result if t.get("camelot") is not None]
    harmonic_pairs = 0
    for a, b in zip(cam, cam[1:]):
        if b["camelot"] in order.camelot_neighbors(a["camelot"]):
            harmonic_pairs += 1
    # en az ilk birkaç geçişin uyumlu olduğunu garanti et
    assert harmonic_pairs >= 3


def test_first_pair_is_harmonic():
    tracks = _all_tracks()
    result = order.harmonic_order(tracks)
    cam = [t for t in result if t.get("camelot") is not None]
    assert cam[1]["camelot"] in order.camelot_neighbors(cam[0]["camelot"])


def test_empty_list():
    assert order.harmonic_order([]) == []


def test_single_element():
    track = fixtures.TRACKS["t01"]
    result = order.harmonic_order([track])
    assert len(result) == 1
    assert result[0]["id"] == "t01"


def test_single_element_camelot_none():
    track = fixtures.TRACKS["t17"]
    result = order.harmonic_order([track])
    assert len(result) == 1
    assert result[0]["id"] == "t17"


def test_only_camelot_none_tracks():
    track = dict(fixtures.TRACKS["t17"])
    result = order.harmonic_order([track])
    assert [t["id"] for t in result] == ["t17"]
