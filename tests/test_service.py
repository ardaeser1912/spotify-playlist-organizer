"""F2 servis testleri — güvenlik çekirdeği: preview mutasyon yapmaz, apply önce
yedek alır, Beğenilenler asla reorder edilmez (kopya playlist)."""
import os

import pytest

from spotify_organizer.service import OrganizerService
from tests.mock_client import MockClient


def svc(tmp_path):
    return OrganizerService(MockClient(), backup_dir=str(tmp_path / "backups"))


# ---------- güvenlik: preview ----------
def test_preview_yapmaz_mutasyon_ve_yedek(tmp_path):
    s = svc(tmp_path)
    s.preview_split_genre("liked")
    s.preview_order("liked")
    s.preview_dedupe("liked")
    assert s.client.created == [] and s.client.replaced == {}
    assert not os.path.isdir(str(tmp_path / "backups"))  # yedek dosyası yazılmadı


def test_split_genre_preview_gruplar(tmp_path):
    prev = svc(tmp_path).preview_split_genre("liked")
    buckets = {g["bucket"] for g in prev["groups"]}
    assert {"Pop", "Rock", "Elektronik", "Hip-Hop"} & buckets
    assert sum(g["count"] for g in prev["groups"]) == 17  # tüm track'ler bir kovada


# ---------- güvenlik: apply yedek alır ----------
def test_apply_split_genre_yeni_playlistler_ve_yedek(tmp_path):
    s = svc(tmp_path)
    res = s.apply_split_genre("liked")
    assert res["created"] and os.path.isfile(res["backup"])
    assert len(s.client.created) == len(res["created"])  # orijinal silinmedi, yeniler kuruldu


def test_apply_order_liked_kopya_uretir_replace_etmez(tmp_path):
    s = svc(tmp_path)
    res = s.apply_order("liked")
    assert "created" in res and s.client.replaced == {}  # Beğenilenler reorder EDİLMEZ


def test_apply_order_normal_playlist_replace_eder(tmp_path):
    s = svc(tmp_path)
    res = s.apply_order("p_yaz")
    assert res["updated"]["id"] == "p_yaz" and "p_yaz" in s.client.replaced
    assert os.path.isfile(res["backup"])


def test_apply_dedupe_yedekli(tmp_path):
    s = svc(tmp_path)
    res = s.apply_dedupe("p_yaz")
    assert os.path.isfile(res["backup"])


# ---------- diğer işlemler ----------
def test_preview_sort_desc(tmp_path):
    prev = svc(tmp_path).preview_sort("liked", [("popularity", "desc")])
    pops = [t["popularity"] for t in prev["tracks"]]
    assert pops == sorted(pops, reverse=True)


def test_merge_birlestirir_dedup(tmp_path):
    prev = svc(tmp_path).preview_merge(["p_yaz", "p_spor"])
    ids = [t["id"] for t in prev["tracks"]]
    assert len(ids) == len(set(ids))  # ortak track'ler tek


def test_split_decade_tempo_size(tmp_path):
    s = svc(tmp_path)
    assert s.preview_split("liked", "decade")["groups"]
    assert s.preview_split("liked", "tempo")["groups"]
    sized = s.preview_split("liked", "size", size=5)["groups"]
    assert all(g["count"] <= 5 for g in sized)


def test_insights_genre_dist_dolu(tmp_path):
    ins = svc(tmp_path).insights("liked")
    assert ins["total"] == 17
    assert ins["genre_dist"] and "bpm_dist" in ins and ins["avg_popularity"] > 0


def test_order_bpm_eksik_olsa_da_calisir(tmp_path):
    # t17 bpm/camelot None; bpm_fetch None → enrich doldurmaz ama sıralama kırılmaz
    prev = svc(tmp_path).preview_order("liked")
    assert len(prev["tracks"]) == 17


def test_backups_listele_ve_restore(tmp_path):
    s = svc(tmp_path)
    s.apply_split_genre("liked")  # yedek üretir
    bks = s.list_backups()
    assert bks
    res = s.restore(bks[0]["file"])
    assert res["created"][0]["id"]


def test_create_from_top_ve_arama(tmp_path):
    s = svc(tmp_path)
    assert s.create_from("", "top")["created"][0]["count"] > 0
    res = s.create_from("Tarkan Listesi", "search", "tarkan")
    assert res["created"][0]["name"] == "Tarkan Listesi" and res["created"][0]["count"] >= 1


def test_enrich_fetch_ile_doldurur(tmp_path):
    s = OrganizerService(MockClient(), backup_dir=str(tmp_path / "b"),
                         bpm_fetch=lambda title, artist: {"bpm": 120, "camelot": "8A"})
    prev = s.preview_order("liked")
    assert all(t["bpm"] is not None for t in prev["tracks"])  # t17 dahil dolduruldu
