from config import settings
from utils.logger import log
from spotipy.oauth2 import SpotifyClientCredentials

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=settings.spotify_client_id, client_secret=settings.spotify_client_secret))

