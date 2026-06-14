"""DEMO verisi — auth olmadan panelin uçtan uca çalışması için.

Şekil, gerçek client'ın döndüreceğiyle aynı tutuldu (loop client.py'yi buna göre yazar).
Her şarkıda demo amaçlı `bpm` + `camelot` var ki 'Geçişli Sırala' özelliği
GetSongBPM olmadan da demo veride çalışabilsin.
"""

ARTISTS = {
    "a_tarkan":   {"id": "a_tarkan",   "name": "Tarkan",        "genres": ["turkish pop", "pop"]},
    "a_sezen":    {"id": "a_sezen",    "name": "Sezen Aksu",    "genres": ["turkish pop", "arabesk"]},
    "a_dua":      {"id": "a_dua",      "name": "Dua Lipa",      "genres": ["dance pop", "pop"]},
    "a_weeknd":   {"id": "a_weeknd",   "name": "The Weeknd",    "genres": ["pop", "r&b"]},
    "a_daft":     {"id": "a_daft",     "name": "Daft Punk",     "genres": ["french house", "electronic"]},
    "a_avicii":   {"id": "a_avicii",   "name": "Avicii",        "genres": ["edm", "electronic"]},
    "a_ceza":     {"id": "a_ceza",     "name": "Ceza",          "genres": ["turkish hip hop", "rap"]},
    "a_eminem":   {"id": "a_eminem",   "name": "Eminem",        "genres": ["hip hop", "rap"]},
    "a_acdc":     {"id": "a_acdc",     "name": "AC/DC",         "genres": ["hard rock", "rock"]},
    "a_muse":     {"id": "a_muse",     "name": "Muse",          "genres": ["alternative rock", "rock"]},
    "a_unknown":  {"id": "a_unknown",  "name": "Bilinmeyen",    "genres": []},
}

# (id, başlık, sanatçı_id, bpm, camelot, süre_sn)
_TRACKS = [
    ("t01", "Kuzu Kuzu",          "a_tarkan",  104, "8B", 245),
    ("t02", "Şımarık",            "a_tarkan",  120, "9B", 230),
    ("t03", "Gülümse",            "a_sezen",    98, "7A", 268),
    ("t04", "Hadi Bakalım",       "a_sezen",   112, "8A", 240),
    ("t05", "Levitating",         "a_dua",     103, "6B", 203),
    ("t06", "Don't Start Now",    "a_dua",     124, "11B", 183),
    ("t07", "Blinding Lights",    "a_weeknd",  171, "1A", 200),
    ("t08", "Save Your Tears",    "a_weeknd",  118, "3B", 215),
    ("t09", "One More Time",      "a_daft",    123, "4A", 320),
    ("t10", "Get Lucky",          "a_daft",    116, "10B", 248),
    ("t11", "Wake Me Up",         "a_avicii",  124, "5A", 247),
    ("t12", "Levels",             "a_avicii",  126, "2B", 200),
    ("t13", "Holocaust",          "a_ceza",     92, "9A", 258),
    ("t14", "Lose Yourself",      "a_eminem",   86, "12A", 326),
    ("t15", "Thunderstruck",      "a_acdc",    134, "6A", 292),
    ("t16", "Uprising",           "a_muse",    128, "7B", 304),
    ("t17", "Adsız Parça",        "a_unknown", None, None, 210),
]

TRACKS = {
    tid: {
        "id": tid,
        "title": title,
        "artist": ARTISTS[aid]["name"],
        "artist_id": aid,
        "uri": f"spotify:track:{tid}",
        "duration_ms": dur * 1000,
        "bpm": bpm,
        "camelot": cam,
    }
    for (tid, title, aid, bpm, cam, dur) in _TRACKS
}

PLAYLISTS = [
    {"id": "p_liked",  "name": "Beğenilenler",  "track_ids": list(TRACKS.keys())},
    {"id": "p_yaz",    "name": "Yaz Karışık",   "track_ids": ["t05", "t06", "t09", "t10", "t11", "t12", "t01"]},
    {"id": "p_spor",   "name": "Spor",          "track_ids": ["t07", "t12", "t15", "t16", "t14"]},
    {"id": "p_chill",  "name": "Chill",         "track_ids": ["t03", "t08", "t13"]},
]


def playlists_summary():
    return [{"id": p["id"], "name": p["name"], "track_count": len(p["track_ids"])} for p in PLAYLISTS]


def get_playlist(pid):
    pl = next((p for p in PLAYLISTS if p["id"] == pid), None)
    if not pl:
        return None
    return {
        "id": pl["id"],
        "name": pl["name"],
        "tracks": [TRACKS[t] for t in pl["track_ids"] if t in TRACKS],
    }
