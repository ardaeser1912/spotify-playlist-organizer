"""SpotipyClient (gerçek istemci) testleri — sahte spotipy nesnesiyle, ağ/auth YOK.

En kritik eksikti: SpotipyClient şu ana dek SIFIR test'liydi (DEMO yolu DemoClient
kullanıyor, gerçek yol hiç çalışmıyordu). Burada `FakeSpotify` spotipy-şekilli cevaplar
döndürür VE çağrı argümanlarını (özellikle add/replace/create) kaydeder ki yazma
batch'lemesi doğrulanabilsin.
"""
from spotify_organizer.client import SpotipyClient, _normalize_track

_MISSING = object()  # "saved_total verilmedi" işareti → cevap 'total' içermez


# --- spotipy-şekilli yardımcılar ---------------------------------------------

def _sp_track(tid, name="Şarkı", artist_id="a1", artist_name="Sanatçı",
              release_date="2019-05-01", duration_ms=200_000, popularity=50,
              uri=None, ttype="track", album=True):
    """Tek bir spotipy track objesi üretir."""
    t = {
        "id": tid,
        "name": name,
        "artists": [{"id": artist_id, "name": artist_name}],
        "duration_ms": duration_ms,
        "popularity": popularity,
        "type": ttype,
    }
    if album:
        t["album"] = {"release_date": release_date}
    if uri is not None:
        t["uri"] = uri
    else:
        t["uri"] = f"spotify:track:{tid}"
    return t


def _page(items, next_url=None):
    """spotipy sayfalı cevabı: {items, next}."""
    return {"items": list(items), "next": next_url}


class FakeSpotify:
    """spotipy.Spotify yerine geçen sahte. Cevapları konfigüre edilir, çağrılar kaydedilir."""

    def __init__(self, **responses):
        # Önceden ayarlanmış cevaplar
        self._user = responses.get("user", {"id": "u1", "display_name": "Şef"})
        self._pages = responses.get("pages", {})          # method adı -> [page, page, ...]
        # Beğenilenler toplamı: playlists() bunu current_user_saved_tracks(limit=1).total'dan okur.
        # _MISSING = anahtar verilmedi → cevap 'total' içermesin (savunmacı None yolu).
        self._saved_total = responses.get("saved_total", _MISSING)
        self._artists_pages = responses.get("artists", [])  # her artists() çağrısı için sıralı cevap
        self._top_tracks = responses.get("top_tracks", {"items": []})
        self._top_artists = responses.get("top_artists", {"items": []})
        self._search = responses.get("search", {"tracks": {"items": []}})
        self._create_result = responses.get("create_result", {"id": "new_pl", "name": "Yeni"})

        # Çağrı kayıtları
        self.calls = []                    # (method, args, kwargs)
        self.next_calls = []               # next() çağrılarında verilen page
        self.added = []                    # (playlist_id, uris) playlist_add_items
        self.replaced = []                 # (playlist_id, uris) playlist_replace_items
        self.created = []                  # (uid, name, kwargs) user_playlist_create
        self.artists_calls = []            # her artists() çağrısına geçen id listesi
        self._page_index = {}              # method -> hangi sayfadayız

    def _record(self, method, *args, **kwargs):
        self.calls.append((method, args, kwargs))

    # --- okuma ---
    def current_user(self):
        self._record("current_user")
        return self._user

    def _first_page(self, method):
        pages = self._pages.get(method, [_page([])])
        self._page_index[method] = pages
        # ilk sayfayı döndür; sonraki sayfalar next() ile gelir
        return pages[0] if pages else _page([])

    def current_user_playlists(self, limit=50):
        self._record("current_user_playlists", limit=limit)
        return self._first_page("current_user_playlists")

    def playlist_items(self, playlist_id, limit=100, additional_types=None):
        self._record("playlist_items", playlist_id, limit=limit,
                     additional_types=additional_types)
        return self._first_page("playlist_items")

    def current_user_saved_tracks(self, limit=50):
        self._record("current_user_saved_tracks", limit=limit)
        page = self._first_page("current_user_saved_tracks")
        if self._saved_total is not _MISSING:
            # total alanını ilk sayfaya yaz (playlists() limit=1 ile bunu okur).
            # next() kimlik karşılaştırması bozulmasın diye orijinal nesneyi mutasyona uğrat.
            page["total"] = self._saved_total
        return page

    def next(self, page):
        """spotipy.next(page) — kayıtlı sayfa zincirinde bir sonrakini döndürür."""
        self.next_calls.append(page)
        # page hangi method'a aitse o zincirde sonrakini bul
        for method, pages in self._page_index.items():
            for i, p in enumerate(pages):
                if p is page and i + 1 < len(pages):
                    return pages[i + 1]
        return None

    def artists(self, ids):
        self._record("artists", ids)
        self.artists_calls.append(list(ids))
        idx = len(self.artists_calls) - 1
        if idx < len(self._artists_pages):
            return self._artists_pages[idx]
        return {"artists": []}

    def current_user_top_tracks(self, limit=20):
        self._record("current_user_top_tracks", limit=limit)
        return self._top_tracks

    def current_user_top_artists(self, limit=20):
        self._record("current_user_top_artists", limit=limit)
        return self._top_artists

    def search(self, q=None, type=None, limit=20):
        self._record("search", q=q, type=type, limit=limit)
        return self._search

    # --- yazma ---
    def user_playlist_create(self, uid, name, public=True, description=""):
        self._record("user_playlist_create", uid, name, public=public,
                     description=description)
        self.created.append((uid, name, {"public": public, "description": description}))
        return self._create_result

    def playlist_add_items(self, playlist_id, items):
        self._record("playlist_add_items", playlist_id, items)
        self.added.append((playlist_id, list(items)))

    def playlist_replace_items(self, playlist_id, items):
        self._record("playlist_replace_items", playlist_id, items)
        self.replaced.append((playlist_id, list(items)))


def _called(fake, method):
    """Belirli bir method kaç kez çağrıldı."""
    return sum(1 for m, _a, _k in fake.calls if m == method)


# =============================================================================
# _normalize_track — happy
# =============================================================================

def test_normalize_full_track_happy():
    src = _sp_track("t01", name="Gece", artist_id="a9", artist_name="DJ",
                    release_date="2019-05-01", duration_ms=210_000, popularity=77,
                    uri="spotify:track:t01")
    out = _normalize_track(src)
    assert out == {
        "id": "t01",
        "title": "Gece",
        "artist": "DJ",
        "artist_id": "a9",
        "uri": "spotify:track:t01",
        "duration_ms": 210_000,
        "bpm": None,
        "camelot": None,
        "year": 2019,
        "popularity": 77,
        "image": None,
    }


def test_normalize_album_kapagi_secer():
    # album.images içinden ~300px tercih edilir; yoksa ilk (en büyük).
    src = _sp_track("t1")
    src["album"]["images"] = [
        {"url": "big", "width": 640}, {"url": "mid", "width": 300}, {"url": "sm", "width": 64}]
    assert _normalize_track(src)["image"] == "mid"
    src["album"]["images"] = [{"url": "only", "width": 640}]
    assert _normalize_track(src)["image"] == "only"
    src["album"]["images"] = []
    assert _normalize_track(src)["image"] is None


def test_normalize_year_full_date():
    out = _normalize_track(_sp_track("t1", release_date="2019-05-01"))
    assert out["year"] == 2019


def test_normalize_year_only_year_string():
    out = _normalize_track(_sp_track("t1", release_date="1997"))
    assert out["year"] == 1997


def test_normalize_bpm_camelot_always_none():
    out = _normalize_track(_sp_track("t1"))
    assert out["bpm"] is None and out["camelot"] is None


# =============================================================================
# _normalize_track — edge
# =============================================================================

def test_normalize_empty_release_date_year_none():
    out = _normalize_track(_sp_track("t1", release_date=""))
    assert out["year"] is None


def test_normalize_missing_album_year_none():
    out = _normalize_track(_sp_track("t1", album=False))
    assert out["year"] is None


def test_normalize_uri_derived_when_missing():
    src = _sp_track("t42", uri=None)
    del src["uri"]  # uri anahtarını tamamen kaldır
    out = _normalize_track(src)
    assert out["uri"] == "spotify:track:t42"


def test_normalize_episode_returns_none():
    out = _normalize_track(_sp_track("e1", ttype="episode"))
    assert out is None


def test_normalize_missing_id_returns_none():
    src = _sp_track("t1")
    del src["id"]
    assert _normalize_track(src) is None


def test_normalize_none_item_returns_none():
    assert _normalize_track(None) is None
    assert _normalize_track({}) is None


# =============================================================================
# _paginate (playlists üzerinden) — ikinci sayfa toplanır
# =============================================================================

def test_paginate_collects_second_page():
    p1 = _page([{"id": "pl1", "name": "A", "tracks": {"total": 3}}], next_url="url://p2")
    p2 = _page([{"id": "pl2", "name": "B", "tracks": {"total": 5}}], next_url=None)
    fake = FakeSpotify(pages={"current_user_playlists": [p1, p2]})
    client = SpotipyClient(fake)
    res = client.playlists()
    # Beğenilenler sözde-listesi başta, ardından gerçek listeler.
    assert [p["id"] for p in res] == ["liked", "pl1", "pl2"]
    # next() ilk sayfa için (next dolu) tam 1 kez çağrılmalı
    assert len(fake.next_calls) == 1
    assert fake.next_calls[0] is p1


def test_paginate_single_page_no_next_call():
    p1 = _page([{"id": "pl1", "name": "A", "tracks": {"total": 1}}], next_url=None)
    fake = FakeSpotify(pages={"current_user_playlists": [p1]})
    client = SpotipyClient(fake)
    client.playlists()
    assert fake.next_calls == []


# =============================================================================
# playlists
# =============================================================================

def test_playlists_maps_track_count():
    p1 = _page([
        {"id": "pl1", "name": "Sabah", "tracks": {"total": 12}},
        {"id": "pl2", "name": "Akşam", "tracks": {"total": 0}},
    ])
    fake = FakeSpotify(pages={"current_user_playlists": [p1]}, saved_total=979)
    res = SpotipyClient(fake).playlists()
    assert res == [
        {"id": "liked", "name": "Beğenilenler", "track_count": 979},
        {"id": "pl1", "name": "Sabah", "track_count": 12},
        {"id": "pl2", "name": "Akşam", "track_count": 0},
    ]


def test_playlists_real_world_quirks():
    # Gerçek API (canlı hesapla yakalandı): takip edilen listelerde tracks=None,
    # bazı öğeler None, isim eksik olabilir. track_count yanlış 0 değil, None olmalı.
    p1 = _page([
        {"id": "pl1", "name": "Takip Edilen", "tracks": None},          # bilinmeyen sayı
        {"id": "pl2", "name": "Eksik Tracks"},                          # 'tracks' anahtarı yok
        None,                                                           # null öğe → atlanır
        {"id": "pl3", "tracks": {"total": 7}},                          # isim yok
        {"name": "ID yok"},                                            # id yok → atlanır
    ])
    fake = FakeSpotify(pages={"current_user_playlists": [p1]})
    res = SpotipyClient(fake).playlists()
    assert res == [
        # saved_total verilmedi → savunmacı None
        {"id": "liked", "name": "Beğenilenler", "track_count": None},
        {"id": "pl1", "name": "Takip Edilen", "track_count": None},
        {"id": "pl2", "name": "Eksik Tracks", "track_count": None},
        {"id": "pl3", "name": "(isimsiz)", "track_count": 7},
    ]


def test_playlists_liked_pseudo_first_with_total():
    # Beğenilenler her zaman ilk öğe; track_count = saved tracks toplamı.
    p1 = _page([{"id": "pl1", "name": "Sabah", "tracks": {"total": 3}}])
    fake = FakeSpotify(pages={"current_user_playlists": [p1]}, saved_total=979)
    res = SpotipyClient(fake).playlists()
    assert res[0] == {"id": "liked", "name": "Beğenilenler", "track_count": 979}
    # toplam yalnızca limit=1 ile (sayfalama değil) sorgulanmalı
    call = next(c for c in fake.calls if c[0] == "current_user_saved_tracks")
    assert call[2]["limit"] == 1


def test_playlists_liked_total_none_when_missing():
    # saved tracks 'total' içermezse savunmacı None (UI '—' gösterir).
    p1 = _page([{"id": "pl1", "name": "Sabah", "tracks": {"total": 3}}])
    fake = FakeSpotify(pages={"current_user_playlists": [p1]})  # saved_total verilmedi
    res = SpotipyClient(fake).playlists()
    assert res[0] == {"id": "liked", "name": "Beğenilenler", "track_count": None}


# =============================================================================
# playlist_tracks — episode/None atlanır + additional_types doğrulama
# =============================================================================

def test_playlist_tracks_skips_episode_and_none():
    p1 = _page([
        {"track": _sp_track("t1", name="İyi")},
        {"track": _sp_track("e1", ttype="episode")},  # atlanır
        {"track": None},                               # atlanır
    ])
    fake = FakeSpotify(pages={"playlist_items": [p1]})
    res = SpotipyClient(fake).playlist_tracks("pReal")
    assert [t["id"] for t in res] == ["t1"]


def test_playlist_tracks_passes_additional_types():
    p1 = _page([{"track": _sp_track("t1")}])
    fake = FakeSpotify(pages={"playlist_items": [p1]})
    SpotipyClient(fake).playlist_tracks("pX")
    call = next(c for c in fake.calls if c[0] == "playlist_items")
    assert call[1][0] == "pX"                        # playlist_id pozisyonel
    assert call[2]["additional_types"] == ("track",)
    assert call[2]["limit"] == 100


# =============================================================================
# liked_tracks
# =============================================================================

def test_liked_tracks_normalizes():
    p1 = _page([
        {"track": _sp_track("t1", name="A")},
        {"track": _sp_track("t2", name="B")},
    ])
    fake = FakeSpotify(pages={"current_user_saved_tracks": [p1]})
    res = SpotipyClient(fake).liked_tracks()
    assert [t["title"] for t in res] == ["A", "B"]
    assert _called(fake, "current_user_saved_tracks") == 1


def test_liked_tracks_empty():
    fake = FakeSpotify(pages={"current_user_saved_tracks": [_page([])]})
    assert SpotipyClient(fake).liked_tracks() == []


def test_playlist_tracks_liked_id_returns_liked_tracks():
    # "liked" gerçek playlist değil → saved tracks normalize edilip döner.
    p1 = _page([{"track": _sp_track("t1", name="A")},
                {"track": _sp_track("t2", name="B")}])
    fake = FakeSpotify(pages={"current_user_saved_tracks": [p1]})
    res = SpotipyClient(fake).playlist_tracks("liked")
    assert [t["title"] for t in res] == ["A", "B"]
    # playlist_items'a hiç gidilmemeli
    assert _called(fake, "playlist_items") == 0


def test_playlist_tracks_p_liked_id_returns_liked_tracks():
    # DEMO/legacy "p_liked" id'si de aynı saved tracks yoluna düşer.
    p1 = _page([{"track": _sp_track("t1", name="A")}])
    fake = FakeSpotify(pages={"current_user_saved_tracks": [p1]})
    res = SpotipyClient(fake).playlist_tracks("p_liked")
    assert [t["title"] for t in res] == ["A"]
    assert _called(fake, "playlist_items") == 0


# =============================================================================
# artist_genres — 120 sanatçı → 3 batch, tekrarsız, boş id atlanır
# =============================================================================

def test_artist_genres_three_batches_of_fifty():
    ids = [f"a{i}" for i in range(120)]
    # her batch'e cevap: artists içinde ilgili id'lerle genres
    pages = []
    for start in (0, 50, 100):
        chunk = ids[start:start + 50]
        pages.append({"artists": [{"id": a, "genres": ["pop"]} for a in chunk]})
    fake = FakeSpotify(artists=pages)
    res = SpotipyClient(fake).artist_genres(ids)
    # artists() tam 3 kez (50+50+20)
    assert _called(fake, "artists") == 3
    assert [len(c) for c in fake.artists_calls] == [50, 50, 20]
    assert len(res) == 120
    assert res["a0"] == ["pop"]


def test_artist_genres_dedup_preserves_order():
    ids = ["a1", "a2", "a1", "a3", "a2"]  # a1, a2 tekrar
    pages = [{"artists": [{"id": "a1", "genres": ["rock"]},
                          {"id": "a2", "genres": ["jazz"]},
                          {"id": "a3", "genres": []}]}]
    fake = FakeSpotify(artists=pages)
    SpotipyClient(fake).artist_genres(ids)
    # tekrarsız ve giriş sırasını korur (dict.fromkeys)
    assert fake.artists_calls[0] == ["a1", "a2", "a3"]


def test_artist_genres_skips_empty_ids():
    ids = ["a1", "", None, "a2"]
    pages = [{"artists": [{"id": "a1", "genres": []}, {"id": "a2", "genres": ["pop"]}]}]
    fake = FakeSpotify(artists=pages)
    SpotipyClient(fake).artist_genres(ids)
    assert fake.artists_calls[0] == ["a1", "a2"]


def test_artist_genres_returns_dict():
    pages = [{"artists": [{"id": "a1", "genres": ["pop", "dance"]}]}]
    fake = FakeSpotify(artists=pages)
    res = SpotipyClient(fake).artist_genres(["a1"])
    assert res == {"a1": ["pop", "dance"]}


def test_artist_genres_403_olunca_zarif_atlar():
    # Gerçek: Spotify Development-mode /artists 403 döndürüyor → batch atlanır, çökme yok.
    fake = FakeSpotify(artists=[])

    def boom(ids):
        raise Exception("http status: 403 Forbidden")

    fake.artists = boom
    res = SpotipyClient(fake).artist_genres(["a1", "a2"])
    assert res == {}  # tür bilgisi yok ama panel çökmedi


# =============================================================================
# top_tracks / top_artists
# =============================================================================

def test_top_tracks_normalizes():
    fake = FakeSpotify(top_tracks={"items": [_sp_track("t1", name="Top1"),
                                             _sp_track("t2", name="Top2")]})
    res = SpotipyClient(fake).top_tracks(limit=10)
    assert [t["title"] for t in res] == ["Top1", "Top2"]
    call = next(c for c in fake.calls if c[0] == "current_user_top_tracks")
    assert call[2]["limit"] == 10


def test_top_tracks_skips_episode():
    fake = FakeSpotify(top_tracks={"items": [_sp_track("t1"),
                                             _sp_track("e1", ttype="episode")]})
    assert len(SpotipyClient(fake).top_tracks()) == 1


def test_top_artists_maps_id_name_genres():
    fake = FakeSpotify(top_artists={"items": [
        {"id": "a1", "name": "Sanatçı1", "genres": ["pop"]},
        {"id": "a2", "name": "Sanatçı2", "genres": []},
    ]})
    res = SpotipyClient(fake).top_artists()
    assert res == [
        {"id": "a1", "name": "Sanatçı1", "genres": ["pop"]},
        {"id": "a2", "name": "Sanatçı2", "genres": []},
    ]


# =============================================================================
# search_tracks — q + type="track" doğrulama
# =============================================================================

def test_search_tracks_normalizes_and_passes_query():
    fake = FakeSpotify(search={"tracks": {"items": [_sp_track("t1", name="Bulundu")]}})
    res = SpotipyClient(fake).search_tracks("daft punk", limit=5)
    assert [t["title"] for t in res] == ["Bulundu"]
    call = next(c for c in fake.calls if c[0] == "search")
    assert call[2]["q"] == "daft punk"
    assert call[2]["type"] == "track"
    assert call[2]["limit"] == 5


def test_search_tracks_empty_results():
    fake = FakeSpotify(search={"tracks": {"items": []}})
    assert SpotipyClient(fake).search_tracks("yok") == []


# =============================================================================
# create_playlist — 250 uri → create 1x + add 3x (100+100+50)
# =============================================================================

def test_create_playlist_batches_250_uris():
    uris = [f"spotify:track:t{i}" for i in range(250)]
    fake = FakeSpotify(create_result={"id": "pl_new", "name": "Karışım"})
    res = SpotipyClient(fake).create_playlist("Karışım", uris, description="açıklama")

    # user_playlist_create tam 1 kez, public=False, doğru ad + açıklama
    assert _called(fake, "user_playlist_create") == 1
    uid, name, kw = fake.created[0]
    assert uid == "u1" and name == "Karışım"
    assert kw["public"] is False and kw["description"] == "açıklama"

    # playlist_add_items 3 kez: 100 + 100 + 50, doğru uri dilimleriyle
    assert len(fake.added) == 3
    assert [len(items) for _pid, items in fake.added] == [100, 100, 50]
    assert fake.added[0][1] == uris[:100]
    assert fake.added[1][1] == uris[100:200]
    assert fake.added[2][1] == uris[200:250]
    # hepsi yeni playlist'e eklendi
    assert all(pid == "pl_new" for pid, _ in fake.added)

    assert res == {"id": "pl_new", "name": "Karışım"}


def test_create_playlist_empty_uris_no_add():
    fake = FakeSpotify(create_result={"id": "pl_new", "name": "Boş"})
    res = SpotipyClient(fake).create_playlist("Boş", [])
    assert _called(fake, "user_playlist_create") == 1
    assert fake.added == []
    assert res == {"id": "pl_new", "name": "Boş"}


# =============================================================================
# add_tracks — 100'lük batch
# =============================================================================

def test_add_tracks_batches_by_100():
    uris = [f"spotify:track:t{i}" for i in range(205)]
    fake = FakeSpotify()
    SpotipyClient(fake).add_tracks("pX", uris)
    assert [len(items) for _pid, items in fake.added] == [100, 100, 5]
    assert all(pid == "pX" for pid, _ in fake.added)
    assert fake.added[2][1] == uris[200:205]


def test_add_tracks_under_100_single_call():
    uris = [f"spotify:track:t{i}" for i in range(30)]
    fake = FakeSpotify()
    SpotipyClient(fake).add_tracks("pX", uris)
    assert len(fake.added) == 1 and len(fake.added[0][1]) == 30


def test_add_tracks_empty_no_call():
    fake = FakeSpotify()
    SpotipyClient(fake).add_tracks("pX", [])
    assert fake.added == []


# =============================================================================
# replace_tracks — ilk 100 replace, kalanı add
# =============================================================================

def test_replace_tracks_first_100_replace_rest_add():
    uris = [f"spotify:track:t{i}" for i in range(250)]
    fake = FakeSpotify()
    SpotipyClient(fake).replace_tracks("pX", uris)

    # tek replace çağrısı, ilk 100
    assert len(fake.replaced) == 1
    pid, items = fake.replaced[0]
    assert pid == "pX" and items == uris[:100]

    # kalan 150 → add 2 kez (100 + 50)
    assert [len(it) for _pid, it in fake.added] == [100, 50]
    assert fake.added[0][1] == uris[100:200]
    assert fake.added[1][1] == uris[200:250]


def test_replace_tracks_under_100_only_replace():
    uris = [f"spotify:track:t{i}" for i in range(40)]
    fake = FakeSpotify()
    SpotipyClient(fake).replace_tracks("pX", uris)
    assert len(fake.replaced) == 1 and fake.replaced[0][1] == uris
    assert fake.added == []


def test_replace_tracks_empty_replaces_empty():
    fake = FakeSpotify()
    SpotipyClient(fake).replace_tracks("pX", [])
    assert fake.replaced == [("pX", [])]
    assert fake.added == []


# =============================================================================
# current_user
# =============================================================================

def test_current_user_maps_id_and_display_name():
    fake = FakeSpotify(user={"id": "u1", "display_name": "Şef"})
    assert SpotipyClient(fake).current_user() == {"id": "u1", "display_name": "Şef"}


def test_current_user_falls_back_to_id_when_no_display_name():
    fake = FakeSpotify(user={"id": "u1", "display_name": None})
    assert SpotipyClient(fake).current_user() == {"id": "u1", "display_name": "u1"}
