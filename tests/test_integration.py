"""Entegrasyon (uçtan uca) testleri — DEMO=1 Flask test_client, gerçek ağ/auth YOK.

Tam döngüler: apply → backup yazılır → /api/backups listeler → /api/restore geri yükler.
Her test `monkeypatch.chdir(tmp_path)` ile izole: backups/ tmp'ye düşer, testler birbirini
kirletmez. Zarf: {success, data, error}; tüm assert'ler data üzerinden.
"""
import pytest


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DEMO", "1")
    from spotify_organizer.app import app
    app.config["TESTING"] = True
    return app.test_client()


def _data(r):
    j = r.get_json()
    assert j["success"] is True, j.get("error")
    return j["data"]


# ---------- ROUND-TRIP: apply → backups → restore ----------

def test_roundtrip_split_genre_apply_backup_restore(client, monkeypatch, tmp_path):
    # given: izole çalışma dizini (backups/ tmp'ye düşsün)
    monkeypatch.chdir(tmp_path)

    # when: Beğenilenler türe-ayır apply
    applied = _data(client.post("/api/split-genre/apply", json={"source": "liked"}))
    # then: yeni playlist'ler oluştu, orijinal silinmedi (created dolu)
    assert applied["created"]

    # when: yedekler listelenir
    bks = _data(client.get("/api/backups"))
    # then: en az 1 yedek ve kaynak (17 parça) yedeklendi
    assert len(bks) >= 1
    assert bks[0]["count"] == 17

    # when: o yedek geri yüklenir
    restored = _data(client.post("/api/restore", json={"file": bks[0]["file"]}))
    # then: geri yüklenen liste yeni playlist olarak oluşur (17 parça)
    assert restored["created"]
    assert restored["created"][0]["count"] == 17


# ---------- HER MUTASYON ARACI yedek yazar ----------

def test_her_mutasyon_araci_yedek_buyutur(client, monkeypatch, tmp_path):
    # given: izole dizin, başlangıçta yedek yok
    monkeypatch.chdir(tmp_path)
    assert _data(client.get("/api/backups")) == []

    # given: sırayla çalıştırılacak mutasyon apply'ları (her biri en az 1 yedek yazmalı)
    steps = [
        ("/api/order/apply", {"source": "p_yaz"}),
        ("/api/dedupe/apply", {"source": "p_yaz"}),
        ("/api/sort/apply", {"source": "p_yaz", "keys": [["popularity", "desc"]]}),
        ("/api/merge/apply", {"sources": ["p_yaz", "p_spor"], "name": "Birleşik"}),
        ("/api/split/apply", {"source": "p_yaz", "by": "decade"}),
    ]

    prev = 0
    for path, payload in steps:
        # when: mutasyon apply
        _data(client.post(path, json=payload))
        # then: yedek sayısı bir önceki adıma göre kesinlikle büyür
        count = len(_data(client.get("/api/backups")))
        assert count > prev, f"{path} yedek büyütmedi (prev={prev}, count={count})"
        prev = count


# ---------- order apply güvenlik davranışı (kilitli karar #6) ----------

def test_order_apply_liked_created_doner_replace_etmez(client, monkeypatch, tmp_path):
    # given: izole dizin
    monkeypatch.chdir(tmp_path)
    # when: Beğenilenler üzerinde geçişli-sırala apply
    res = _data(client.post("/api/order/apply", json={"source": "liked"}))
    # then: Beğenilenler replace EDİLMEZ → kopya YENİ playlist üretilir (created)
    assert "created" in res
    assert "updated" not in res
    assert res["created"][0]["count"] == 17


def test_order_apply_normal_playlist_updated_doner(client, monkeypatch, tmp_path):
    # given: izole dizin
    monkeypatch.chdir(tmp_path)
    # when: normal playlist (p_yaz) üzerinde geçişli-sırala apply
    res = _data(client.post("/api/order/apply", json={"source": "p_yaz"}))
    # then: normal playlist yerinde güncellenir (updated), kopya üretilmez
    assert "updated" in res
    assert "created" not in res
    assert res["updated"]["id"] == "p_yaz"


# ---------- discover/apply (yedeksiz YENİ playlist) ----------

def test_discover_apply_search_created(client, monkeypatch, tmp_path):
    # given: izole dizin
    monkeypatch.chdir(tmp_path)
    # when: arama sonucundan keşif playlist'i oluştur
    res = _data(client.post("/api/discover/apply",
                            json={"kind": "search", "query": "tarkan", "name": "Tarkan Keşif"}))
    # then: en az 1 parçayla yeni playlist oluşur
    assert res["created"]
    assert res["created"][0]["count"] >= 1


# ---------- PREVIEW uçları YEDEK YAZMAZ (mutasyon yok güvencesi) ----------

@pytest.mark.parametrize("path, payload", [
    ("/api/split-genre/preview", {"source": "liked"}),
    ("/api/order/preview", {"source": "liked"}),
    ("/api/dedupe/preview", {"source": "p_yaz"}),
    ("/api/sort/preview", {"source": "liked", "keys": [["popularity", "desc"]]}),
    ("/api/merge/preview", {"sources": ["p_yaz", "p_spor"]}),
    ("/api/split/preview", {"source": "liked", "by": "decade"}),
])
def test_preview_yedek_yazmaz(client, monkeypatch, tmp_path, path, payload):
    # given: izole dizin, başlangıçta yedek yok
    monkeypatch.chdir(tmp_path)
    assert _data(client.get("/api/backups")) == []
    # when: bir preview çağrısı yapılır
    _data(client.post(path, json=payload))
    # then: hiçbir yedek yazılmamış olmalı (preview salt-okunur)
    assert _data(client.get("/api/backups")) == []


# ---------- restore hata zarfı ----------

def test_restore_eksik_dosya_temiz_hata(client, monkeypatch, tmp_path):
    # given: izole dizin, var olmayan yedek dosyası
    monkeypatch.chdir(tmp_path)
    # when: olmayan dosya geri yüklenmeye çalışılır
    r = client.post("/api/restore", json={"file": "yok-1234.json"})
    j = r.get_json()
    # then: temiz hata zarfı (success:false, error dolu, 4xx/5xx)
    assert j["success"] is False
    assert j["error"]
    assert j["data"] is None
    assert r.status_code >= 400
