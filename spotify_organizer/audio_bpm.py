"""BPM + Camelot — "bütün şarkıları bilen" hibrit kaynak.

GetSongBPM mainstream odaklı (niş elektronik/rap'i bilmez). Bunun yerine:
  1. Deezer'da şarkıyı bul (büyük katalog, ücretsiz/anahtarsız) → BPM alanı + 30sn önizleme.
  2. Deezer BPM doluysa ONU kullan (hızlı, doğru).
  3. Boşsa (0) → 30sn önizleme sesini YEREL analiz et (librosa) → gerçek BPM (octave düzeltmeli).
  4. Camelot: önizleme sesinden anahtar tahmini (Krumhansl-Schmuckler) → Camelot.

Veritabanı kapsamına bağımlı DEĞİL — Deezer'da olan (≈tüm ticari müzik) her şarkının BPM'i çıkar.
librosa + ffmpeg gerekir (yerel analiz). Ağ: Deezer + önizleme indirme.
"""
from __future__ import annotations

import json
import tempfile
import urllib.parse
import urllib.request

_DEEZER_SEARCH = "https://api.deezer.com/search"
_DEEZER_TRACK = "https://api.deezer.com/track"
_UA = {"User-Agent": "SpotifyPlaylistOrganizer/1.0"}

# Pitch-class (0=C..11=B) + mod → Camelot. Major=B çemberi, minor=A çemberi.
_MAJOR_CAMELOT = {0: "8B", 1: "3B", 2: "10B", 3: "5B", 4: "12B", 5: "7B",
                  6: "2B", 7: "9B", 8: "4B", 9: "11B", 10: "6B", 11: "1B"}
_MINOR_CAMELOT = {0: "5A", 1: "12A", 2: "7A", 3: "2A", 4: "9A", 5: "4A",
                  6: "11A", 7: "6A", 8: "1A", 9: "8A", 10: "3A", 11: "10A"}


def _get_json(url: str):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def deezer_lookup(artist: str, title: str):
    """Deezer'da ara → (bpm|None, preview_url|None). Bulunamazsa (None, None)."""
    q = urllib.parse.quote(f"{artist} {title}")
    try:
        res = _get_json(f"{_DEEZER_SEARCH}?q={q}&limit=1").get("data") or []
        if not res:
            return None, None
        first = res[0]
        preview = first.get("preview") or None
        bpm = None
        try:
            track = _get_json(f"{_DEEZER_TRACK}/{first['id']}")
            b = track.get("bpm")
            if b and float(b) > 0:
                bpm = round(float(b))
        except Exception:
            pass
        return bpm, preview
    except Exception:
        return None, None


def _octave_fix(tempo: float) -> int:
    """Yarı/çift tempo hatasını düzelt → 90–185 aralığına çek (modern müzik)."""
    while tempo < 90:
        tempo *= 2
    while tempo > 185:
        tempo /= 2
    return round(tempo)


def analyze_preview(preview_url: str):
    """30sn önizleme sesini indirip yerel BPM + Camelot tahmini → (bpm|None, camelot|None)."""
    try:
        import warnings
        warnings.filterwarnings("ignore")
        import librosa
        import numpy as np
    except Exception:
        return None, None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as tf:
            urllib.request.urlretrieve(preview_url, tf.name)
            y, sr = librosa.load(tf.name, sr=None, mono=True)
        tempo = float(np.atleast_1d(librosa.beat.beat_track(y=y, sr=sr)[0])[0])
        bpm = _octave_fix(tempo) if tempo > 0 else None
        camelot = _estimate_camelot(y, sr, librosa, np)
        return bpm, camelot
    except Exception:
        return None, None


# Krumhansl-Schmuckler anahtar profilleri
_MAJ = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
_MIN = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]


def _estimate_camelot(y, sr, librosa, np):
    """Chroma + Krumhansl-Schmuckler ile anahtar tahmini → Camelot."""
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
        maj, minp = np.array(_MAJ), np.array(_MIN)
        best_corr, best = -2.0, None
        for i in range(12):
            rolled = np.roll(chroma, -i)
            cmaj = float(np.corrcoef(rolled, maj)[0, 1])
            cmin = float(np.corrcoef(rolled, minp)[0, 1])
            if cmaj > best_corr:
                best_corr, best = cmaj, _MAJOR_CAMELOT[i]
            if cmin > best_corr:
                best_corr, best = cmin, _MINOR_CAMELOT[i]
        return best
    except Exception:
        return None


def get_bpm_camelot(artist: str, title: str):
    """{bpm, camelot} — Deezer BPM varsa o, yoksa ses analizi. Bulunamazsa None."""
    bpm, preview = deezer_lookup(artist, title)
    camelot = None
    if preview and (bpm is None or camelot is None):
        a_bpm, a_camelot = analyze_preview(preview)
        if bpm is None:
            bpm = a_bpm
        camelot = a_camelot  # anahtar yalnız ses analizinden gelir (Deezer key vermez)
    if bpm is None and camelot is None:
        return None
    return {"bpm": bpm, "camelot": camelot}
