from typing import Dict, Optional


def track_to_dict(item) -> Optional[Dict]:
    """Map a Spotify playlist_items entry to the compact track dict used downstream.

    Returns None for entries that aren't a real track with an id (e.g. missing or
    unavailable tracks, local files, or podcast episodes), which the caller
    filters out. Fields that Spotify omits (e.g. artists on local files) are
    handled defensively so a single odd entry can't crash the whole run.
    """
    if not isinstance(item, dict):
        return None

    track = item.get("track")
    if not isinstance(track, dict) or not track.get("id"):
        return None

    artists = track.get("artists") or []
    artist_name = ", ".join(a["name"] for a in artists if isinstance(a, dict) and a.get("name"))

    album_name = ""
    cover_url = None
    album = track.get("album")
    if isinstance(album, dict):
        album_name = album.get("name", "")
        images = album.get("images") or []
        if images and isinstance(images[0], dict) and images[0].get("url"):
            cover_url = images[0]["url"]

    return {
        "id": track["id"],
        "name": track.get("name", ""),
        "artist_name": artist_name,
        "album_name": album_name,
        "cover_url": cover_url,
        "duration_ms": track.get("duration_ms", 0),
    }
