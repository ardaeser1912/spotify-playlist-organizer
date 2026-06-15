"""DJ geçişli sıralama — Camelot harmonic mixing + BPM rampası.

Saf Python, ağ YOK. Track dict şekli için fixtures.py'ye bakın
(her track'te `bpm` int|None ve `camelot` str|None, örn "8B").
"""


def camelot_neighbors(code):
    """Verilen Camelot kodunun uyumlu komşu kodları kümesi (kendisi dahil).

    Kurallar (harmonic mixing):
      - aynı kod
      - aynı sayı, diğer harf (relative major/minor): 8B <-> 8A
      - sayı +1 aynı harf (wrap 12 -> 1): 8B -> 9B
      - sayı -1 aynı harf (wrap 1 -> 12): 8B -> 7B

    Geçersiz/None kod -> boş set.
    """
    if not isinstance(code, str):
        return set()
    code = code.strip().upper()
    if len(code) < 2:
        return set()
    num_part, letter = code[:-1], code[-1]
    if letter not in ("A", "B"):
        return set()
    if not num_part.isdigit():
        return set()
    num = int(num_part)
    if num < 1 or num > 12:
        return set()

    up = num + 1 if num < 12 else 1
    down = num - 1 if num > 1 else 12
    other = "A" if letter == "B" else "B"

    return {
        f"{num}{letter}",
        f"{num}{other}",
        f"{up}{letter}",
        f"{down}{letter}",
    }


def _bpm_gap(a, b):
    """İki track arasındaki |bpm farkı|. bpm None ise 0 say."""
    abpm = a.get("bpm")
    bbpm = b.get("bpm")
    if abpm is None or bbpm is None:
        return 0
    return abs(abpm - bbpm)


def harmonic_order(tracks):
    """Greedy harmonic sıralama (Camelot + BPM rampası).

    - camelot'u OLMAYAN (None) track'ler çıkışta en sona giriş-sırasıyla eklenir.
    - camelot'lu track'lerden giriş sırasındaki ilki seed alınır; sonra her
      adımda mevcut track'in komşu kümesinde camelot'u bulunanlar arasından en
      küçük |bpm farkı| olan seçilir. Uyumlu komşu yoksa kalanlardan en küçük
      |bpm farkı| olan seçilir (geçiş kopsa da rampayı koru).

    Dönen liste girişin permütasyonudur; track'ler mutasyona uğratılmaz.
    """
    with_camelot = [t for t in tracks if t.get("camelot") is not None]
    without_camelot = [t for t in tracks if t.get("camelot") is None]

    if not with_camelot:
        return list(without_camelot)

    remaining = list(with_camelot)
    ordered = [remaining.pop(0)]

    while remaining:
        current = ordered[-1]
        neighbors = camelot_neighbors(current.get("camelot"))

        compatible = [t for t in remaining if t.get("camelot") in neighbors]
        pool = compatible if compatible else remaining

        nxt = min(pool, key=lambda t: _bpm_gap(current, t))
        remaining.remove(nxt)
        ordered.append(nxt)

    return ordered + without_camelot
