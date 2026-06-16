"""Ücretsiz tür kaynağı — iTunes Search API'den sanatçı türünü çeker.

Spotify dev-mode /artists 403 verdiği için tür buradan gelir. ANAHTARSIZ:
    https://itunes.apple.com/search?term=ARTIST&entity=musicArtist&limit=1
    → {"results":[{"primaryGenreName":"Hip-Hop/Rap", ...}]}

iTunes ham tür adları genre.py kovalarına çevrilir (Pop/Rock/Elektronik/
Hip-Hop/R&B/Arabesk/Diğer). Saf fonksiyonlar; ağ sadece fetch_itunes_genre'da.
"""
from __future__ import annotations

import json
import os
import re
from urllib.parse import quote

import requests

OTHER = "Diğer"

# Öncelik sırasıyla (üstte olan kazanır). iTunes "Dance"/"Alternative" gibi
# kendine özgü adlar kullanır → kova eşlemesi onları da kapsar.
_BUCKETS = [
    ("Arabesk", ("arabesk",)),
    ("Hard Tekno", ("hard techno", "hardstyle", "hardcore", "gabber")),
    ("Tekno", ("techno",)),
    ("Trap", ("trap", "drill", "phonk")),
    ("Hip-Hop", ("hip hop", "hip-hop", "rap")),
    ("House", ("house", "big room", "garage", "disco")),
    ("Drum & Bass", ("drum and bass", "dnb", "dubstep", "breakbeat", "jungle")),
    ("Trance", ("trance",)),
    ("Elektronik", ("electronic", "edm", "electro", "dance", "dans")),
    ("R&B", ("r&b", "rnb", "rhythm and blues", "soul", "funk")),
    ("Rock", ("rock", "metal", "punk", "alternative", "grunge")),
    # Dünya/tail türleri — DÜŞÜK öncelik: çok-türlü sanatçılarda (ör. Rolling Stones
    # "rock…reggae", Temptations "soul…reggae") baskın tür kazansın, "reggae" minör
    # etiketi çalmasın. Afrobeat→Latin→Reggae sırası: Burna Boy→Afrobeat, reggaeton→Latin.
    ("Afrobeat", ("afrobeat", "afrobeats", "afrika", "african", "amapiano")),
    ("Latin", ("latin", "sertanejo", "brazilian", "samba", "bossa", "reggaeton",
               "forró", "forro", "cumbia", "axé")),
    ("Reggae", ("reggae", "ragga", "ska", "dancehall")),
    ("Jazz", ("jazz", "swing", "bebop")),
    ("Blues", ("blues",)),
    ("Pop", ("pop",)),
]

_ITUNES_URL = "https://itunes.apple.com/search"
_MB_URL = "https://musicbrainz.org/ws/2/artist"
_MB_UA = "SpotifyPlaylistOrganizer/1.0 (kisisel kullanim)"
_DZ_SEARCH_ARTIST = "https://api.deezer.com/search/artist"
_DZ_ARTIST = "https://api.deezer.com/artist"
_DZ_GENRE = "https://api.deezer.com/genre"


# Anahtar kelimeler KELİME-SINIRIYLA eşleşir (\b) → "dance" kelimesi eşleşir ama
# "dancehall" İÇİNDE eşleşmez. Ayrıca "dance" tireli bileşiklerde (dance-rock,
# dance-pop, dance-punk = rock/pop alt türleri) eşleşmez → o sanatçılar Rock/Pop kalır.
def _kw_pattern(kw: str) -> str:
    if kw == "dance":
        return r"\bdance\b(?!-)"
    return r"\b" + re.escape(kw) + r"\b"


_BUCKET_PATTERNS = [
    (bucket, re.compile("|".join(_kw_pattern(kw) for kw in keywords)))
    for bucket, keywords in _BUCKETS
]


def itunes_to_bucket(itunes_genre: str) -> str:
    """Ham tür adını ana kovaya çevirir (kelime-sınırı eşleşmesi). Boş/eşleşme yok → 'Diğer'."""
    g = (itunes_genre or "").lower()
    for bucket, pat in _BUCKET_PATTERNS:
        if pat.search(g):
            return bucket
    return OTHER


def fetch_itunes_genre(artist_name: str, http_get=None) -> str | None:
    """iTunes'tan ham primaryGenreName döndürür; bulunamazsa None.

    http_get(url, **kwargs) enjekte edilebilir (test için). None ise modül
    düzeyi requests.get kullanılır (timeout=10). Hata/boş → None.
    """
    if http_get is None:
        http_get = requests.get
    url = f"{_ITUNES_URL}?term={quote(artist_name)}&entity=musicArtist&limit=1"
    try:
        resp = http_get(url, timeout=10)
        data = resp.json()
        results = data.get("results") or []
        if not results:
            return None
        genre = results[0].get("primaryGenreName")
        return genre or None
    except Exception:
        return None


def fetch_musicbrainz_genre(artist_name: str, http_get=None) -> str | None:
    """MusicBrainz'den sanatçı tür etiketlerini boşlukla birleştirip döndürür; yoksa None.

    ANAHTARSIZ ama User-Agent zorunlu. iTunes IP throttle'a takılınca güvenilir
    alternatif (sürekli sorguya dayanıklı, ~1 istek/sn). Dönen string itunes_to_bucket
    ile kovaya çevrilir (etiketler: 'pop rap hip-hop' gibi).
    """
    if http_get is None:
        http_get = requests.get
    url = f"{_MB_URL}?query={quote(f'artist:\"{artist_name}\"')}&fmt=json&limit=1"
    try:
        resp = http_get(url, headers={"User-Agent": _MB_UA}, timeout=10)
        artists = (resp.json().get("artists") or [])
        if not artists:
            return None
        tags = [t.get("name", "") for t in (artists[0].get("tags") or [])]
        joined = " ".join(t for t in tags if t)
        return joined or None
    except Exception:
        return None


def fetch_deezer_genre(artist_name: str, http_get=None) -> str | None:
    """Deezer'dan sanatçı türü (ANAHTARSIZ). Sanatçıyı ara → ilk album'un genre_id'si
    → tür adı ('Rap/Hip Hop', 'Dans', 'Afrika müziği', 'Reggae' gibi).

    MusicBrainz + iTunes None dönünce güçlü 3. kaynak: niş/underground rap (MAZ0),
    yabancı sanatçıları bilir. itunes_to_bucket Deezer etiketlerini de kovaya çevirir.
    Hata/boş → None.
    """
    if http_get is None:
        http_get = requests.get
    try:
        s = (http_get(f"{_DZ_SEARCH_ARTIST}?q={quote(artist_name)}&limit=1",
                      timeout=10).json().get("data") or [])
        if not s:
            return None
        albums = (http_get(f"{_DZ_ARTIST}/{s[0]['id']}/albums?limit=5",
                           timeout=10).json().get("data") or [])
        for al in albums:
            gid = al.get("genre_id")
            if gid and gid != -1:
                name = http_get(f"{_DZ_GENRE}/{gid}", timeout=10).json().get("name")
                if name:
                    return name
        return None
    except Exception:
        return None


def fetch_best_genre(artist_name: str, http_get=None) -> str | None:
    """En iyi tür: MusicBrainz → iTunes → Deezer. KOVAYA OTURAN ilk sonucu yeğler
    (ör. MB 'turkish' gibi belirsiz/eşleşmez veri verirse Deezer'a iner). Hiçbiri
    oturmazsa ilk dolu ham değeri döndürür; hepsi boşsa None."""
    results = [fetch_musicbrainz_genre(artist_name, http_get),
               fetch_itunes_genre(artist_name, http_get),
               fetch_deezer_genre(artist_name, http_get)]
    for r in results:
        if r and itunes_to_bucket(r) != OTHER:
            return r
    return next((r for r in results if r), None)


def buckets_for_artists(artist_names, cache: dict, fetch=fetch_itunes_genre) -> dict:
    """Benzersiz sanatçı adları için {isim: kova}.

    cache anahtarı isim.lower(); ham tür tutar. Cache'te varsa fetch çağrılmaz.
    fetch None dönerse o isim 'Diğer' kovasına konur.
    """
    out: dict[str, str] = {}
    for name in dict.fromkeys(artist_names):  # benzersiz + sıra korur
        key = name.lower()
        if key in cache:
            raw = cache[key]
        else:
            raw = fetch(name)
            cache[key] = raw
        out[name] = OTHER if raw is None else itunes_to_bucket(raw)
    return out


def load_cache(path) -> dict:
    """cache/genres.json yükler; dosya yoksa {}."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_cache(path, cache: dict) -> None:
    """cache'i JSON olarak yazar."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
