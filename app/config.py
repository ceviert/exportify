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
    # Spotify access: "auto" tries the anonymous web-player token first and falls
    # back to developer credentials when the token endpoint is blocked.
    # "anonymous" and "credentials" force either path.
    spotify_auth_mode: str = os.getenv("SPOTIFY_AUTH", "auto")
    spotify_client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    spotify_client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    cache_path: str = os.getenv("CACHE_PATH", str(BASE_DIR / "data" / "songcache.json"))
    save_dir: str = os.getenv("DOWNLOAD_DIR", str(BASE_DIR / "downloads"))
    cookies_path: str = os.getenv("COOKIE_PATH", str(BASE_DIR / "data" / "cookies.txt"))
    spotify_token_cache_path: str = os.getenv("SPOTIFY_TOKEN_CACHE", str(BASE_DIR / "data" / ".spotify_token.json"))
    spotipy_cache_path: str = os.getenv("SPOTIPY_CACHE", str(BASE_DIR / "data" / ".spotipy_cache"))


settings = Settings()
