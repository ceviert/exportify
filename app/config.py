import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class Settings:
    spotify_client_id: str = os.getenv("SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET")
    cache_path: str = os.getenv("CACHE_PATH")
    save_dir: str = os.getenv("DOWNLOAD_DIR")

settings = Settings()