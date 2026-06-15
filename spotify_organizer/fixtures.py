"""DEMO verisi — auth olmadan panelin uçtan uca çalışması için.

Şekil, gerçek client'ın döndüreceğiyle aynı tutuldu (loop client.py'yi buna göre yazar).
Her şarkıda demo amaçlı `bpm`+`camelot` (Geçişli Sırala) ve `year`+`popularity`
(İçgörüler) var ki özellikler GetSongBPM/Spotify olmadan da demo veride çalışabilsin.
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

# (id, başlık, sanatçı_id, bpm, camelot, süre_sn, yıl, popülerlik)
_TRACKS = [
    ("t01", "Kuzu Kuzu",          "a_tarkan",  104, "8B",  245, 2001, 62),
    ("t02", "Şımarık",            "a_tarkan",  120, "9B",  230, 1997, 75),
    ("t03", "Gülümse",            "a_sezen",    98, "7A",  268, 1991, 55),
    ("t04", "Hadi Bakalım",       "a_sezen",   112, "8A",  240, 1991, 50),
    ("t05", "Levitating",         "a_dua",     103, "6B",  203, 2020, 90),
    ("t06", "Don't Start Now",    "a_dua",     124, "11B", 183, 2019, 88),
    ("t07", "Blinding Lights",    "a_weeknd",  171, "1A",  200, 2019, 95),
    ("t08", "Save Your Tears",    "a_weeknd",  118, "3B",  215, 2020, 89),
    ("t09", "One More Time",      "a_daft",    123, "4A",  320, 2000, 80),
    ("t10", "Get Lucky",          "a_daft",    116, "10B", 248, 2013, 82),
    ("t11", "Wake Me Up",         "a_avicii",  124, "5A",  247, 2013, 86),
    ("t12", "Levels",             "a_avicii",  126, "2B",  200, 2011, 78),
    ("t13", "Holocaust",          "a_ceza",     92, "9A",  258, 2004, 58),
    ("t14", "Lose Yourself",      "a_eminem",   86, "12A", 326, 2002, 87),
    ("t15", "Thunderstruck",      "a_acdc",    134, "6A",  292, 1990, 80),
    ("t16", "Uprising",           "a_muse",    128, "7B",  304, 2009, 76),
    ("t17", "Adsız Parça",        "a_unknown", None, None, 210, 2015, 20),
]

# Albüm kapakları (DEMO için iTunes'tan gerçek görseller; gerçek modda Spotify sağlar).
_b = "https://is1-ssl.mzstatic.com/image/thumb"
_ART = {
    "t01": f"{_b}/Music124/v4/35/8d/22/358d22cf-8b9c-1e7d-996d-85aad739a255/dj.nixigvoo.jpg/300x300bb.jpg",
    "t02": f"{_b}/Music113/v4/f1/95/04/f1950424-2ae5-55ff-580d-d52e8300ec1b/dj.iedkotfi.jpg/300x300bb.jpg",
    "t03": f"{_b}/Music211/v4/75/62/48/75624807-5b53-72a5-8926-cee76fa52091/25UMGIM92899.rgb.jpg/300x300bb.jpg",
    "t04": f"{_b}/Music211/v4/75/62/48/75624807-5b53-72a5-8926-cee76fa52091/25UMGIM92899.rgb.jpg/300x300bb.jpg",
    "t05": f"{_b}/Music116/v4/6c/11/d6/6c11d681-aa3a-d59e-4c2e-f77e181026ab/190295092665.jpg/300x300bb.jpg",
    "t06": f"{_b}/Music116/v4/41/ee/66/41ee66fa-f8dd-7e82-155a-3a1b360dc562/190295322175.jpg/300x300bb.jpg",
    "t07": f"{_b}/Music125/v4/a6/6e/bf/a66ebf79-5008-8948-b352-a790fc87446b/19UM1IM04638.rgb.jpg/300x300bb.jpg",
    "t08": f"{_b}/Music124/v4/83/3a/f7/833af71b-2e0c-3303-24f5-8f5c546c073b/20UMGIM21167.rgb.jpg/300x300bb.jpg",
    "t09": f"{_b}/Music221/v4/fd/4a/77/fd4a77db-0ebc-d043-41a2-f32fa1bb0fb4/dj.qrikkdwj.jpg/300x300bb.jpg",
    "t10": f"{_b}/Music115/v4/e8/43/5f/e8435ffa-b6b9-b171-40ab-4ff3959ab661/886443919266.jpg/300x300bb.jpg",
    "t11": f"{_b}/Music211/v4/18/5b/1e/185b1ef5-5d97-19d8-aebf-8e29e41874ef/13UAAIM59255.rgb.jpg/300x300bb.jpg",
    "t12": f"{_b}/Music211/v4/67/38/43/67384338-9ed7-fc68-5927-93f1fcf4705d/11UMGIM36900.rgb.jpg/300x300bb.jpg",
    "t13": f"{_b}/Music115/v4/f3/af/e2/f3afe2f1-c179-a0ce-347e-5431d7400305/cover.jpg/300x300bb.jpg",
    "t14": f"{_b}/Music125/v4/08/23/fc/0823fcd9-cb44-695b-32bf-b3bf51d9f800/00606949351229.rgb.jpg/300x300bb.jpg",
    "t15": f"{_b}/Features125/v4/bb/a2/f0/bba2f0d7-4d9e-c617-d49e-3ae02fd5d440/dj.xbkfgllk.jpg/300x300bb.jpg",
    "t16": f"{_b}/Music124/v4/e2/8d/41/e28d412b-da8b-6f0b-227a-faa9a453e612/825646092666.jpg/300x300bb.jpg",
}

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
        "year": year,
        "popularity": pop,
        "image": _ART.get(tid),
    }
    for (tid, title, aid, bpm, cam, dur, year, pop) in _TRACKS
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
