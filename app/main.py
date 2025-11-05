from utils.logger import log
from config import settings
from spotify.client import SpotifyClient

sp = SpotifyClient()

print(sp.get_pl_items("3cEYpjA9oz9GiPac4AsH4n"))