"""Servis katmanı — Önizle (preview) + Onaylı Uygula (apply) orkestrasyonu.

EN KRİTİK GÜVENLİK KURALI: hiçbir mutasyon önizlemede olmaz. apply çağrılınca ÖNCE
kaynak `backups/<etiket>-<ts>.json`'a yedeklenir, SONRA istemci üzerinden işlenir.

YENİ-playlist işlemleri (orijinali silmez): türe-ayır, birleştir, böl, keşif.
HEDEF-playlist işlemleri (yedek + replace): sırala, geçişli-sırala, tekrar-temizle.
  → Hedef "Beğenilenler" ise reorder/replace YOK; kopya YENİ playlist üretilir (kilitli karar #6).
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime

from . import enrich, genre, order, organize

LIKED = ("liked", "p_liked")


def _uris(tracks: list[dict]) -> list[str]:
    return [t["uri"] for t in tracks if t.get("uri")]


def _is_liked(source: str) -> bool:
    return source in LIKED


class OrganizerService:
    def __init__(self, client, backup_dir: str = "backups", bpm_fetch=None):
        self.client = client
        self.backup_dir = backup_dir
        self.bpm_fetch = bpm_fetch  # CERRAH: None → enrich gerçek çağrı yapmaz

    # ---------- yardımcılar ----------
    def _tracks_for(self, source: str) -> list[dict]:
        return self.client.liked_tracks() if _is_liked(source) else self.client.playlist_tracks(source)

    def _name_for(self, source: str) -> str:
        if _is_liked(source):
            return "Beğenilenler"
        pl = next((p for p in self.client.playlists() if p["id"] == source), None)
        return pl["name"] if pl else source

    def _artist_genres(self, tracks: list[dict]) -> dict:
        ids = [t["artist_id"] for t in tracks if t.get("artist_id")]
        return self.client.artist_genres(ids) if ids else {}

    def _enriched(self, tracks: list[dict]) -> list[dict]:
        """Eksik bpm/camelot'u (mock fetch) doldur — bpm_fetch None ise dokunmaz."""
        if any(t.get("bpm") is None or t.get("camelot") is None for t in tracks):
            return enrich.enrich_tracks(tracks, fetch=self.bpm_fetch)
        return tracks

    def _backup(self, label: str, tracks: list[dict]) -> str:
        os.makedirs(self.backup_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        safe = re.sub(r"[^\w-]", "_", label) or "playlist"
        path = os.path.join(self.backup_dir, f"{safe}-{ts}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"label": label, "ts": ts, "count": len(tracks), "tracks": tracks},
                      f, ensure_ascii=False, indent=2)
        return path

    def _apply_to_target(self, source: str, new_name: str, tracks: list[dict]) -> dict:
        """Hedef-playlist işlemi: yedek al, sonra Beğenilenler→YENİ kopya, değilse replace."""
        backup = self._backup(self._name_for(source), self._tracks_for(source))
        if _is_liked(source):
            res = self.client.create_playlist(new_name, _uris(tracks))
            return {"created": [{"id": res["id"], "name": res["name"], "count": len(tracks)}],
                    "backup": backup}
        self.client.replace_tracks(source, _uris(tracks))
        return {"updated": {"id": source, "count": len(tracks)}, "backup": backup}

    # ---------- PREVIEW (mutasyon YOK) ----------
    def preview_split_genre(self, source: str) -> dict:
        tracks = self._tracks_for(source)
        ag = self._artist_genres(tracks)
        groups = genre.split_by_genre(tracks, ag)
        return {"source": source,
                "groups": [{"bucket": b, "count": len(ts), "tracks": ts} for b, ts in groups.items()]}

    def preview_order(self, source: str) -> dict:
        tracks = self._enriched(self._tracks_for(source))
        return {"source": source, "tracks": order.harmonic_order(tracks)}

    def preview_dedupe(self, source: str) -> dict:
        res = organize.dedupe(self._tracks_for(source))
        return {"source": source, "kept": res["kept"], "removed": res["removed"],
                "removed_count": len(res["removed"])}

    def preview_sort(self, source: str, keys: list) -> dict:
        return {"source": source, "tracks": organize.sort_tracks(self._tracks_for(source), keys)}

    def preview_merge(self, source_ids: list[str]) -> dict:
        merged = organize.merge_playlists([self._tracks_for(s) for s in source_ids])
        return {"sources": source_ids, "tracks": merged, "count": len(merged)}

    def preview_split(self, source: str, by: str, size: int | None = None) -> dict:
        tracks = self._tracks_for(source)
        if by == "decade":
            groups = organize.split_by_decade(tracks)
        elif by == "tempo":
            tracks = self._enriched(tracks)
            groups = organize.split_by_tempo(tracks)
        elif by == "size":
            chunks = organize.split_by_size(tracks, int(size or 25))
            groups = {f"Bölüm {i + 1}": c for i, c in enumerate(chunks)}
        else:
            raise ValueError(f"bilinmeyen böl tipi: {by}")
        return {"source": source, "by": by,
                "groups": [{"label": k, "count": len(v), "tracks": v} for k, v in groups.items()]}

    def insights(self, source: str) -> dict:
        tracks = self._enriched(self._tracks_for(source))
        ag = self._artist_genres(tracks)
        labels = {t["id"]: genre.normalize_bucket(ag.get(t.get("artist_id"), [])) for t in tracks}
        return organize.insights(tracks, genre_labels=labels)

    def top(self) -> dict:
        return {"tracks": self.client.top_tracks(), "artists": self.client.top_artists()}

    def search(self, query: str) -> dict:
        return {"query": query, "tracks": self.client.search_tracks(query)}

    def list_backups(self) -> list[dict]:
        if not os.path.isdir(self.backup_dir):
            return []
        out = []
        for fn in sorted(os.listdir(self.backup_dir), reverse=True):
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.backup_dir, fn), encoding="utf-8") as f:
                    d = json.load(f)
                out.append({"file": fn, "label": d.get("label"), "ts": d.get("ts"),
                            "count": d.get("count", len(d.get("tracks", [])))})
            except (OSError, json.JSONDecodeError):
                continue
        return out

    # ---------- APPLY (yedek + mutasyon) ----------
    def apply_split_genre(self, source: str) -> dict:
        prev = self.preview_split_genre(source)
        backup = self._backup(self._name_for(source), self._tracks_for(source))
        base = self._name_for(source)
        created = []
        for g in prev["groups"]:
            res = self.client.create_playlist(f"{base} — {g['bucket']}", _uris(g["tracks"]))
            created.append({"id": res["id"], "name": res["name"], "count": g["count"]})
        return {"created": created, "backup": backup}

    def apply_order(self, source: str) -> dict:
        ordered = self.preview_order(source)["tracks"]
        return self._apply_to_target(source, f"{self._name_for(source)} (Geçişli)", ordered)

    def apply_dedupe(self, source: str) -> dict:
        kept = self.preview_dedupe(source)["kept"]
        return self._apply_to_target(source, f"{self._name_for(source)} (Temiz)", kept)

    def apply_sort(self, source: str, keys: list) -> dict:
        sorted_tracks = self.preview_sort(source, keys)["tracks"]
        return self._apply_to_target(source, f"{self._name_for(source)} (Sıralı)", sorted_tracks)

    def apply_merge(self, source_ids: list[str], name: str) -> dict:
        merged = self.preview_merge(source_ids)["tracks"]
        for s in source_ids:
            self._backup(self._name_for(s), self._tracks_for(s))
        res = self.client.create_playlist(name or "Birleştirilmiş", _uris(merged))
        return {"created": [{"id": res["id"], "name": res["name"], "count": len(merged)}]}

    def apply_split(self, source: str, by: str, size: int | None = None) -> dict:
        prev = self.preview_split(source, by, size)
        backup = self._backup(self._name_for(source), self._tracks_for(source))
        base = self._name_for(source)
        created = []
        for g in prev["groups"]:
            res = self.client.create_playlist(f"{base} — {g['label']}", _uris(g["tracks"]))
            created.append({"id": res["id"], "name": res["name"], "count": g["count"]})
        return {"created": created, "backup": backup}

    def restore(self, backup_file: str) -> dict:
        path = os.path.join(self.backup_dir, os.path.basename(backup_file))
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        res = self.client.create_playlist(f"{d.get('label', 'Yedek')} (Geri Yüklendi)",
                                          _uris(d.get("tracks", [])))
        return {"created": [{"id": res["id"], "name": res["name"], "count": d.get("count", 0)}]}
