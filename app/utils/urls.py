def extract_playlist_id(playlist_str: str) -> str:
    """Extract a Spotify playlist ID from a full URL, or return the string as-is."""
    if "spotify.com/playlist/" in playlist_str:
        return playlist_str.split("spotify.com/playlist/")[1].split("?")[0]
    return playlist_str
