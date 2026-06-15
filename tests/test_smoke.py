"""Harness duman testi — MockClient sözleşmeyi karşılıyor mu."""
from spotify_organizer.client import SpotifyClient
from tests.mock_client import MockClient


def test_mock_satisfies_protocol():
    assert isinstance(MockClient(), SpotifyClient)


def test_mock_reads_fixtures():
    c = MockClient()
    assert c.playlist_tracks("p_liked"), "Beğenilenler dolu olmalı"
    assert c.playlists(), "playlist özeti dolu olmalı"
    # kopya döndüğünü doğrula (fixtures bozulmasın)
    t = c.playlist_tracks("p_liked")[0]
    t["title"] = "BOZULDU"
    assert c.playlist_tracks("p_liked")[0]["title"] != "BOZULDU"


def test_mock_records_mutations():
    c = MockClient()
    res = c.create_playlist("Test", ["spotify:track:t01"])
    assert res["id"] and c.created[0]["name"] == "Test"
