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


def test_service_gercek_modda_organizer_service_doner(monkeypatch):
    # Regresyon: gerçek mod ÇIPLAK SpotipyClient değil, OrganizerService dönmeli.
    monkeypatch.delenv("DEMO", raising=False)
    import spotipy
    from spotipy import oauth2
    monkeypatch.setattr(oauth2, "SpotifyOAuth", lambda **k: object())
    monkeypatch.setattr(spotipy, "Spotify", lambda **k: object())
    from spotify_organizer import app as appmod
    from spotify_organizer.service import OrganizerService
    assert isinstance(appmod._service(), OrganizerService)


def test_discover_apply_olusturur(client):
    res = _data(client.post("/api/discover/apply", json={"kind": "search", "query": "tarkan", "name": "T"}))
    assert res["created"][0]["count"] >= 1


def test_apply_yedek_yazar_ve_listelenir(client, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # backups/ tmp'ye düşsün
    res = _data(client.post("/api/split-genre/apply", json={"source": "liked"}))
    assert res["created"]
    bks = _data(client.get("/api/backups"))
    assert bks and bks[0]["count"] == 17


def test_rate_limit_dostça_mesaj(monkeypatch):
    # 429/rate-limit gelince ham hata değil net Türkçe mesaj + 429 kodu.
    monkeypatch.setenv("DEMO", "1")
    import spotify_organizer.app as appmod

    class Boom:
        client = object()
        def insights(self, source):
            raise Exception("http status: 429 - Your application has reached a rate/request limit")

    monkeypatch.setattr(appmod, "_service", lambda: Boom())
    r = appmod.app.test_client().get("/api/insights/liked")
    j = r.get_json()
    assert j["success"] is False and r.status_code == 429
    assert "limit" in j["error"].lower()


def test_gercek_mod_cachingclient_sarmalar(monkeypatch):
    # Regresyon: gerçek modda istemci CachingClient ile sarılmalı (rate-limit koruması).
    monkeypatch.delenv("DEMO", raising=False)
    import spotipy
    from spotipy import oauth2
    monkeypatch.setattr(oauth2, "SpotifyOAuth", lambda **k: object())
    monkeypatch.setattr(spotipy, "Spotify", lambda **k: object())
    import spotify_organizer.app as appmod
    from spotify_organizer.cache_layer import CachingClient
    svc = appmod._service()
    assert isinstance(svc.client, CachingClient)


# ---------- DJ Modu önizleme ucu (/api/preview) — Spotify'a dokunmaz, diske cache ----------

def test_preview_url_doner_ve_cacheler(client, monkeypatch, tmp_path):
    calls = {"n": 0}

    def fake_lookup(artist, title):
        calls["n"] += 1
        return "https://cdn.deezer.com/p.mp3"

    import spotify_organizer.app as appmod
    from spotify_organizer import audio_bpm
    monkeypatch.setattr(audio_bpm, "preview_lookup", fake_lookup)
    monkeypatch.setattr(appmod, "_PREVIEW_CACHE", str(tmp_path / "previews.json"))

    r1 = client.get("/api/preview?artist=A%24AP%20Ferg&title=Plain%20Jane")
    assert _data(r1)["url"] == "https://cdn.deezer.com/p.mp3"
    # ikinci çağrı cache'ten gelir → lookup TEKRAR çağrılmaz
    r2 = client.get("/api/preview?artist=A%24AP%20Ferg&title=Plain%20Jane")
    assert _data(r2)["url"] == "https://cdn.deezer.com/p.mp3"
    assert calls["n"] == 1


def test_preview_bos_param_400(client):
    r = client.get("/api/preview")
    assert r.status_code == 400
    assert r.get_json()["success"] is False


def test_preview_lookup_deezer_sonra_itunes(monkeypatch):
    from spotify_organizer import audio_bpm
    # Deezer önizleme verir → onu döndürür
    monkeypatch.setattr(audio_bpm, "_deezer_search_one", lambda q: {"preview": "http://dz.mp3"})
    assert audio_bpm.preview_lookup("X", "Y") == "http://dz.mp3"
    # Deezer boş → iTunes yedeğe düşer
    monkeypatch.setattr(audio_bpm, "_deezer_search_one", lambda q: None)
    monkeypatch.setattr(audio_bpm, "itunes_preview", lambda a, t: "http://it.mp3")
    assert audio_bpm.preview_lookup("X", "Y") == "http://it.mp3"
