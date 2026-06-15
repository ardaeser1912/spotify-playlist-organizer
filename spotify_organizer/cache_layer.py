"""CachingClient — pahalı Spotify OKUMALARINI diske cache'leyen sarmalayıcı.

Sorun: Gerçek hesapta her işlem 979 Beğenilenler'i Spotify'dan tekrar tekrar çekiyordu
→ yavaş + rate-limit (bir kez 13 saat kilit). Bu katman pahalı listeleri TTL'li olarak
diske yazar; taze ise diskten döner, ağ yormaz.

Sözleşme: SpotifyClient Protocol'ün TÜM metotlarını uygular (runtime_checkable → isinstance True).
- Cache'lenen pahalı okumalar: liked_tracks / playlists / playlist_tracks(pid).
- Ucuz/değişken okumalar (current_user, artist_genres, top_*, search_tracks): doğrudan delege.
- Yazma (create_playlist, add_tracks, replace_tracks): delege + tüm cache geçersiz (bayat kalmasın).

Disk formatı: {anahtar: {"ts": epoch, "data": <liste>}}. Dosya yoksa boş başlar.
Bozuk JSON → çökmeden boş başlar.
"""
from __future__ import annotations

import json
import os
import time


class CachingClient:
    def __init__(self, client, cache_path: str = "cache/spotify_data.json", ttl_seconds: int = 1800):
        self.client = client
        self.cache_path = cache_path
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, dict] = self._load()

    # --- disk yardımcıları ---
    def _load(self) -> dict[str, dict]:
        """Diskten cache'i oku. Dosya yok / bozuk JSON → boş dict (çökme yok)."""
        try:
            with open(self.cache_path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, ValueError, OSError):
            return {}

    def _save(self) -> None:
        d = os.path.dirname(self.cache_path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f)

    def _fresh(self, key: str) -> bool:
        entry = self._cache.get(key)
        return bool(entry) and (time.time() - entry.get("ts", 0) < self.ttl_seconds)

    def _cached(self, key: str, fetch):
        """key taze ise diskten döndür, değilse fetch() çağır + diske yaz."""
        if self._fresh(key):
            return self._cache[key]["data"]
        data = fetch()
        self._cache[key] = {"ts": time.time(), "data": data}
        self._save()
        return data

    def clear(self) -> None:
        """Bellek + disk cache'ini boşalt (kullanıcı 'yenile' derse)."""
        self._cache = {}
        try:
            os.remove(self.cache_path)
        except FileNotFoundError:
            pass

    # --- cache'lenen pahalı okumalar ---
    def liked_tracks(self) -> list[dict]:
        return self._cached("liked", self.client.liked_tracks)

    def playlists(self) -> list[dict]:
        return self._cached("playlists", self.client.playlists)

    def playlist_tracks(self, playlist_id: str) -> list[dict]:
        return self._cached(f"pl:{playlist_id}", lambda: self.client.playlist_tracks(playlist_id))

    # --- delege edilen ucuz / değişken okumalar (cache yok) ---
    def current_user(self) -> dict:
        return self.client.current_user()

    def artist_genres(self, artist_ids: list[str]) -> dict:
        return self.client.artist_genres(artist_ids)

    def top_tracks(self, limit: int = 20) -> list[dict]:
        return self.client.top_tracks(limit)

    def top_artists(self, limit: int = 20) -> list[dict]:
        return self.client.top_artists(limit)

    def search_tracks(self, query: str, limit: int = 20) -> list[dict]:
        return self.client.search_tracks(query, limit)

    # --- yazma: delege + cache geçersiz kıl (playlist değişti → bayat veri kalmasın) ---
    def create_playlist(self, name: str, track_uris: list[str], description: str = "") -> dict:
        res = self.client.create_playlist(name, track_uris, description)
        self.clear()
        return res

    def add_tracks(self, playlist_id: str, track_uris: list[str]) -> None:
        self.client.add_tracks(playlist_id, track_uris)
        self.clear()

    def replace_tracks(self, playlist_id: str, track_uris: list[str]) -> None:
        self.client.replace_tracks(playlist_id, track_uris)
        self.clear()
