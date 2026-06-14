"""Flask backend.

DEMO=1 iken fixture verisi döner (auth gerekmez). DEMO olmadan gerçek Spotify
client'ı kullanılır (loop client.py + endpoint'leri doldurur).

Frontend (Vite) dev'de /api'yi buraya proxy'ler → CORS gerekmez.
Çalıştır:  DEMO=1 python -m spotify_organizer.app   (varsayılan port 5055)
"""
import os

from flask import Flask, jsonify

from . import fixtures

app = Flask(__name__)
DEMO = os.environ.get("DEMO") == "1"


@app.get("/api/me")
def me():
    return jsonify({"display_name": "Demo Kullanıcı" if DEMO else "—", "demo": DEMO})


@app.get("/api/playlists")
def playlists():
    data = fixtures.playlists_summary() if DEMO else []
    return jsonify({"success": True, "data": data, "error": None})


@app.get("/api/playlist/<pid>")
def playlist(pid):
    pl = fixtures.get_playlist(pid) if DEMO else None
    if not pl:
        return jsonify({"success": False, "data": None, "error": "playlist bulunamadı"}), 404
    return jsonify({"success": True, "data": pl, "error": None})


def main():
    port = int(os.environ.get("PORT", "5055"))
    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
