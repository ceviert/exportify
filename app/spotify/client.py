from config import settings
from utils.logger import log
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict

from spotipy.cache_handler import CacheFileHandler

class SpotifyClient:
    def __init__(self):
        client_id = settings.spotify_client_id
        client_secret = settings.spotify_client_secret
        if not client_id or not client_secret:
            raise ValueError("Missing Spotify API credentials in .env")

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id, 
                client_secret=client_secret,
                cache_handler=CacheFileHandler(cache_path="data/.spotipy_cache")
            )
        )

    def get_pl_info(self, pl_id: str) -> dict:
        response = self.sp.playlist(playlist_id=pl_id, fields="name, tracks.total")
        return {
            "playlist_name": response["name"],
            "track_count": response["tracks"]["total"]
        }

    def get_pl_items(self, pl_id: str) -> List[Dict]:
        results = []
        offset = 0

        while True:
            response = self.sp.playlist_items(
                playlist_id=pl_id,
                offset=offset,
                fields="next,items.track.id,items.track.name,items.track.artists.name,items.track.album.name,items.track.album.images,items.track.duration_ms"
            )
            items = response.get("items", [])
            results.extend(items)
            if not response.get("next"):
                break
            offset += len(items)

        return [
            {
                "id": item["track"]["id"],
                "name": item["track"]["name"],
                "artist_name": ", ".join(a["name"] for a in item["track"]["artists"]),
                "album_name": item["track"]["album"]["name"] if item.get("track") and item["track"].get("album") else "",
                "cover_url": item["track"]["album"]["images"][0]["url"] if item.get("track") and item["track"].get("album") and item["track"]["album"].get("images") else None,
                "duration_ms": item["track"].get("duration_ms", 0)
            }
            for item in results if item and item.get("track") and item["track"].get("id")
        ]
    
    def get_pl_data(self, pl_id: str) -> dict:
        pl_info = self.get_pl_info(pl_id)
        pl_items = self.get_pl_items(pl_id)
        return {
            **pl_info,
            "tracks": pl_items
        }