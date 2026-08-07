import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root (the directory containing app/, data/, downloads/).
# All paths default relative to this so the app works regardless of cwd.
BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    spotify_client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    spotify_client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    cache_path: str = os.getenv("CACHE_PATH", str(BASE_DIR / "data" / "songcache.json"))
    save_dir: str = os.getenv("DOWNLOAD_DIR", str(BASE_DIR / "downloads"))
    cookies_path: str = os.getenv("COOKIE_PATH", str(BASE_DIR / "data" / "cookies.txt"))
    spotipy_cache_path: str = os.getenv("SPOTIPY_CACHE", str(BASE_DIR / "data" / ".spotipy_cache"))


settings = Settings()
