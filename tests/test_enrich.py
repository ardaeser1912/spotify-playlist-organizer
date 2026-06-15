"""enrich.enrich_tracks + cache + open_key_to_camelot testleri (happy + edge).

GERÇEK AĞ YOK — sahte (fake) fetcher kullanılır.
"""
from spotify_organizer import enrich, fixtures


def _fake(title, artist):
    return {"bpm": 128, "camelot": "8A"}


def _missing_track():
    # t17: bpm/camelot None olan demo track
    return dict(fixtures.TRACKS["t17"])


# --- enrich_tracks: doldurma (happy path) ---

def test_enrich_eksik_doldurulur():
    tracks = [_missing_track()]
    result = enrich.enrich_tracks(tracks, fetch=_fake)
    assert result[0]["bpm"] == 128
    assert result[0]["camelot"] == "8A"


def test_enrich_dolu_track_dokunulmaz():
    full = dict(fixtures.TRACKS["t01"])  # bpm=104, camelot="8B"
    result = enrich.enrich_tracks([full], fetch=_fake)
    assert result[0]["bpm"] == 104
    assert result[0]["camelot"] == "8B"


def test_enrich_uzunluk_korunur():
    tracks = [dict(fixtures.TRACKS["t01"]), _missing_track()]
    result = enrich.enrich_tracks(tracks, fetch=_fake)
    assert len(result) == len(tracks)


# --- mutasyon yok ---

def test_enrich_giris_mutasyona_ugramaz():
    track = _missing_track()
    enrich.enrich_tracks([track], fetch=_fake)
    assert track["bpm"] is None
    assert track["camelot"] is None


# --- cache: ikinci çağrıda fetch tekrar çağrılmaz ---

def test_enrich_cache_fetch_tek_cagri():
    calls = {"n": 0}

    def counting_fetch(title, artist):
        calls["n"] += 1
        return {"bpm": 128, "camelot": "8A"}

    cache = {}
    enrich.enrich_tracks([_missing_track()], fetch=counting_fetch, cache=cache)
    assert calls["n"] == 1
    # Aynı title|artist tekrar gelince cache'ten okunur, fetch artmaz
    enrich.enrich_tracks([_missing_track()], fetch=counting_fetch, cache=cache)
    assert calls["n"] == 1


def test_enrich_cache_anahtar_paylasimi():
    calls = {"n": 0}

    def counting_fetch(title, artist):
        calls["n"] += 1
        return {"bpm": 128, "camelot": "8A"}

    cache = {}
    # İki ayrı listede aynı şarkı → tek fetch
    enrich.enrich_tracks([_missing_track()], fetch=counting_fetch, cache=cache)
    enrich.enrich_tracks([_missing_track()], fetch=counting_fetch, cache=cache)
    assert calls["n"] == 1
    key = f'{fixtures.TRACKS["t17"]["title"]}|{fixtures.TRACKS["t17"]["artist"]}'.lower()
    assert key in cache


# --- fetch=None ---

def test_enrich_fetch_none_track_degismez():
    track = _missing_track()
    result = enrich.enrich_tracks([track], fetch=None)
    assert result[0]["bpm"] is None
    assert result[0]["camelot"] is None


# --- fetch None döndürürse kırılmaz ---

def test_enrich_fetch_none_dondurur():
    def none_fetch(title, artist):
        return None

    result = enrich.enrich_tracks([_missing_track()], fetch=none_fetch)
    assert result[0]["bpm"] is None
    assert result[0]["camelot"] is None


# --- load_cache / save_cache round-trip ---

def test_load_cache_olmayan_dosya_bos_dict(tmp_path):
    path = tmp_path / "yok" / "bpm.json"
    assert enrich.load_cache(str(path)) == {}


def test_save_load_cache_round_trip(tmp_path):
    path = tmp_path / "cache" / "bpm.json"
    data = {"şımarık|tarkan": {"bpm": 120, "camelot": "9B"}}
    enrich.save_cache(str(path), data)
    assert enrich.load_cache(str(path)) == data


# --- open_key_to_camelot ---

def test_open_key_major():
    # OpenKey 1d (C major) → Camelot 8B
    assert enrich.open_key_to_camelot("1d") == "8B"


def test_open_key_minor():
    # OpenKey 1m (A minor) → Camelot 8A
    assert enrich.open_key_to_camelot("1m") == "8A"


def test_open_key_gecersiz():
    assert enrich.open_key_to_camelot("") is None
    assert enrich.open_key_to_camelot("x") is None
    assert enrich.open_key_to_camelot("99z") is None


# --- build_getsongbpm_fetch: boş key güvenli (ağ YOK) ---

def test_build_fetch_bos_key_none():
    fetch = enrich.build_getsongbpm_fetch("")
    assert fetch("Şımarık", "Tarkan") is None
