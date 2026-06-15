"""Kenar-durum sertleştirme testleri — boş/tek/None girdiler ve servis sınır halleri.

Amaç: çekirdek saf fonksiyonların ve servis katmanının dejenere girdilerde
PATLAMADAN mantıklı (çoğunlukla boş) sonuç döndürdüğünü kanıtlamak.
given/when/then düzeni mevcut test stiliyle uyumlu. Gerçek ağ/auth YOK.
"""
import os

import pytest

from spotify_organizer import enrich, genre, order, organize
from spotify_organizer.service import OrganizerService
from tests.mock_client import MockClient


def _track(tid, **over):
    """Tam şekilli minimal track; over ile alan ezilebilir."""
    base = {
        "id": tid,
        "title": f"Şarkı {tid}",
        "artist": f"Sanatçı {tid}",
        "artist_id": f"a_{tid}",
        "uri": f"spotify:track:{tid}",
        "duration_ms": 200000,
        "bpm": 120,
        "camelot": "8B",
        "year": 2020,
        "popularity": 50,
    }
    base.update(over)
    return base


def _svc(tmp_path):
    return OrganizerService(MockClient(), backup_dir=str(tmp_path / "backups"))


# ============================================================
# BOŞ liste — hiçbiri patlamamalı, mantıklı boş sonuç dönmeli
# ============================================================

def test_given_empty_when_split_by_genre_then_empty_dict():
    assert genre.split_by_genre([], {}) == {}


def test_given_empty_when_harmonic_order_then_empty_list():
    assert order.harmonic_order([]) == []


def test_given_empty_when_dedupe_then_empty_kept_and_removed():
    assert organize.dedupe([]) == {"kept": [], "removed": []}


def test_given_empty_when_sort_tracks_then_empty_list():
    assert organize.sort_tracks([], [("popularity", "desc")]) == []


def test_given_empty_when_merge_playlists_then_empty_list():
    assert organize.merge_playlists([]) == []


def test_given_empty_when_split_by_decade_then_empty_dict():
    assert organize.split_by_decade([]) == {}


def test_given_empty_when_split_by_tempo_then_empty_dict():
    assert organize.split_by_tempo([]) == {}


def test_given_empty_when_split_by_size_then_empty_list():
    assert organize.split_by_size([], 5) == []


def test_given_empty_when_insights_then_zeroed_summary():
    out = organize.insights([])
    assert out["total"] == 0
    assert out["avg_popularity"] == 0.0
    assert out["top_artists"] == []
    assert out["bpm_dist"] == {}
    assert out["decade_dist"] == {}
    assert out["genre_dist"] == {}


# ============================================================
# TEK parça — tek elemanlı listede düzgün
# ============================================================

def test_given_single_when_split_by_genre_then_one_bucket():
    t = _track("s1")
    out = genre.split_by_genre([t], {"a_s1": ["pop"]})
    assert out == {"Pop": [t]}


def test_given_single_when_harmonic_order_then_same_single():
    t = _track("s1")
    assert order.harmonic_order([t]) == [t]


def test_given_single_when_dedupe_then_kept_one_removed_none():
    t = _track("s1")
    out = organize.dedupe([t])
    assert out["kept"] == [t]
    assert out["removed"] == []


def test_given_single_when_sort_tracks_then_same_single():
    t = _track("s1")
    assert organize.sort_tracks([t], [("popularity", "desc")]) == [t]


def test_given_single_when_merge_playlists_then_same_single():
    t = _track("s1")
    assert organize.merge_playlists([[t]]) == [t]


def test_given_single_when_split_by_decade_then_one_bucket():
    t = _track("s1", year=2020)
    assert organize.split_by_decade([t]) == {"2020'lar": [t]}


def test_given_single_when_split_by_tempo_then_one_band():
    t = _track("s1", bpm=120)
    assert organize.split_by_tempo([t]) == {organize.MEDIUM: [t]}


def test_given_single_when_split_by_size_then_one_chunk():
    t = _track("s1")
    assert organize.split_by_size([t], 5) == [[t]]


def test_given_single_when_insights_then_total_one():
    t = _track("s1", popularity=80)
    out = organize.insights([t])
    assert out["total"] == 1
    assert out["avg_popularity"] == 80.0
    assert out["top_artists"] == [[t["artist"], 1]]


# ============================================================
# HEPSİ bpm=None / camelot=None
# ============================================================

def test_given_all_camelot_none_when_harmonic_order_then_permutation_preserved():
    tracks = [_track("n1", bpm=None, camelot=None),
              _track("n2", bpm=None, camelot=None),
              _track("n3", bpm=None, camelot=None)]
    out = order.harmonic_order(tracks)
    # camelot yok → giriş sırası korunur, eleman kümesi aynı
    assert [t["id"] for t in out] == ["n1", "n2", "n3"]
    assert len(out) == len(tracks)


def test_given_all_bpm_none_when_split_by_tempo_then_all_unknown():
    tracks = [_track("n1", bpm=None), _track("n2", bpm=None)]
    out = organize.split_by_tempo(tracks)
    assert list(out.keys()) == [organize.UNKNOWN]
    assert len(out[organize.UNKNOWN]) == 2


def test_given_none_fields_when_enrich_with_no_fetch_then_untouched():
    tracks = [_track("n1", bpm=None, camelot=None)]
    out = enrich.enrich_tracks(tracks, fetch=None)
    assert out[0]["bpm"] is None
    assert out[0]["camelot"] is None
    # kopya döner, girişi mutasyona uğratmaz
    assert out is not tracks
    assert tracks[0]["bpm"] is None


# ============================================================
# split_by_size sınır halleri
# ============================================================

def test_given_size_larger_than_len_when_split_by_size_then_single_chunk():
    out = organize.split_by_size([1, 2, 3], 5)
    assert out == [[1, 2, 3]]


def test_given_zero_size_when_split_by_size_then_value_error():
    with pytest.raises(ValueError):
        organize.split_by_size([1, 2, 3], 0)


def test_given_negative_size_when_split_by_size_then_value_error():
    with pytest.raises(ValueError):
        organize.split_by_size([1, 2, 3], -2)


# ============================================================
# sort_tracks BİLİNMEYEN alan — mevcut davranış: net ValueError (ham KeyError DEĞİL)
# ============================================================

def test_given_unknown_field_when_sort_tracks_then_value_error_not_keyerror():
    tracks = [_track("s1"), _track("s2")]
    with pytest.raises(ValueError):
        organize.sort_tracks(tracks, [("foo", "asc")])


def test_given_unknown_direction_when_sort_tracks_then_value_error():
    tracks = [_track("s1")]
    with pytest.raises(ValueError):
        organize.sort_tracks(tracks, [("popularity", "sideways")])


# ============================================================
# service.restore EKSİK dosya — temiz FileNotFoundError
# ============================================================

def test_given_missing_backup_when_restore_then_file_not_found(tmp_path):
    s = _svc(tmp_path)
    with pytest.raises(FileNotFoundError):
        s.restore("olmayan-yedek.json")


# ============================================================
# service: boş/olmayan kaynak playlist — preview/insights patlamamalı
# ============================================================

def test_given_unknown_source_when_preview_split_genre_then_empty_groups(tmp_path):
    out = _svc(tmp_path).preview_split_genre("p_yok")
    assert out["groups"] == []


def test_given_unknown_source_when_insights_then_zeroed(tmp_path):
    out = _svc(tmp_path).insights("p_yok")
    assert out["total"] == 0
    assert out["genre_dist"] == {}


def test_given_unknown_source_when_preview_order_then_empty(tmp_path):
    assert _svc(tmp_path).preview_order("p_yok")["tracks"] == []


def test_given_unknown_source_when_preview_dedupe_then_empty(tmp_path):
    out = _svc(tmp_path).preview_dedupe("p_yok")
    assert out["kept"] == []
    assert out["removed_count"] == 0


def test_given_unknown_sources_when_preview_merge_then_empty(tmp_path):
    out = _svc(tmp_path).preview_merge(["p_yok", "p_hic"])
    assert out["tracks"] == []
    assert out["count"] == 0


def test_given_unknown_source_when_preview_split_size_then_empty_groups(tmp_path):
    out = _svc(tmp_path).preview_split("p_yok", "size", size=5)
    assert out["groups"] == []
