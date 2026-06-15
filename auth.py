"""Tek seferlik Spotify OAuth — gerçek hesabına bağlanmak için (Şef sabah ÇALIŞTIRIR).

Loop bunu ASLA çalıştırmaz (CERRAH modu). `.env` doldurulduktan sonra:

    python auth.py

Tarayıcı açılır, onaylarsın, token `.spotify_cache`'e yazılır. Sonra panel gerçek
modda (DEMO=1 olmadan) bu cache'i kullanır.
"""
import os

from dotenv import load_dotenv

from spotify_organizer.client import REDIRECT_URI, SCOPES


def main():
    load_dotenv()
    for var in ("SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET"):
        if not os.environ.get(var):
            raise SystemExit(f"Eksik: {var} — .env dosyasını doldur (bkz .env.example).")

    import spotipy
    from spotipy.oauth2 import SpotifyOAuth

    redirect = os.environ.get("SPOTIPY_REDIRECT_URI", REDIRECT_URI)
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=SCOPES, redirect_uri=redirect, cache_path=".spotify_cache", open_browser=True))
    me = sp.current_user()
    print(f"✅ Giriş başarılı: {me.get('display_name') or me['id']}")
    print("Token .spotify_cache'e yazıldı. Artık: python -m spotify_organizer.app (DEMO=1 OLMADAN)")


if __name__ == "__main__":
    main()
