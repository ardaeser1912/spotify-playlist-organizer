"""CachingClient testleri — AĞSIZ. Sahte client çağrıları sayar; disk tmp_path ile izole.

Doğrulanan davranış:
- Pahalı okumalar (liked/playlists/playlist_tracks) cache'lenir → tekrar çağrıda client'a gitmez.
- TTL=0 → her seferinde yeniden çeker (cache bayat).
- Farklı pid ayrı anahtara cache'lenir.
- Ucuz/değişken okumalar (artist_genres/top_*/search) her çağrıda delege edilir (cache yok).
- Yazma metotları delege eder + cache'i temizler → sonraki okuma client'tan yeniden çekilir.
- clear() sonrası yeniden çeker. Bozuk/eksik cache dosyası çökmez. isinstance Protocol True.
"""
import json

import pytest

from spotify_organizer.cache_layer import CachingClient
from spotify_organizer.client import SpotifyClient


class FakeClient:
    """Çağrıları sayan ağsız sahte client (SpotifyClient sözleşmesini karşılar)."""

    def __init__(self):
        self.calls: dict[str, int] = {}

    def _hit(self, name):
        self.calls[name] = self.calls.get(name, 0) + 1

    def current_user(self):
        self._hit("current_user")
        return {"id": "u1", "display_name": "Şef"}

    def playlists(self):
        self._hit("playlists")
        return [{"id": "liked", "name": "Beğenilenler", "track_count": 979}]

    def playlist_tracks(self, playlist_id):
        self._hit("playlist_tracks")
        return [{"id": f"{playlist_id}_t1", "title": "x"}]

    def liked_tracks(self):
        self._hit("liked_tracks")
        return [{"id": "t1", "title": "A"}, {"id": "t2", "title": "B"}]

    def artist_genres(self, artist_ids):
        self._hit("artist_genres")
        return {a: ["pop"] for a in artist_ids}

    def top_tracks(self, limit=20):
        self._hit("top_tracks")
        return [{"id": "tt1"}]

    def top_artists(self, limit=20):
        self._hit("top_artists")
        return [{"id": "ta1", "name": "X", "genres": []}]

    def search_tracks(self, query, limit=20):
        self._hit("search_tracks")
        return [{"id": "s1"}]

    def create_playlist(self, name, track_uris, description=""):
        self._hit("create_playlist")
        return {"id": "new", "name": name}

    def add_tracks(self, playlist_id, track_uris):
        self._hit("add_tracks")

    def replace_tracks(self, playlist_id, track_uris):
        self._hit("replace_tracks")


@pytest.fixture
def cache_file(tmp_path):
    return str(tmp_path / "sub" / "spotify_data.json")  # 'sub' yok → dizin oluşturma da test edilir


def _wrap(client, cache_file, ttl=1800):
    return CachingClient(client, cache_path=cache_file, ttl_seconds=ttl)


# --- cache temel davranışı ---

def test_liked_tracks_cached_client_called_once(cache_file):
    fake = FakeClient()
    cc = _wrap(fake, cache_file)
    first = cc.liked_tracks()
    second = cc.liked_tracks()
    assert first == second
    assert fake.calls.get("liked_tracks") == 1  # ikinci çağrı cache'ten


def test_cache_persists_to_disk(cache_file):
    fake = FakeClient()
    _wrap(fake, cache_file).liked_tracks()
    with open(cache_file, encoding="utf-8") as f:
        disk = json.load(f)
    assert "liked" in disk and disk["liked"]["data"][0]["id"] == "t1"


def test_ttl_zero_refetches_every_time(cache_file):
    fake = FakeClient()
    cc = _wrap(fake, cache_file, ttl=0)
    cc.liked_tracks()
    cc.liked_tracks()
    assert fake.calls.get("liked_tracks") == 2  # bayat → her seferinde yeniden


def test_playlists_and_tracks_separate_keys(cache_file):
    fake = FakeClient()
    cc = _wrap(fake, cache_file)
    cc.playlists()
    cc.playlists()
    cc.playlist_tracks("p1")
    cc.playlist_tracks("p1")
    assert fake.calls.get("playlists") == 1
    assert fake.calls.get("playlist_tracks") == 1


def test_different_pid_different_cache(cache_file):
    fake = FakeClient()
    cc = _wrap(fake, cache_file)
    r1 = cc.playlist_tracks("p1")
    r2 = cc.playlist_tracks("p2")
    assert r1 != r2
    assert fake.calls.get("playlist_tracks") == 2  # ayrı pid → ayrı anahtar, iki gerçek çağrı
    assert cc.playlist_tracks("p1") == r1
    assert fake.calls.get("playlist_tracks") == 2  # p1 tekrar cache'ten


# --- delege edilen okumalar (cache YOK) ---

def test_delegated_reads_not_cached(cache_file):
    fake = FakeClient()
    cc = _wrap(fake, cache_file)
    cc.artist_genres(["a1"]); cc.artist_genres(["a1"])
    cc.top_tracks(); cc.top_tracks()
    cc.top_artists(); cc.top_artists()
    cc.search_tracks("q"); cc.search_tracks("q")
    cc.current_user(); cc.current_user()
    assert fake.calls.get("artist_genres") == 2
    assert fake.calls.get("top_tracks") == 2
    assert fake.calls.get("top_artists") == 2
    assert fake.calls.get("search_tracks") == 2
    assert fake.calls.get("current_user") == 2


def test_delegated_reads_pass_args(cache_file):
    fake = FakeClient()
    cc = _wrap(fake, cache_file)
    assert cc.artist_genres(["a1", "a2"]) == {"a1": ["pop"], "a2": ["pop"]}
    assert cc.top_tracks(5) == [{"id": "tt1"}]
    assert cc.search_tracks("q", 3) == [{"id": "s1"}]


# --- yazma metotları: delege + cache temizle ---

def test_create_playlist_delegates_and_invalidates(cache_file):
    fake = FakeClient()
    cc = _wrap(fake, cache_file)
    cc.liked_tracks()                       # cache'le
    assert fake.calls.get("liked_tracks") == 1
    res = cc.create_playlist("Yeni", ["spotify:track:t1"])
    assert res == {"id": "new", "name": "Yeni"}
    assert fake.calls.get("create_playlist") == 1
    cc.liked_tracks()                       # cache temizlendi → yeniden çek
    assert fake.calls.get("liked_tracks") == 2


def test_add_tracks_invalidates_cache(cache_file):
    fake = FakeClient()
    cc = _wrap(fake, cache_file)
    cc.playlists()
    cc.add_tracks("p1", ["spotify:track:t1"])
    assert fake.calls.get("add_tracks") == 1
    cc.playlists()
    assert fake.calls.get("playlists") == 2  # yazma sonrası bayat değil, yeniden


def test_replace_tracks_invalidates_cache(cache_file):
    fake = FakeClient()
    cc = _wrap(fake, cache_file)
    cc.playlist_tracks("p1")
    cc.replace_tracks("p1", ["spotify:track:t1"])
    assert fake.calls.get("replace_tracks") == 1
    cc.playlist_tracks("p1")
    assert fake.calls.get("playlist_tracks") == 2


# --- clear / dayanıklılık ---

def test_clear_refetches(cache_file):
    fake = FakeClient()
    cc = _wrap(fake, cache_file)
    cc.liked_tracks()
    cc.clear()
    cc.liked_tracks()
    assert fake.calls.get("liked_tracks") == 2


def test_missing_cache_file_no_crash(cache_file):
    fake = FakeClient()
    cc = _wrap(fake, cache_file)  # dosya yok
    assert cc.liked_tracks()      # çökmeden çalışır


def test_corrupt_cache_file_no_crash(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{bozuk json ::::", encoding="utf-8")
    fake = FakeClient()
    cc = CachingClient(fake, cache_path=str(bad), ttl_seconds=1800)
    assert cc.liked_tracks()  # bozuk → boş başla, çökme yok
    assert fake.calls.get("liked_tracks") == 1


def test_loads_existing_disk_cache_no_client_call(cache_file):
    # Önceki oturum cache yazmış olsun → yeni örnek client'a gitmeden okur.
    fake1 = FakeClient()
    CachingClient(fake1, cache_path=cache_file, ttl_seconds=1800).liked_tracks()
    fake2 = FakeClient()
    cc2 = CachingClient(fake2, cache_path=cache_file, ttl_seconds=1800)
    assert cc2.liked_tracks() == [{"id": "t1", "title": "A"}, {"id": "t2", "title": "B"}]
    assert fake2.calls.get("liked_tracks") is None  # disk taze → client hiç çağrılmadı


def test_isinstance_protocol(cache_file):
    cc = _wrap(FakeClient(), cache_file)
    assert isinstance(cc, SpotifyClient)
