"""Performans bekçisi — büyük listede (5000 track) organize/order ölçeklenmesi.

Eşikler CI titremesine dayanıklı olacak şekilde RAHAT tutuldu (gözlenenin
~3-4 katı). Amaç regresyon yakalamak: bir fonksiyon yanlışlıkla O(n²)/kopya
patlamasına dönerse bu testler kırmızıya döner.

Ölçülen (geliştirme makinesi, 5000 track):
    dedupe/sort/merge/split/insights  → her biri < ~3 ms  (eşik 0.5 s)
    harmonic_order                    → ~0.40 s (O(n²) greedy ama 5000'de
                                        eşiğin altında — ÖLÇEKLENİYOR)
"""
import random
import time

from spotify_organizer import organize, order

N = 5000
CAMELOTS = [f"{n}{l}" for n in range(1, 13) for l in ("A", "B")]


def _make_tracks(n):
    """n sentetik track. id benzersiz; title/artist çeşitli (dedupe için bazı
    tekrarlar); bpm/camelot/year çeşitli ve bazıları None.

    Not: popularity bilinçli olarak DOLU tutuldu — None varyasyonu diğer
    alanlarda var. (insights() bugün popularity=None'a karşı dayanıklı değil;
    bkz. perf raporu, görev kapsamı dışı.)
    """
    rnd = random.Random(42)
    out = []
    for i in range(n):
        cam = rnd.choice(CAMELOTS) if rnd.random() > 0.1 else None
        bpm = rnd.randint(70, 180) if rnd.random() > 0.1 else None
        year = rnd.choice([None, rnd.randint(1970, 2024)])
        out.append({
            "id": f"t{i}",
            "title": f"Song {i % 2000}",       # ~%60 satır tekrar eden başlık
            "artist": f"Artist {i % 300}",
            "artist_id": f"a{i % 300}",
            "uri": f"spotify:track:t{i}",
            "duration_ms": rnd.randint(120, 360) * 1000,
            "bpm": bpm,
            "camelot": cam,
            "year": year,
            "popularity": rnd.randint(0, 100),
        })
    return out


def _elapsed(fn):
    start = time.perf_counter()
    result = fn()
    return time.perf_counter() - start, result


# ---------- organize: her biri < 0.5 s ----------

def test_perf_dedupe():
    tracks = _make_tracks(N)
    dt, out = _elapsed(lambda: organize.dedupe(tracks))
    assert dt < 0.5, f"dedupe çok yavaş: {dt:.3f}s"
    # doğruluk: kept + removed == girdi; benzersiz (id, pair) sayısı korunur
    assert len(out["kept"]) + len(out["removed"]) == N
    seen = set()
    for t in tracks:
        seen.add((t["title"].lower(), t["artist"].lower()))
    assert len(out["kept"]) == len(seen)


def test_perf_sort_tracks():
    tracks = _make_tracks(N)
    keys = [("popularity", "desc"), ("year", "asc"), ("title", "asc")]
    dt, out = _elapsed(lambda: organize.sort_tracks(tracks, keys))
    assert dt < 0.5, f"sort_tracks çok yavaş: {dt:.3f}s"
    assert len(out) == N


def test_perf_merge_playlists():
    tracks = _make_tracks(N)
    dt, out = _elapsed(lambda: organize.merge_playlists([tracks, tracks[:1000]]))
    assert dt < 0.5, f"merge_playlists çok yavaş: {dt:.3f}s"
    # ikinci liste tamamen tekrar → kept == benzersiz başlık-sanatçı sayısı
    seen = {(t["title"].lower(), t["artist"].lower()) for t in tracks}
    assert len(out) == len(seen)


def test_perf_split_by_decade():
    tracks = _make_tracks(N)
    dt, out = _elapsed(lambda: organize.split_by_decade(tracks))
    assert dt < 0.5, f"split_by_decade çok yavaş: {dt:.3f}s"
    assert sum(len(v) for v in out.values()) == N


def test_perf_split_by_tempo():
    tracks = _make_tracks(N)
    dt, out = _elapsed(lambda: organize.split_by_tempo(tracks))
    assert dt < 0.5, f"split_by_tempo çok yavaş: {dt:.3f}s"
    assert sum(len(v) for v in out.values()) == N


def test_perf_insights():
    tracks = _make_tracks(N)
    dt, out = _elapsed(lambda: organize.insights(tracks))
    assert dt < 0.5, f"insights çok yavaş: {dt:.3f}s"
    assert out["total"] == N


# ---------- order: harmonic_order 5000 < 1.5 s (ölçekleniyor) ----------

def test_perf_harmonic_order():
    tracks = _make_tracks(N)
    dt, out = _elapsed(lambda: order.harmonic_order(tracks))
    # Greedy O(n²) ama 5000'de geliştirme makinesinde ~0.40s.
    # Rahat guard: 1.5s'i aşarsa regresyon var demektir.
    assert dt < 1.5, f"harmonic_order çok yavaş: {dt:.3f}s"
    assert len(out) == N
    # permütasyon korunur
    assert sorted(t["id"] for t in out) == sorted(t["id"] for t in tracks)
