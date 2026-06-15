"""Flask backend — DEMO + servis endpoint'leri.

DEMO=1 iken DemoClient (fixtures, auth gerekmez). DEMO olmadan SpotipyClient
(auth.py'nin ürettiği token cache; CERRAH modunda loop ÇALIŞTIRMAZ).

Tüm cevaplar tutarlı zarf: {success, data, error}. Mutasyon yalnızca .../apply
uçlarında ve servis ÖNCE backup alır.

Çalıştır:  DEMO=1 python -m spotify_organizer.app   (varsayılan port 5055)
"""
import os

from flask import Flask, jsonify, request

from .service import OrganizerService

app = Flask(__name__)


def _demo() -> bool:
    return os.environ.get("DEMO") == "1"


def _service() -> OrganizerService:
    if _demo():
        from .demo_client import DemoClient
        return OrganizerService(DemoClient())
    # Gerçek mod: spotipy (auth.py token cache). Loop CERRAH'ta buraya GİRMEZ.
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    from .client import REDIRECT_URI, SCOPES, SpotipyClient
    from .enrich import build_getsongbpm_fetch
    # retries/status_retries=0: 429 (rate limit) gelince spotipy SAATLERCE retry-sleep
    # yapıp backend'i KİLİTLEMESİN → hızlı başarısız ol, UI net mesaj göstersin.
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=SCOPES, redirect_uri=os.environ.get("SPOTIPY_REDIRECT_URI", REDIRECT_URI),
        cache_path=".spotify_cache", open_browser=False),
        retries=0, status_retries=0, requests_timeout=20)
    from .cache_layer import CachingClient
    fetch = build_getsongbpm_fetch(os.environ.get("GETSONGBPM_API_KEY", ""))
    # CachingClient: 979 Beğenilenler'i bir kez çekip diske cache'ler → tekrarlı işlemler
    # anında gelir + Spotify rate-limit'ini bir daha tetiklemez.
    client = CachingClient(SpotipyClient(sp))
    return OrganizerService(client, bpm_fetch=fetch, genre_provider=_genre_provider)


_GENRE_CACHE = "cache/genres.json"


def _genre_provider(names):
    """Tür kovası: cache/genres.json'dan SADECE OKUR (istek anında ağ YOK; prewarm_genres.py
    MusicBrainz'den doldurur). Önbellekte olmayan sanatçı → 'Diğer'."""
    from . import genre_source
    cache = genre_source.load_cache(_GENRE_CACHE)
    out = {}
    for n in names:
        if not n:
            continue
        raw = cache.get(n.lower())
        out[n] = genre_source.OTHER if raw is None else genre_source.itunes_to_bucket(raw)
    return out


def _ok(data):
    return jsonify({"success": True, "data": data, "error": None})


def _err(msg, code=400):
    return jsonify({"success": False, "data": None, "error": str(msg)}), code


def _run(fn):
    """Body'yi al, servisi kur, fn(svc, body) çalıştır, zarfla + hata yakala."""
    body = request.get_json(silent=True) or {}
    try:
        svc = _service()
    except Exception as e:  # noqa: BLE001 — gerçek modda auth eksikse temiz hata
        return _err(f"istemci kurulamadı (auth gerekli olabilir): {e}", 401)
    try:
        return _ok(fn(svc, body))
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        low = msg.lower()
        if "429" in msg or "rate" in low or "request limit" in low:
            return _err("Spotify geçici olarak istek limiti koydu (geliştirici-modu düşük kota). "
                        "Birkaç saat sonra tekrar dene — DEMO modu çalışmaya devam eder.", 429)
        return _err(e, 400)


# ---------- temel okuma ----------
@app.get("/api/me")
def me():
    if _demo():
        return jsonify({"display_name": "Demo Kullanıcı", "demo": True})
    try:
        name = _service().client.current_user().get("display_name", "—")
    except Exception:  # noqa: BLE001 — auth yoksa panel yine açılsın
        name = "—"
    return jsonify({"display_name": name, "demo": False})


@app.get("/api/playlists")
def playlists():
    return _run(lambda s, b: s.client.playlists())


@app.get("/api/playlist/<pid>")
def playlist(pid):
    def fn(s, b):
        tracks = s.client.playlist_tracks(pid)
        if not tracks:
            raise ValueError("playlist bulunamadı")
        return {"id": pid, "name": s._name_for(pid), "tracks": tracks}
    return _run(fn)


# ---------- türe göre ayır ----------
@app.post("/api/split-genre/preview")
def split_genre_preview():
    return _run(lambda s, b: s.preview_split_genre(b.get("source", "liked")))


@app.post("/api/split-genre/apply")
def split_genre_apply():
    return _run(lambda s, b: s.apply_split_genre(b.get("source", "liked")))


# ---------- geçişli sırala (DJ) ----------
@app.post("/api/order/preview")
def order_preview():
    return _run(lambda s, b: s.preview_order(b.get("source", "liked")))


@app.post("/api/order/apply")
def order_apply():
    return _run(lambda s, b: s.apply_order(b.get("source", "liked")))


# ---------- tekrar temizle ----------
@app.post("/api/dedupe/preview")
def dedupe_preview():
    return _run(lambda s, b: s.preview_dedupe(b.get("source", "liked")))


@app.post("/api/dedupe/apply")
def dedupe_apply():
    return _run(lambda s, b: s.apply_dedupe(b.get("source", "liked")))


# ---------- çok-anahtarlı sırala ----------
@app.post("/api/sort/preview")
def sort_preview():
    return _run(lambda s, b: s.preview_sort(b.get("source", "liked"), b.get("keys", [])))


@app.post("/api/sort/apply")
def sort_apply():
    return _run(lambda s, b: s.apply_sort(b.get("source", "liked"), b.get("keys", [])))


# ---------- birleştir ----------
@app.post("/api/merge/preview")
def merge_preview():
    return _run(lambda s, b: s.preview_merge(b.get("sources", [])))


@app.post("/api/merge/apply")
def merge_apply():
    return _run(lambda s, b: s.apply_merge(b.get("sources", []), b.get("name", "")))


# ---------- böl ----------
@app.post("/api/split/preview")
def split_preview():
    return _run(lambda s, b: s.preview_split(b.get("source", "liked"), b.get("by", "decade"), b.get("size")))


@app.post("/api/split/apply")
def split_apply():
    return _run(lambda s, b: s.apply_split(b.get("source", "liked"), b.get("by", "decade"), b.get("size")))


# ---------- içgörüler / keşif / yedekler ----------
@app.get("/api/insights/<source>")
def insights(source):
    return _run(lambda s, b: s.insights(source))


@app.get("/api/top")
def top():
    return _run(lambda s, b: s.top())


@app.post("/api/search")
def search():
    return _run(lambda s, b: s.search(b.get("query", "")))


@app.post("/api/discover/apply")
def discover_apply():
    return _run(lambda s, b: s.create_from(b.get("name", ""), b.get("kind", "top"), b.get("query", "")))


# ---------- Akıllı Mix ----------
@app.post("/api/smartmix/preview")
def smartmix_preview():
    return _run(lambda s, b: s.preview_smartmix(b.get("source", "liked")))


@app.post("/api/smartmix/apply")
def smartmix_apply():
    return _run(lambda s, b: s.apply_smartmix(b.get("source", "liked")))


@app.get("/api/backups")
def backups():
    return _run(lambda s, b: s.list_backups())


@app.post("/api/restore")
def restore():
    return _run(lambda s, b: s.restore(b.get("file", "")))


@app.post("/api/refresh")
def refresh():
    """Önbelleği temizle — kullanıcı Spotify'da şarkı ekleyince taze veri çekilsin."""
    def fn(s, b):
        if hasattr(s.client, "clear"):
            s.client.clear()
        return {"refreshed": True}
    return _run(fn)


def main():
    port = int(os.environ.get("PORT", "5055"))
    # threaded=True: 979-parça gibi yavaş istekler işlenirken panel diğer isteklere
    # (örn /api/me) yanıt vermeye devam etsin (tek-thread blok → "backend düştü" hissini önler).
    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
