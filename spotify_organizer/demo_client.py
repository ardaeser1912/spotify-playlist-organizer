"""DemoClient — fixtures üzerine SpotifyClient sözleşmesi (DEMO=1 modunun istemcisi).

Auth GEREKMEZ. Yazma işlemleri (create/add/replace) bellekte kaydedilir.
Dönen track'ler KOPYADIR → çağıran fixtures'ı bozamaz.
"""
from __future__ import annotations

from . import fixtures


class DemoClient:
    def __init__(self):
        self.created: list[dict] = []
        self.added: dict[str, list[str]] = {}
        self.replaced: dict[str, list[str]] = {}
        self._seq = 0

    # --- okuma ---
    def current_user(self) -> dict:
        return {"id": "demo", "display_name": "Demo Kullanıcı"}

    def playlists(self) -> list[dict]:
        return fixtures.playlists_summary()

    def playlist_tracks(self, playlist_id: str) -> list[dict]:
        pl = fixtures.get_playlist(playlist_id)
        return [dict(t) for t in pl["tracks"]] if pl else []

    def liked_tracks(self) -> list[dict]:
        return self.playlist_tracks("p_liked")

    def artist_genres(self, artist_ids: list[str]) -> dict:
        return {a: list(fixtures.ARTISTS[a]["genres"])
                for a in dict.fromkeys(artist_ids) if a in fixtures.ARTISTS}

    def top_tracks(self, limit: int = 20) -> list[dict]:
        tracks = sorted(fixtures.TRACKS.values(), key=lambda t: t["popularity"], reverse=True)
        return [dict(t) for t in tracks[:limit]]

    def top_artists(self, limit: int = 20) -> list[dict]:
        arts = [{"id": a["id"], "name": a["name"], "genres": list(a["genres"])}
                for a in fixtures.ARTISTS.values() if a["genres"]]
        return arts[:limit]

    def search_tracks(self, query: str, limit: int = 20) -> list[dict]:
        q = (query or "").lower()
        hits = [dict(t) for t in fixtures.TRACKS.values()
                if q in t["title"].lower() or q in t["artist"].lower()]
        return hits[:limit]

    # --- yazma (apply) — bellekte kaydet ---
    def create_playlist(self, name: str, track_uris: list[str], description: str = "") -> dict:
        self._seq += 1
        pid = f"new_{self._seq}"
        self.created.append({"id": pid, "name": name, "uris": list(track_uris)})
        return {"id": pid, "name": name}

    def add_tracks(self, playlist_id: str, track_uris: list[str]) -> None:
        self.added.setdefault(playlist_id, []).extend(track_uris)

    def replace_tracks(self, playlist_id: str, track_uris: list[str]) -> None:
        self.replaced[playlist_id] = list(track_uris)
