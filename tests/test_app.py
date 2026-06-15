"""F2 endpoint testleri — DEMO=1 ile zarf ({success,data,error}) + uçtan uca akış."""
import pytest


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DEMO", "1")
    from spotify_organizer.app import app
    app.config["TESTING"] = True
    return app.test_client()


def _data(r):
    j = r.get_json()
    assert j["success"] is True, j.get("error")
    return j["data"]


def test_me_demo(client):
    assert client.get("/api/me").get_json()["demo"] is True


def test_playlists_ve_playlist(client):
    assert _data(client.get("/api/playlists"))
    pl = _data(client.get("/api/playlist/p_liked"))
    assert pl["tracks"] and pl["name"] == "Beğenilenler"


def test_playlist_bulunamadi(client):
    r = client.get("/api/playlist/yok")
    assert r.get_json()["success"] is False


def test_split_genre_preview(client):
    d = _data(client.post("/api/split-genre/preview", json={"source": "liked"}))
    assert d["groups"]


def test_order_preview(client):
    d = _data(client.post("/api/order/preview", json={"source": "liked"}))
    assert len(d["tracks"]) == 17


def test_dedupe_preview(client):
    d = _data(client.post("/api/dedupe/preview", json={"source": "p_yaz"}))
    assert "removed_count" in d


def test_sort_preview(client):
    d = _data(client.post("/api/sort/preview",
                          json={"source": "liked", "keys": [["popularity", "desc"]]}))
    pops = [t["popularity"] for t in d["tracks"]]
    assert pops == sorted(pops, reverse=True)


def test_merge_split_preview(client):
    assert _data(client.post("/api/merge/preview", json={"sources": ["p_yaz", "p_spor"]}))["tracks"]
    assert _data(client.post("/api/split/preview", json={"source": "liked", "by": "decade"}))["groups"]


def test_insights(client):
    d = _data(client.get("/api/insights/liked"))
    assert d["genre_dist"] and d["total"] == 17


def test_top_ve_search(client):
    assert _data(client.get("/api/top"))["tracks"]
    hits = _data(client.post("/api/search", json={"query": "tarkan"}))["tracks"]
    assert any("Tarkan" in t["artist"] for t in hits)


def test_discover_apply_olusturur(client):
    res = _data(client.post("/api/discover/apply", json={"kind": "search", "query": "tarkan", "name": "T"}))
    assert res["created"][0]["count"] >= 1


def test_apply_yedek_yazar_ve_listelenir(client, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # backups/ tmp'ye düşsün
    res = _data(client.post("/api/split-genre/apply", json={"source": "liked"}))
    assert res["created"]
    bks = _data(client.get("/api/backups"))
    assert bks and bks[0]["count"] == 17
