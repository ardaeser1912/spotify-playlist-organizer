"""genre.normalize_bucket + split_by_genre testleri (happy + edge)."""
from spotify_organizer import genre
from spotify_organizer import fixtures


# --- normalize_bucket: öncelik + substring eşleşmesi ---

def test_normalize_pop():
    assert genre.normalize_bucket(["turkish pop", "pop"]) == "Pop"


def test_normalize_arabesk_oncelik():
    # "arabesk" Pop'tan önce gelir
    assert genre.normalize_bucket(["turkish pop", "arabesk"]) == "Arabesk"


def test_normalize_dance_pop():
    assert genre.normalize_bucket(["dance pop", "pop"]) == "Pop"


def test_normalize_rnb_oncelik():
    # "r&b" Pop'tan önce gelir
    assert genre.normalize_bucket(["pop", "r&b"]) == "R&B"


def test_normalize_french_house():
    assert genre.normalize_bucket(["french house", "electronic"]) == "Elektronik"


def test_normalize_edm():
    assert genre.normalize_bucket(["edm", "electronic"]) == "Elektronik"


def test_normalize_hiphop():
    assert genre.normalize_bucket(["hip hop", "rap"]) == "Hip-Hop"


def test_normalize_rock():
    assert genre.normalize_bucket(["hard rock", "rock"]) == "Rock"


def test_normalize_empty():
    assert genre.normalize_bucket([]) == "Diğer"


def test_normalize_no_match():
    assert genre.normalize_bucket(["jazz"]) == "Diğer"


# --- split_by_genre: fixtures verisiyle ---

def _liked_tracks_and_genres():
    pl = next(p for p in fixtures.PLAYLISTS if p["id"] == "p_liked")
    tracks = [fixtures.TRACKS[tid] for tid in pl["track_ids"]]
    artist_genres = {aid: a["genres"] for aid, a in fixtures.ARTISTS.items()}
    return tracks, artist_genres


def test_split_buckets_olusur():
    tracks, artist_genres = _liked_tracks_and_genres()
    result = genre.split_by_genre(tracks, artist_genres)
    for bucket in ("Pop", "Rock", "Elektronik", "Hip-Hop"):
        assert bucket in result


def test_split_toplam_korunur():
    tracks, artist_genres = _liked_tracks_and_genres()
    result = genre.split_by_genre(tracks, artist_genres)
    total = sum(len(v) for v in result.values())
    assert total == len(tracks)


def test_split_sira_bozulmaz():
    tracks, artist_genres = _liked_tracks_and_genres()
    result = genre.split_by_genre(tracks, artist_genres)
    # Her kova içinde track'ler giriş sırasını korur
    for bucket_tracks in result.values():
        ids = [t["id"] for t in bucket_tracks]
        order = [t["id"] for t in tracks if t["id"] in ids]
        assert ids == order


def test_split_no_empty_buckets():
    tracks, artist_genres = _liked_tracks_and_genres()
    result = genre.split_by_genre(tracks, artist_genres)
    assert all(len(v) > 0 for v in result.values())


def test_split_bilinmeyen_artist_diger():
    # artist_genres sözlüğünde olmayan bir artist_id → "Diğer"
    tracks = [
        {"id": "x1", "title": "Yok", "artist": "?", "artist_id": "a_yok",
         "uri": "spotify:track:x1", "duration_ms": 1000, "bpm": None,
         "camelot": None, "year": 2020, "popularity": 0},
    ]
    result = genre.split_by_genre(tracks, {})
    assert result == {"Diğer": [tracks[0]]}


def test_split_track_mutasyona_ugramaz():
    tracks, artist_genres = _liked_tracks_and_genres()
    before = {t["id"]: dict(t) for t in tracks}
    result = genre.split_by_genre(tracks, artist_genres)
    # Gruplanan track'ler orijinal referans + içerik aynı kalır
    for bucket_tracks in result.values():
        for t in bucket_tracks:
            assert t == before[t["id"]]
