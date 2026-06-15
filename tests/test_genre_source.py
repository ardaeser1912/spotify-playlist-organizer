"""genre_source testleri — iTunes tür kaynağı. GERÇEK AĞ YOK (http_get mock)."""
import json

from spotify_organizer import genre_source


# --- itunes_to_bucket: iTunes ham adı → kova ---

def test_bucket_hiphop():
    assert genre_source.itunes_to_bucket("Hip-Hop/Rap") == "Hip-Hop"


def test_bucket_dance_elektronik():
    assert genre_source.itunes_to_bucket("Dance") == "Elektronik"


def test_bucket_electronic_elektronik():
    assert genre_source.itunes_to_bucket("Electronic") == "Elektronik"


def test_bucket_pop():
    assert genre_source.itunes_to_bucket("Pop") == "Pop"


def test_bucket_alternative_rock():
    assert genre_source.itunes_to_bucket("Alternative") == "Rock"


def test_bucket_rnb_soul():
    assert genre_source.itunes_to_bucket("R&B/Soul") == "R&B"


def test_bucket_jazz_diger():
    assert genre_source.itunes_to_bucket("Jazz") == "Diğer"


def test_bucket_empty_diger():
    assert genre_source.itunes_to_bucket("") == "Diğer"


def test_bucket_arabesk_oncelik():
    # Arabesk, Pop'tan önce gelir (öncelik sırası)
    assert genre_source.itunes_to_bucket("Arabesk-Pop") == "Arabesk"


# --- İnce elektronik kovaları: gerçek cache ham verisi örnekleri ---

def test_bucket_hard_techno_oncelik():
    # "hard techno" + "hardstyle" var → Hard Tekno (Tekno'dan önce kazanır)
    assert genre_source.itunes_to_bucket(
        "electronic edm big room house hard techno hardstyle"
    ) == "Hard Tekno"


def test_bucket_techno():
    assert genre_source.itunes_to_bucket("techno") == "Tekno"


def test_bucket_house_oncelik():
    # garage + house var, edm de var → House (Elektronik'ten önce kazanır)
    assert genre_source.itunes_to_bucket("dance house dj garage edm") == "House"


def test_bucket_hiphop_genel():
    # rap var → Hip-Hop (House'tan önce kazanır)
    assert genre_source.itunes_to_bucket("pop rap jazz dance house") == "Hip-Hop"


def test_bucket_trap():
    assert genre_source.itunes_to_bucket("trap drill") == "Trap"


def test_bucket_dance_elektronik_genel():
    assert genre_source.itunes_to_bucket("Dance") == "Elektronik"


def test_bucket_rnb_birlesik():
    assert genre_source.itunes_to_bucket("r&b rnb soul") == "R&B"


def test_bucket_rock_metal():
    assert genre_source.itunes_to_bucket("rock metal") == "Rock"


def test_bucket_pop_synth():
    assert genre_source.itunes_to_bucket("pop synth-pop") == "Pop"


def test_bucket_jazz_diger_genel():
    assert genre_source.itunes_to_bucket("Jazz") == "Diğer"


# --- fetch_itunes_genre: sahte http_get ---

class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def test_fetch_results_dolu():
    def http_get(url, timeout):
        return _FakeResp({"results": [{"primaryGenreName": "Hip-Hop/Rap"}]})
    assert genre_source.fetch_itunes_genre("Drake", http_get=http_get) == "Hip-Hop/Rap"


def test_fetch_results_bos_none():
    def http_get(url, timeout):
        return _FakeResp({"results": []})
    assert genre_source.fetch_itunes_genre("Yokyok", http_get=http_get) is None


def test_fetch_exception_none():
    def http_get(url, timeout):
        raise RuntimeError("ağ patladı")
    assert genre_source.fetch_itunes_genre("Drake", http_get=http_get) is None


def test_fetch_artist_url_encode():
    seen = {}

    def http_get(url, timeout):
        seen["url"] = url
        return _FakeResp({"results": [{"primaryGenreName": "Pop"}]})
    genre_source.fetch_itunes_genre("Sezen Aksu", http_get=http_get)
    assert "Sezen%20Aksu" in seen["url"]


# --- buckets_for_artists: cache kullanır, fetch tekrarlamaz ---

def test_buckets_for_artists_temel():
    fake = {"Drake": "Hip-Hop/Rap", "Tarkan": "Pop"}
    cache = {}
    result = genre_source.buckets_for_artists(
        ["Drake", "Tarkan"], cache, fetch=lambda n: fake.get(n)
    )
    assert result == {"Drake": "Hip-Hop", "Tarkan": "Pop"}


def test_buckets_for_artists_cache_fetch_cagrilmaz():
    calls = {"n": 0}

    def fetch(name):
        calls["n"] += 1
        return "Pop"

    cache = {}
    genre_source.buckets_for_artists(["Tarkan"], cache, fetch=fetch)
    # İkinci çağrıda cache dolu → fetch tekrar çağrılmaz
    genre_source.buckets_for_artists(["Tarkan"], cache, fetch=fetch)
    assert calls["n"] == 1


def test_buckets_for_artists_fetch_none_diger():
    cache = {}
    result = genre_source.buckets_for_artists(
        ["Bilinmeyen"], cache, fetch=lambda n: None
    )
    assert result == {"Bilinmeyen": "Diğer"}


def test_buckets_for_artists_benzersiz():
    calls = {"n": 0}

    def fetch(name):
        calls["n"] += 1
        return "Pop"

    result = genre_source.buckets_for_artists(["Tarkan", "Tarkan"], {}, fetch=fetch)
    assert result == {"Tarkan": "Pop"}
    assert calls["n"] == 1


# --- load_cache / save_cache: round-trip ---

def test_load_cache_yoksa_bos(tmp_path):
    assert genre_source.load_cache(tmp_path / "yok.json") == {}


def test_save_load_round_trip(tmp_path):
    path = tmp_path / "genres.json"
    data = {"drake": "Hip-Hop/Rap", "tarkan": "Pop"}
    genre_source.save_cache(path, data)
    assert genre_source.load_cache(path) == data
    # gerçekten JSON yazılmış mı
    assert json.loads(path.read_text(encoding="utf-8")) == data


# --- MusicBrainz (iTunes throttle alternatifi) ---

def test_itunes_to_bucket_mb_birlesik_etiketler():
    # MB etiketleri boşlukla birleşik gelir; öncelikli kova kazanır.
    assert genre_source.itunes_to_bucket("pop rap hip-hop") == "Hip-Hop"
    assert genre_source.itunes_to_bucket("pop synth-pop rnb") == "R&B"
    assert genre_source.itunes_to_bucket("rock heavy metal") == "Rock"
    assert genre_source.itunes_to_bucket("electronic pop") == "Elektronik"


def test_fetch_musicbrainz_genre_birlestirir():
    def http_get(url, headers=None, timeout=None):
        class R:
            def json(self):
                return {"artists": [{"name": "Drake",
                                     "tags": [{"name": "pop"}, {"name": "rap"}, {"name": "hip-hop"}]}]}
        return R()
    assert genre_source.fetch_musicbrainz_genre("Drake", http_get=http_get) == "pop rap hip-hop"


def test_fetch_musicbrainz_genre_bos_ve_hata():
    def empty(url, headers=None, timeout=None):
        class R:
            def json(self): return {"artists": []}
        return R()
    assert genre_source.fetch_musicbrainz_genre("Yok", http_get=empty) is None

    def boom(url, headers=None, timeout=None):
        raise RuntimeError("ağ")
    assert genre_source.fetch_musicbrainz_genre("X", http_get=boom) is None
