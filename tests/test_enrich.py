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


# --- build_getsongbpm_fetch: dayanıklılık (monkeypatch, GERÇEK AĞ YOK) ---

class _FakeResp:
    """requests.Response taklidi — sadece test için."""

    def __init__(self, payload, *, raise_status=False):
        self._payload = payload
        self._raise_status = raise_status

    def raise_for_status(self):
        if self._raise_status:
            raise RuntimeError("HTTP 500")

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def _patch_get(monkeypatch, resp_or_exc):
    """enrich.requests.get'i ağsız sahte ile değiştirir."""
    def fake_get(url, params=None, timeout=None):
        if isinstance(resp_or_exc, Exception):
            raise resp_or_exc
        return resp_or_exc
    monkeypatch.setattr(enrich.requests, "get", fake_get)


def test_fetch_basarili_cevap_bpm_camelot(monkeypatch):
    payload = {"search": [{"tempo": "120", "key_of": "G", "open_key": "9d"}]}
    _patch_get(monkeypatch, _FakeResp(payload))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    data = fetch("Şarkı", "Sanatçı")
    assert data == {"bpm": 120, "camelot": enrich.open_key_to_camelot("9d")}


def test_fetch_bos_search_none(monkeypatch):
    _patch_get(monkeypatch, _FakeResp({"search": []}))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    assert fetch("x", "y") is None


def test_fetch_search_anahtari_yok_none(monkeypatch):
    _patch_get(monkeypatch, _FakeResp({"error": "nope"}))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    assert fetch("x", "y") is None


def test_fetch_payload_dict_degil_none(monkeypatch):
    _patch_get(monkeypatch, _FakeResp(["liste", "değil", "dict"]))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    assert fetch("x", "y") is None


def test_fetch_tempo_yok_camelot_dolu_bpm_none(monkeypatch):
    payload = {"search": [{"open_key": "9d"}]}  # tempo yok
    _patch_get(monkeypatch, _FakeResp(payload))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    data = fetch("x", "y")
    assert data["bpm"] is None
    assert data["camelot"] == enrich.open_key_to_camelot("9d")


def test_fetch_open_key_yok_key_of_fallback(monkeypatch):
    payload = {"search": [{"tempo": "100", "key_of": "Am"}]}  # open_key yok
    _patch_get(monkeypatch, _FakeResp(payload))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    data = fetch("x", "y")
    assert data["bpm"] == 100
    assert data["camelot"] == "8A"  # Am → 8A


def test_fetch_open_key_oncelikli(monkeypatch):
    # open_key VARSA key_of'a düşmez; open_key kazanır
    payload = {"search": [{"tempo": "90", "open_key": "1d", "key_of": "Am"}]}
    _patch_get(monkeypatch, _FakeResp(payload))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    data = fetch("x", "y")
    assert data["camelot"] == "8B"  # open_key 1d → 8B (Am olsaydı 8A olurdu)


def test_fetch_tempo_ve_anahtar_yok_none(monkeypatch):
    payload = {"search": [{"title": "no tempo no key"}]}
    _patch_get(monkeypatch, _FakeResp(payload))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    assert fetch("x", "y") is None


def test_fetch_tempo_float_string(monkeypatch):
    payload = {"search": [{"tempo": "128.7", "open_key": "1m"}]}
    _patch_get(monkeypatch, _FakeResp(payload))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    data = fetch("x", "y")
    assert data["bpm"] == 128  # "128.7" → 128


def test_fetch_http_exception_none(monkeypatch):
    # raise_for_status patlar → None
    _patch_get(monkeypatch, _FakeResp({"search": [{"tempo": "120"}]}, raise_status=True))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    assert fetch("x", "y") is None


def test_fetch_requests_exception_none(monkeypatch):
    # requests.get'in kendisi patlar (bağlantı hatası)
    _patch_get(monkeypatch, RuntimeError("connection refused"))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    assert fetch("x", "y") is None


def test_fetch_timeout_none(monkeypatch):
    class _Timeout(Exception):
        pass
    _patch_get(monkeypatch, _Timeout("timed out"))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    assert fetch("x", "y") is None


def test_fetch_json_decode_hatasi_none(monkeypatch):
    # resp.json() patlar (JSON değil)
    _patch_get(monkeypatch, _FakeResp(ValueError("not json")))
    fetch = enrich.build_getsongbpm_fetch("KEY")
    assert fetch("x", "y") is None


def test_fetch_bos_key_aga_cikmaz(monkeypatch):
    # api_key boşsa requests.get HİÇ çağrılmamalı
    def boom(*a, **k):
        raise AssertionError("ağa çıkıldı!")
    monkeypatch.setattr(enrich.requests, "get", boom)
    fetch = enrich.build_getsongbpm_fetch("")
    assert fetch("x", "y") is None


# --- key_of_to_camelot doğrudan ---

def test_key_of_to_camelot_major_minor():
    assert enrich.key_of_to_camelot("C") == "8B"
    assert enrich.key_of_to_camelot("Am") == "8A"
    assert enrich.key_of_to_camelot("F#m") == "11A"


def test_key_of_to_camelot_gecersiz():
    assert enrich.key_of_to_camelot("") is None
    assert enrich.key_of_to_camelot("Zzz") is None
    assert enrich.key_of_to_camelot(None) is None
