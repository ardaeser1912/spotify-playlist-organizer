"""Spotify istemci sözleşmesi (Protocol) + gerçek spotipy implementasyonu.

CERRAH modu: gerçek istemci LOOP TARAFINDAN ÇALIŞTIRILMAZ. Testler `tests/mock_client.py`
kullanır. Bu dosya yalnızca sözleşmeyi ve sabah `auth.py` ile bağlanınca kullanılacak
gerçek implementasyonu tanımlar.

Normalize edilmiş Track şekli (fixtures.py ile birebir aynı):
    {id, title, artist, artist_id, uri, duration_ms, bpm, camelot, year, popularity}

bpm/camelot Spotify'dan GELMEZ (Audio Features Kasım 2024 kapandı) → enrich.py GetSongBPM
ile doldurur. Bu yüzden gerçek istemci bpm=None, camelot=None döndürür.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SpotifyClient(Protocol):
    """Servis katmanının ihtiyaç duyduğu tüm işlemler. Mock + gerçek aynı sözleşmeyi uygular."""

    # --- okuma ---
    def current_user(self) -> dict: ...
    def playlists(self) -> list[dict]: ...                       # [{id, name, track_count}]
    def playlist_tracks(self, playlist_id: str) -> list[dict]: ...  # [Track]
    def liked_tracks(self) -> list[dict]: ...                    # [Track]
    def artist_genres(self, artist_ids: list[str]) -> dict: ...  # {artist_id: [genre,...]}
    def top_tracks(self, limit: int = 20) -> list[dict]: ...     # [Track]
    def top_artists(self, limit: int = 20) -> list[dict]: ...    # [{id, name, genres}]
    def search_tracks(self, query: str, limit: int = 20) -> list[dict]: ...  # [Track]

    # --- yazma (apply) — servis önce backup alır, sonra çağırır ---
    def create_playlist(self, name: str, track_uris: list[str], description: str = "") -> dict: ...  # {id, name}
    def add_tracks(self, playlist_id: str, track_uris: list[str]) -> None: ...
    def replace_tracks(self, playlist_id: str, track_uris: list[str]) -> None: ...  # reorder = replace


# Spotify sanatçı genres → bizim Track'te yok; ayrı çağrı. Sayfa limiti 50.
_PAGE = 50


def _normalize_track(item: dict) -> dict | None:
    """spotipy track objesi → normalize Track. Episode/None öğeleri atlar."""
    if not item or item.get("type") == "episode" or not item.get("id"):
        return None
    artists = item.get("artists") or [{}]
    album = item.get("album") or {}
    release = album.get("release_date") or ""
    try:
        year = int(release[:4]) if release else None
    except ValueError:
        year = None
    return {
        "id": item["id"],
        "title": item.get("name", ""),
        "artist": artists[0].get("name", ""),
        "artist_id": artists[0].get("id", ""),
        "uri": item.get("uri", f"spotify:track:{item['id']}"),
        "duration_ms": item.get("duration_ms", 0),
        "bpm": None,       # enrich.py doldurur (GetSongBPM)
        "camelot": None,   # enrich.py doldurur
        "year": year,
        "popularity": item.get("popularity", 0),
    }


class SpotipyClient:
    """Gerçek Spotify istemcisi (spotipy sarmalayıcı). CERRAH modunda loop ÇALIŞTIRMAZ.

    `sp` bir yetkilendirilmiş `spotipy.Spotify` örneğidir (auth.py üretir).
    Metot adları context7/spotipy docs ile doğrulandı.
    """

    def __init__(self, sp):
        self.sp = sp

    # --- okuma ---
    def current_user(self) -> dict:
        u = self.sp.current_user()
        return {"id": u["id"], "display_name": u.get("display_name") or u["id"]}

    def _paginate(self, page):
        """spotipy sayfalı cevabını ({items, next}) tek listede toplar."""
        items = []
        while page:
            items.extend(page.get("items", []))
            page = self.sp.next(page) if page.get("next") else None
        return items

    def playlists(self) -> list[dict]:
        items = self._paginate(self.sp.current_user_playlists(limit=_PAGE))
        return [{"id": p["id"], "name": p["name"], "track_count": p["tracks"]["total"]}
                for p in items if p]

    def playlist_tracks(self, playlist_id: str) -> list[dict]:
        items = self._paginate(self.sp.playlist_items(playlist_id, limit=100,
                                                       additional_types=("track",)))
        out = [_normalize_track(it.get("track")) for it in items]
        return [t for t in out if t]

    def liked_tracks(self) -> list[dict]:
        items = self._paginate(self.sp.current_user_saved_tracks(limit=_PAGE))
        out = [_normalize_track(it.get("track")) for it in items]
        return [t for t in out if t]

    def artist_genres(self, artist_ids: list[str]) -> dict:
        out: dict[str, list[str]] = {}
        uniq = [a for a in dict.fromkeys(artist_ids) if a]
        for i in range(0, len(uniq), _PAGE):
            res = self.sp.artists(uniq[i:i + _PAGE]) or {}
            for a in res.get("artists", []):
                if a:
                    out[a["id"]] = a.get("genres", [])
        return out

    def top_tracks(self, limit: int = 20) -> list[dict]:
        res = self.sp.current_user_top_tracks(limit=limit) or {}
        out = [_normalize_track(t) for t in res.get("items", [])]
        return [t for t in out if t]

    def top_artists(self, limit: int = 20) -> list[dict]:
        res = self.sp.current_user_top_artists(limit=limit) or {}
        return [{"id": a["id"], "name": a["name"], "genres": a.get("genres", [])}
                for a in res.get("items", []) if a]

    def search_tracks(self, query: str, limit: int = 20) -> list[dict]:
        res = self.sp.search(q=query, type="track", limit=limit) or {}
        items = (res.get("tracks") or {}).get("items", [])
        out = [_normalize_track(t) for t in items]
        return [t for t in out if t]

    # --- yazma ---
    def create_playlist(self, name: str, track_uris: list[str], description: str = "") -> dict:
        uid = self.sp.current_user()["id"]
        pl = self.sp.user_playlist_create(uid, name, public=False, description=description)
        for i in range(0, len(track_uris), 100):
            self.sp.playlist_add_items(pl["id"], track_uris[i:i + 100])
        return {"id": pl["id"], "name": pl["name"]}

    def add_tracks(self, playlist_id: str, track_uris: list[str]) -> None:
        for i in range(0, len(track_uris), 100):
            self.sp.playlist_add_items(playlist_id, track_uris[i:i + 100])

    def replace_tracks(self, playlist_id: str, track_uris: list[str]) -> None:
        # reorder = mevcut içeriği yeni sırayla değiştir (ilk 100 replace, gerisi add)
        self.sp.playlist_replace_items(playlist_id, track_uris[:100])
        for i in range(100, len(track_uris), 100):
            self.sp.playlist_add_items(playlist_id, track_uris[i:i + 100])
