from config import settings
from utils.logger import log
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict

class SpotifyClient:
    def __init__(self):
        client_id = settings.spotify_client_id
        client_secret = settings.spotify_client_secret
        if not client_id or not client_secret:
            raise ValueError("Missing Spotify API credentials in .env")

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            )
        )

    def get_pl_items(self, pl_id: str) -> List[Dict]:
        results = []
        offset = 0

        while True:
            response = self.sp.playlist_items(
                playlist_id=pl_id,
                offset=offset,
                fields="items.track.id, items.track.name, items.track.artists.name"
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
                "artist_name": ", ".join(a["name"] for a in item["track"]["artists"])
            }
            for item in results
        ]